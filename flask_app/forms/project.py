# flask_app/forms/project.py

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

class ProjectForm(FlaskForm):
    """Form for creating/editing a project"""
    name = StringField(
        'Name',
        validators=[
            DataRequired(message="Name is required."),
            Length(max=200, message="Name must be less than 200 characters.")
        ],
        render_kw={
            "placeholder": "Enter project name"
        }
    )
    
    description = TextAreaField(
        'Description',
        validators=[
            Optional(),
            Length(max=2000, message="Description must be less than 2000 characters.")
        ],
        render_kw={
            "placeholder": "Enter project description (optional)",
            "rows": 3
        }
    )
    
    submit = SubmitField('Add Project')

