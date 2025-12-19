# flask_app/forms/todo.py

from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SubmitField, TextAreaField, SelectField
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
    
    goal_id = SelectField(
        'Goal',
        choices=[],  # Will be populated dynamically
        validators=[Optional()],
        coerce=int
    )
    
    submit = SubmitField('Add Todo')

class EventForm(FlaskForm):
    """Form for creating/editing an event"""
    description = StringField(
        'Description',
        validators=[
            DataRequired(message="Description is required."),
            Length(max=500, message="Description must be less than 500 characters.")
        ],
        render_kw={
            "placeholder": "Event description"
        }
    )
    
    event_date = DateField(
        'Date',
        validators=[DataRequired(message="Date is required.")],
        render_kw={
            "placeholder": "mm/dd/yyyy"
        }
    )
    
    notes = TextAreaField(
        'Notes',
        validators=[
            Optional(),
            Length(max=2000, message="Notes must be less than 2000 characters.")
        ],
        render_kw={
            "placeholder": "Additional notes (optional)",
            "rows": 2
        }
    )

