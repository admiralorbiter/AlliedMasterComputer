# flask_app/models/todo.py

from .base import db, BaseModel

class SubTask(BaseModel):
    """Model for storing subtasks within a todo"""
    __tablename__ = 'subtasks'
    
    id = db.Column(db.Integer, primary_key=True)
    todo_id = db.Column(db.Integer, db.ForeignKey('todos.id', ondelete='CASCADE'), nullable=False, index=True)
    description = db.Column(db.String(500), nullable=False)
    completed = db.Column(db.Boolean, default=False, nullable=False, index=True)
    order = db.Column(db.Integer, default=0, nullable=False)
    
    # Relationship to Todo
    todo = db.relationship('Todo', backref=db.backref('subtasks', lazy='dynamic', cascade='all, delete-orphan', order_by='SubTask.order'))
    
    def __repr__(self):
        return f'<SubTask {self.id}: {self.description[:50]}>'
    
    @staticmethod
    def find_by_todo(todo_id):
        """Find all subtasks for a todo, ordered by order then created_at"""
        try:
            return SubTask.query.filter_by(todo_id=todo_id)\
                .order_by(SubTask.order.asc(), SubTask.created_at.asc())\
                .all()
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Database error finding subtasks for todo {todo_id}: {str(e)}")
            return []

class Todo(BaseModel):
    """Model for storing user todos"""
    __tablename__ = 'todos'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    due_date = db.Column(db.Date, nullable=True)
    completed = db.Column(db.Boolean, default=False, nullable=False, index=True)
    goal_id = db.Column(db.Integer, db.ForeignKey('goals.id', ondelete='SET NULL'), nullable=True, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True, index=True)
    
    # Relationship to User
    user = db.relationship('User', backref=db.backref('todos', lazy='dynamic', cascade='all, delete-orphan'))
    
    def __repr__(self):
        return f'<Todo {self.id}: {self.description[:50]}>'
    
    @staticmethod
    def find_by_user(user_id):
        """Find all todos for a user, ordered by created_at descending"""
        try:
            return Todo.query.filter_by(user_id=user_id)\
                .order_by(Todo.created_at.desc())\
                .all()
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Database error finding todos for user {user_id}: {str(e)}")
            return []
    
    @staticmethod
    def find_by_id_and_user(todo_id, user_id):
        """Find a todo by ID ensuring it belongs to the user"""
        try:
            return Todo.query.filter_by(id=todo_id, user_id=user_id).first()
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Database error finding todo {todo_id} for user {user_id}: {str(e)}")
            return None
    
    @staticmethod
    def find_by_project(project_id, user_id):
        """Find all todos for a project, ordered by created_at descending"""
        try:
            return Todo.query.filter_by(project_id=project_id, user_id=user_id)\
                .order_by(Todo.created_at.desc())\
                .all()
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Database error finding todos for project {project_id}: {str(e)}")
            return []

class Event(BaseModel):
    """Model for storing user upcoming events"""
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    description = db.Column(db.String(500), nullable=False)
    event_date = db.Column(db.Date, nullable=False, index=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Processing fields
    processed = db.Column(db.Boolean, default=False, nullable=False, index=True)
    processed_at = db.Column(db.DateTime, nullable=True)
    outcome = db.Column(db.String(50), nullable=True)  # 'did_not_happen', 'happened', 'happened_with_notes'
    outcome_reason = db.Column(db.Text, nullable=True)  # For "didn't happen" option
    outcome_notes = db.Column(db.Text, nullable=True)  # For "happened with notes" option
    
    # Relationship to User
    user = db.relationship('User', backref=db.backref('events', lazy='dynamic', cascade='all, delete-orphan'))
    
    def __repr__(self):
        return f'<Event {self.id}: {self.description[:50]}>'
    
    @staticmethod
    def find_by_user(user_id):
        """Find all events for a user, ordered by event_date ascending (upcoming first)"""
        try:
            return Event.query.filter_by(user_id=user_id)\
                .order_by(Event.event_date.asc(), Event.created_at.asc())\
                .all()
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Database error finding events for user {user_id}: {str(e)}")
            return []
    
    @staticmethod
    def find_by_id_and_user(event_id, user_id):
        """Find an event by ID ensuring it belongs to the user"""
        try:
            return Event.query.filter_by(id=event_id, user_id=user_id).first()
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Database error finding event {event_id} for user {user_id}: {str(e)}")
            return None
    
    @staticmethod
    def find_upcoming_by_user(user_id):
        """Find all upcoming (future date) unprocessed events for a user"""
        try:
            from datetime import date
            return Event.query.filter_by(user_id=user_id, processed=False)\
                .filter(Event.event_date >= date.today())\
                .order_by(Event.event_date.asc(), Event.created_at.asc())\
                .all()
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Database error finding upcoming events for user {user_id}: {str(e)}")
            return []
    
    @staticmethod
    def find_past_unprocessed_by_user(user_id):
        """Find all past unprocessed events for a user"""
        try:
            from datetime import date
            return Event.query.filter_by(user_id=user_id, processed=False)\
                .filter(Event.event_date < date.today())\
                .order_by(Event.event_date.desc(), Event.created_at.desc())\
                .all()
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Database error finding past unprocessed events for user {user_id}: {str(e)}")
            return []
    
    @staticmethod
    def find_processed_by_user(user_id, limit=20):
        """Find recently processed events for a user"""
        try:
            return Event.query.filter_by(user_id=user_id, processed=True)\
                .order_by(Event.processed_at.desc())\
                .limit(limit)\
                .all()
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Database error finding processed events for user {user_id}: {str(e)}")
            return []

