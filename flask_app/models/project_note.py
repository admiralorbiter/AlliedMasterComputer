# flask_app/models/project_note.py

from .base import db, BaseModel

class ProjectNote(BaseModel):
    """Model for storing project notes"""
    __tablename__ = 'project_notes'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    
    # Relationships
    project = db.relationship('Project', backref=db.backref('notes', lazy='dynamic', cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('project_notes', lazy='dynamic'))
    
    def __repr__(self):
        return f'<ProjectNote {self.id}: {self.content[:50]}>'
    
    @staticmethod
    def find_by_project(project_id):
        """Find all notes for a project, ordered by created_at descending"""
        try:
            return ProjectNote.query.filter_by(project_id=project_id)\
                .order_by(ProjectNote.created_at.desc())\
                .all()
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Database error finding notes for project {project_id}: {str(e)}")
            return []
    
    @staticmethod
    def find_by_id_and_user(note_id, user_id):
        """Find a note by ID ensuring it belongs to the user"""
        try:
            return ProjectNote.query.filter_by(id=note_id, user_id=user_id).first()
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Database error finding note {note_id} for user {user_id}: {str(e)}")
            return None

