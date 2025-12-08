# flask_app/models/research_brief.py

from .base import db, BaseModel

class ResearchBrief(BaseModel):
    """Model for storing research briefs generated from PDFs or text"""
    __tablename__ = 'research_briefs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(500), nullable=False)
    citation = db.Column(db.String(1000), nullable=False)
    summary = db.Column(db.Text, nullable=False)  # Bullet points stored as text
    source_text = db.Column(db.Text, nullable=False)  # Extracted text from PDF or user input
    pdf_filename = db.Column(db.String(255), nullable=True)  # Original filename if PDF uploaded
    pdf_data = db.Column(db.LargeBinary, nullable=True)  # PDF file stored as binary
    source_type = db.Column(db.String(10), nullable=False)  # 'pdf' or 'text'
    
    # Relationship to User
    user = db.relationship('User', backref=db.backref('research_briefs', lazy='dynamic', cascade='all, delete-orphan'))
    
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
