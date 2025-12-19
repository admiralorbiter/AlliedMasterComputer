# flask_app/forms/project.py

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, URLField
from wtforms.validators import DataRequired, Length, Optional, URL

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

class ProjectNoteForm(FlaskForm):
    """Form for creating/editing a project note"""
    content = TextAreaField(
        'Content',
        validators=[
            DataRequired(message="Note content is required."),
            Length(max=10000, message="Note must be less than 10000 characters.")
        ],
        render_kw={
            "placeholder": "Enter note content",
            "rows": 4
        }
    )
    
    submit = SubmitField('Save Note')

class ProjectLinkForm(FlaskForm):
    """Form for creating/editing a project link"""
    title = StringField(
        'Title',
        validators=[
            DataRequired(message="Link title is required."),
            Length(max=200, message="Title must be less than 200 characters.")
        ],
        render_kw={
            "placeholder": "Enter link title"
        }
    )
    
    url = URLField(
        'URL',
        validators=[
            DataRequired(message="URL is required."),
            URL(message="Please enter a valid URL."),
            Length(max=500, message="URL must be less than 500 characters.")
        ],
        render_kw={
            "placeholder": "https://example.com"
        }
    )
    
    submit = SubmitField('Save Link')

