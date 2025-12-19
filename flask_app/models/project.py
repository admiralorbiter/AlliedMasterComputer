# flask_app/models/project.py

from .base import db, BaseModel

# Association table for many-to-many relationship between Project and ResearchBrief
project_research_briefs = db.Table(
    'project_research_briefs',
    db.Column('project_id', db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), primary_key=True),
    db.Column('research_brief_id', db.Integer, db.ForeignKey('research_briefs.id', ondelete='CASCADE'), primary_key=True),
    db.Index('idx_project_research_briefs_project', 'project_id'),
    db.Index('idx_project_research_briefs_brief', 'research_brief_id')
)

class Project(BaseModel):
    """Model for storing user projects"""
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Relationship to User
    user = db.relationship('User', backref=db.backref('projects', lazy='dynamic', cascade='all, delete-orphan'))
    
    # Relationship to Goals
    goals = db.relationship('Goal', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    
    # Relationship to Todos
    todos = db.relationship('Todo', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    
    # Many-to-many relationship with ResearchBrief
    research_briefs = db.relationship(
        'ResearchBrief',
        secondary=project_research_briefs,
        back_populates='projects',
        lazy='dynamic'
    )
    
    def __repr__(self):
        return f'<Project {self.id}: {self.name}>'
    
    @staticmethod
    def find_by_user(user_id):
        """Find all projects for a user, ordered by created_at descending"""
        try:
            return Project.query.filter_by(user_id=user_id)\
                .order_by(Project.created_at.desc())\
                .all()
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Database error finding projects for user {user_id}: {str(e)}")
            return []
    
    @staticmethod
    def find_by_id_and_user(project_id, user_id):
        """Find a project by ID ensuring it belongs to the user"""
        try:
            return Project.query.filter_by(id=project_id, user_id=user_id).first()
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Database error finding project {project_id} for user {user_id}: {str(e)}")
            return None

