# flask_app/models/music_import_job.py

from .base import db, BaseModel
import uuid

class MusicImportJob(BaseModel):
    """Model for tracking CSV import jobs with progress"""
    __tablename__ = 'music_import_jobs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    status = db.Column(db.String(20), nullable=False, default='queued')  # queued, running, completed, failed
    
    # Progress tracking
    total_rows = db.Column(db.Integer, nullable=False, default=0)
    processed_rows = db.Column(db.Integer, nullable=False, default=0)
    inserted_count = db.Column(db.Integer, nullable=False, default=0)
    duplicate_count = db.Column(db.Integer, nullable=False, default=0)
    error_count = db.Column(db.Integer, nullable=False, default=0)
    
    # File metadata
    original_filename = db.Column(db.String(255), nullable=False)
    stored_path = db.Column(db.String(500), nullable=False)
    
    # Timestamps
    started_at = db.Column(db.DateTime, nullable=True)
    finished_at = db.Column(db.DateTime, nullable=True)
    
    # Error information
    error_message = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<MusicImportJob {self.id}: {self.status}>'
    
    def to_dict(self):
        """Convert job to dictionary for JSON serialization"""
        progress_percent = 0
        if self.total_rows > 0:
            progress_percent = int((self.processed_rows / self.total_rows) * 100)
        
        return {
            'id': self.id,
            'status': self.status,
            'total_rows': self.total_rows,
            'processed_rows': self.processed_rows,
            'inserted_count': self.inserted_count,
            'duplicate_count': self.duplicate_count,
            'error_count': self.error_count,
            'progress_percent': progress_percent,
            'original_filename': self.original_filename,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'finished_at': self.finished_at.isoformat() if self.finished_at else None,
            'error_message': self.error_message,
        }
    
    @staticmethod
    def find_by_id(job_id):
        """Find a job by ID"""
        try:
            return MusicImportJob.query.filter_by(id=job_id).first()
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Database error finding import job {job_id}: {str(e)}")
            return None

