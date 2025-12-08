# flask_app/models/tag.py

from .base import db, BaseModel

class Tag(BaseModel):
    """Model for storing tags (global, shared across users)"""
    __tablename__ = 'tags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    
    # Many-to-many relationship with ResearchBrief
    research_briefs = db.relationship(
        'ResearchBrief',
        secondary='research_brief_tags',
        back_populates='tags',
        lazy='dynamic'
    )
    
    def __repr__(self):
        return f'<Tag {self.id}: {self.name}>'
    
    @staticmethod
    def find_or_create_by_name(tag_name):
        """Find a tag by name or create it if it doesn't exist (lazy creation)"""
        try:
            # Normalize tag name: lowercase and strip whitespace
            normalized_name = tag_name.strip().lower()
            
            if not normalized_name:
                return None, "Tag name cannot be empty"
            
            # Try to find existing tag
            tag = Tag.query.filter_by(name=normalized_name).first()
            
            if tag:
                return tag, None
            
            # Create new tag
            tag, error = Tag.safe_create(name=normalized_name)
            
            if error:
                from flask import current_app
                current_app.logger.error(f"Error creating tag '{normalized_name}': {error}")
                return None, error
            
            return tag, None
            
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Error finding or creating tag '{tag_name}': {str(e)}")
            return None, str(e)
    
    @staticmethod
    def get_all_tags_with_counts():
        """Get all tags with their usage counts"""
        try:
            from sqlalchemy import func
            from .research_brief import ResearchBrief
            
            # Query tags with counts of associated briefs
            tags_with_counts = db.session.query(
                Tag,
                func.count(ResearchBrief.id).label('count')
            ).join(
                Tag.research_briefs
            ).group_by(Tag.id).order_by(Tag.name).all()
            
            return [(tag, count) for tag, count in tags_with_counts], None
            
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Error getting tags with counts: {str(e)}")
            return [], str(e)
    
    @staticmethod
    def get_all_tags():
        """Get all tags ordered by name"""
        try:
            return Tag.query.order_by(Tag.name).all()
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Error getting all tags: {str(e)}")
            return []