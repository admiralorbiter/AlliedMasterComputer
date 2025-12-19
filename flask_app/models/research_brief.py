# flask_app/models/research_brief.py

from .base import db, BaseModel

# Association table for many-to-many relationship between ResearchBrief and Tag
research_brief_tags = db.Table(
    'research_brief_tags',
    db.Column('research_brief_id', db.Integer, db.ForeignKey('research_briefs.id', ondelete='CASCADE'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
    db.Index('idx_research_brief_tags_brief', 'research_brief_id'),
    db.Index('idx_research_brief_tags_tag', 'tag_id')
)

class ResearchBrief(BaseModel):
    """Model for storing research briefs generated from PDFs or text"""
    __tablename__ = 'research_briefs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(500), nullable=False)
    citation = db.Column(db.String(1000), nullable=False)
    summary = db.Column(db.Text, nullable=False)  # Bullet points stored as text
    source_text = db.Column(db.Text, nullable=False)  # Extracted text from PDF or user input
    url = db.Column(db.String(500), nullable=True)  # URL to the source article or document
    pdf_filename = db.Column(db.String(255), nullable=True)  # Original filename if PDF uploaded
    pdf_data = db.Column(db.LargeBinary, nullable=True)  # PDF file stored as binary
    content_hash = db.Column(db.String(64), nullable=True, index=True)  # MD5 hash of PDF content for duplicate detection
    source_type = db.Column(db.String(20), nullable=False)  # 'pdf', 'text', or 'manual'
    model_name = db.Column(db.String(50), nullable=True)  # OpenAI model used to generate the brief or source name for manual entries
    
    # Relationship to User
    user = db.relationship('User', backref=db.backref('research_briefs', lazy='dynamic', cascade='all, delete-orphan'))
    
    # Many-to-many relationship with Tag
    tags = db.relationship(
        'Tag',
        secondary=research_brief_tags,
        back_populates='research_briefs',
        lazy='dynamic'
    )
    
    # Many-to-many relationship with Project (imported from project.py)
    projects = db.relationship(
        'Project',
        secondary='project_research_briefs',
        back_populates='research_briefs',
        lazy='dynamic'
    )
    
    def __repr__(self):
        return f'<ResearchBrief {self.id}: {self.title[:50]}>'
    
    @staticmethod
    def find_by_user(user_id, page=1, per_page=20):
        """Find all briefs for a user with pagination"""
        try:
            return ResearchBrief.query.filter_by(user_id=user_id)\
                .order_by(ResearchBrief.created_at.desc())\
                .paginate(page=page, per_page=per_page, error_out=False)
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Database error finding briefs for user {user_id}: {str(e)}")
            return None
    
    @staticmethod
    def find_by_id_and_user(brief_id, user_id):
        """Find a brief by ID ensuring it belongs to the user"""
        try:
            return ResearchBrief.query.filter_by(id=brief_id, user_id=user_id).first()
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Database error finding brief {brief_id} for user {user_id}: {str(e)}")
            return None
    
    @staticmethod
    def find_duplicate_by_hash(content_hash):
        """Find existing research briefs with the same content hash (global check)"""
        try:
            if not content_hash:
                return None
            return ResearchBrief.query.filter_by(content_hash=content_hash).first()
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Database error finding duplicate by hash: {str(e)}")
            return None
    
    @staticmethod
    def find_duplicate_by_filename(filename, user_id=None):
        """Find existing research briefs with the same filename (global check, optionally filtered by user)"""
        try:
            if not filename:
                return None
            query = ResearchBrief.query.filter_by(pdf_filename=filename)
            if user_id:
                query = query.filter_by(user_id=user_id)
            return query.first()
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Database error finding duplicate by filename: {str(e)}")
            return None
    
    @staticmethod
    def check_duplicate(pdf_filename, pdf_data):
        """
        Check for duplicate PDFs by both filename and content hash.
        
        Args:
            pdf_filename: The filename of the PDF
            pdf_data: The binary PDF data
            
        Returns:
            Tuple of (is_duplicate: bool, duplicate_brief: ResearchBrief or None, reason: str or None)
        """
        try:
            from flask_app.utils.openai_service import calculate_pdf_hash
            
            # Check by filename first (global check)
            duplicate_by_filename = ResearchBrief.find_duplicate_by_filename(pdf_filename)
            if duplicate_by_filename:
                return True, duplicate_by_filename, f"Duplicate filename: '{pdf_filename}'"
            
            # Check by content hash (global check)
            content_hash = calculate_pdf_hash(pdf_data)
            duplicate_by_hash = ResearchBrief.find_duplicate_by_hash(content_hash)
            if duplicate_by_hash:
                return True, duplicate_by_hash, f"Duplicate content (hash match)"
            
            return False, None, None
            
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Error checking for duplicates: {str(e)}")
            # On error, don't block upload - return not duplicate
            return False, None, None
    
    def add_tag(self, tag_name):
        """Add a tag to this brief (creates tag if it doesn't exist)"""
        try:
            from .tag import Tag
            tag, error = Tag.find_or_create_by_name(tag_name)
            if error or not tag:
                return False, error or "Failed to create or find tag"
            
            if tag not in self.tags:
                self.tags.append(tag)
                db.session.commit()
            
            return True, None
        except Exception as e:
            db.session.rollback()
            from flask import current_app
            current_app.logger.error(f"Error adding tag '{tag_name}' to brief {self.id}: {str(e)}")
            return False, str(e)
    
    def remove_tag(self, tag_name):
        """Remove a tag from this brief"""
        try:
            from .tag import Tag
            normalized_name = tag_name.strip().lower()
            tag = Tag.query.filter_by(name=normalized_name).first()
            
            if tag and tag in self.tags:
                self.tags.remove(tag)
                db.session.commit()
            
            return True, None
        except Exception as e:
            db.session.rollback()
            from flask import current_app
            current_app.logger.error(f"Error removing tag '{tag_name}' from brief {self.id}: {str(e)}")
            return False, str(e)
    
    def get_tag_names(self):
        """Get list of tag names for this brief"""
        try:
            return [tag.name for tag in self.tags.order_by('name').all()]
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Error getting tag names for brief {self.id}: {str(e)}")
            return []
    
    @staticmethod
    def find_by_user_and_tag(user_id, tag_id=None, page=1, per_page=20):
        """Find all briefs for a user, optionally filtered by tag, with pagination"""
        try:
            query = ResearchBrief.query.filter_by(user_id=user_id)
            
            if tag_id:
                query = query.join(ResearchBrief.tags).filter_by(id=tag_id)
            
            return query.order_by(ResearchBrief.created_at.desc())\
                .paginate(page=page, per_page=per_page, error_out=False)
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Database error finding briefs for user {user_id} with tag {tag_id}: {str(e)}")
            return None