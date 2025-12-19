# flask_app/models/goal.py

from .base import db, BaseModel

class Goal(BaseModel):
    """Model for storing user goals"""
    __tablename__ = 'goals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    goal_type = db.Column(db.String(20), nullable=False, index=True)  # 'professional', 'personal', 'project'
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True, index=True)
    completed = db.Column(db.Boolean, default=False, nullable=False, index=True)
    
    # Relationship to User
    user = db.relationship('User', backref=db.backref('goals', lazy='dynamic', cascade='all, delete-orphan'))
    
    # Relationship to Todos
    todos = db.relationship('Todo', backref='goal', lazy='dynamic')
    
    def __repr__(self):
        return f'<Goal {self.id}: {self.title}>'
    
    @staticmethod
    def find_by_user(user_id, goal_type=None):
        """Find all goals for a user, optionally filtered by type, ordered by created_at descending"""
        try:
            query = Goal.query.filter_by(user_id=user_id)
            if goal_type:
                query = query.filter_by(goal_type=goal_type)
            return query.order_by(Goal.created_at.desc()).all()
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Database error finding goals for user {user_id}: {str(e)}")
            return []
    
    @staticmethod
    def find_by_id_and_user(goal_id, user_id):
        """Find a goal by ID ensuring it belongs to the user"""
        try:
            return Goal.query.filter_by(id=goal_id, user_id=user_id).first()
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Database error finding goal {goal_id} for user {user_id}: {str(e)}")
            return None

