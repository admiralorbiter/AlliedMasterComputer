# flask_app/models/project_link.py

from .base import db, BaseModel

class ProjectLink(BaseModel):
    """Model for storing project links"""
    __tablename__ = 'project_links'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    
    # Relationships
    project = db.relationship('Project', backref=db.backref('links', lazy='dynamic', cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('project_links', lazy='dynamic'))
    
    def __repr__(self):
        return f'<ProjectLink {self.id}: {self.title}>'
    
    @staticmethod
    def find_by_project(project_id):
        """Find all links for a project, ordered by created_at descending"""
        try:
            return ProjectLink.query.filter_by(project_id=project_id)\
                .order_by(ProjectLink.created_at.desc())\
                .all()
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Database error finding links for project {project_id}: {str(e)}")
            return []
    
    @staticmethod
    def find_by_id_and_user(link_id, user_id):
        """Find a link by ID ensuring it belongs to the user"""
        try:
            return ProjectLink.query.filter_by(id=link_id, user_id=user_id).first()
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Database error finding link {link_id} for user {user_id}: {str(e)}")
            return None

