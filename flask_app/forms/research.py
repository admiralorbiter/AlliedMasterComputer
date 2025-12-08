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
        'PDF File(s)',
        validators=[
            Optional(),
            FileAllowed(['pdf'], message='Only PDF files are allowed.')
        ],
        render_kw={"accept": ".pdf", "multiple": True}
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
        """Validate PDF file(s) if source type is PDF
        
        Note: For multiple file uploads, actual validation is done in the route
        using request.files.getlist(). This validator checks basic requirements.
        """
        if self.source_type.data == 'pdf':
            # Basic check - detailed validation happens in route for multiple files
            # Flask-WTF FileField doesn't handle multiple files natively
            if not field.data:
                raise ValidationError('Please upload at least one PDF file.')
            
            # Validate single file if provided (for backward compatibility)
            if hasattr(field.data, 'read'):
                field.data.seek(0, 2)  # Seek to end
                size = field.data.tell()
                field.data.seek(0)  # Reset to beginning
                
                max_size = 25 * 1024 * 1024  # 25 MB per file
                if size > max_size:
                    filename = getattr(field.data, 'filename', 'File')
                    raise ValidationError(f'File "{filename}" exceeds 25MB limit. Current size: {size / (1024*1024):.2f} MB')
    
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
    
    tags = StringField(
        'Tags',
        validators=[
            Optional(),
            Length(max=500, message="Tags input must be less than 500 characters.")
        ],
        render_kw={
            "placeholder": "Enter tags separated by commas (e.g., ai, research, machine-learning)"
        }
    )
    
    submit = SubmitField('Update Brief')
