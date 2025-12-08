# flask_app/forms/research.py

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SubmitField, RadioField
from wtforms.validators import DataRequired, Length, ValidationError, Optional

class ResearchBriefForm(FlaskForm):
    """Form for creating a new research brief"""
    source_type = RadioField(
        'Input Type',
        choices=[('pdf', 'Upload PDF'), ('text', 'Enter Text')],
        validators=[DataRequired(message="Please select an input type.")],
        default='text'
    )
    
    pdf_file = FileField(
        'PDF File',
        validators=[
            Optional(),
            FileAllowed(['pdf'], message='Only PDF files are allowed.')
        ],
        render_kw={"accept": ".pdf"}
    )
    
    source_text = TextAreaField(
        'Source Text',
        validators=[
            Optional(),
            Length(min=50, message="Text must be at least 50 characters long.")
        ],
        render_kw={
            "placeholder": "Paste or type your source text here (minimum 50 characters)",
            "rows": 10
        }
    )
    
    submit = SubmitField('Generate Brief')
    
    def validate_pdf_file(self, field):
        """Validate PDF file if source type is PDF"""
        if self.source_type.data == 'pdf':
            if not field.data:
                raise ValidationError('Please upload a PDF file.')
            
            # Check file size (25MB limit)
            if hasattr(field.data, 'read'):
                field.data.seek(0, 2)  # Seek to end
                size = field.data.tell()
                field.data.seek(0)  # Reset to beginning
                
                max_size = 25 * 1024 * 1024  # 25 MB
                if size > max_size:
                    raise ValidationError(f'File size exceeds 25MB limit. Current size: {size / (1024*1024):.2f} MB')
    
    def validate_source_text(self, field):
        """Validate source text if source type is text"""
        if self.source_type.data == 'text':
            if not field.data or len(field.data.strip()) < 50:
                raise ValidationError('Source text must be at least 50 characters long.')


class EditBriefForm(FlaskForm):
    """Form for editing an existing research brief"""
    title = StringField(
        'Title',
        validators=[
            DataRequired(message="Title is required."),
            Length(max=500, message="Title must be less than 500 characters.")
        ],
        render_kw={"placeholder": "Enter brief title"}
    )
    
    citation = StringField(
        'Citation',
        validators=[
            DataRequired(message="Citation is required."),
            Length(max=1000, message="Citation must be less than 1000 characters.")
        ],
        render_kw={"placeholder": "Enter citation"}
    )
    
    summary = TextAreaField(
        'Summary',
        validators=[
            DataRequired(message="Summary is required.")
        ],
        render_kw={
            "placeholder": "Enter summary with bullet points",
            "rows": 15
        }
    )
    
    submit = SubmitField('Update Brief')
