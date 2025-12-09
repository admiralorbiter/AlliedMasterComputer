# flask_app/forms/todo.py

from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

class TodoForm(FlaskForm):
    """Form for creating a new todo"""
    description = StringField(
        'Description',
        validators=[
            DataRequired(message="Description is required."),
            Length(max=2000, message="Description must be less than 2000 characters.")
        ],
        render_kw={
            "placeholder": "Enter todo description"
        }
    )
    
    due_date = DateField(
        'Due Date',
        validators=[Optional()],
        render_kw={
            "placeholder": "mm/dd/yyyy"
        }
    )
    
    submit = SubmitField('Add Todo')

