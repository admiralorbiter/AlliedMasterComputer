# flask_app/forms/goal.py

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

class GoalForm(FlaskForm):
    """Form for creating/editing a goal"""
    title = StringField(
        'Title',
        validators=[
            DataRequired(message="Title is required."),
            Length(max=200, message="Title must be less than 200 characters.")
        ],
        render_kw={
            "placeholder": "Enter goal title"
        }
    )
    
    description = TextAreaField(
        'Description',
        validators=[
            Optional(),
            Length(max=2000, message="Description must be less than 2000 characters.")
        ],
        render_kw={
            "placeholder": "Enter goal description (optional)",
            "rows": 3
        }
    )
    
    goal_type = SelectField(
        'Goal Type',
        choices=[
            ('professional', 'Professional'),
            ('personal', 'Personal'),
            ('project', 'Project')
        ],
        validators=[DataRequired(message="Goal type is required.")]
    )
    
    project_id = SelectField(
        'Project',
        choices=[],  # Will be populated dynamically
        validators=[Optional()],
        coerce=int
    )
    
    submit = SubmitField('Add Goal')

