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

