# flask_app/models/spotify_auth.py

from .base import db, BaseModel
from sqlalchemy import Index
from datetime import datetime, timezone, timedelta

class SpotifyAuth(BaseModel):
    """Model for storing Spotify OAuth tokens"""
    __tablename__ = 'spotify_auth'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    access_token = db.Column(db.Text, nullable=False)
    refresh_token = db.Column(db.Text, nullable=True)
    token_expires_at = db.Column(db.DateTime, nullable=True)
    scope = db.Column(db.Text, nullable=True)
    
    # Relationship to User
    user = db.relationship('User', backref=db.backref('spotify_auth', lazy='dynamic', cascade='all, delete-orphan'))
    
    # Indexes
    __table_args__ = (
        Index('idx_spotify_auth_user_id', 'user_id'),
    )
    
    def __repr__(self):
        return f'<SpotifyAuth {self.id}: user_id={self.user_id}>'
    
    def to_dict(self):
        """Convert to dictionary (exclude sensitive tokens)"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'token_expires_at': self.token_expires_at.isoformat() if self.token_expires_at else None,
            'scope': self.scope,
            'is_valid': self.is_valid(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def is_valid(self):
        """Check if token is valid (not expired)"""
        if not self.token_expires_at:
            return False
        # Ensure both datetimes are timezone-aware for comparison
        now = datetime.now(timezone.utc)
        expires_at = self.token_expires_at
        if expires_at.tzinfo is None:
            # If token_expires_at is naive, assume it's UTC
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return now < expires_at
    
    def is_expired(self):
        """Check if token is expired"""
        return not self.is_valid()
    
    def get_expires_at(self):
        """Get token expiration time, ensuring it's timezone-aware"""
        if not self.token_expires_at:
            return None
        if self.token_expires_at.tzinfo is None:
            return self.token_expires_at.replace(tzinfo=timezone.utc)
        return self.token_expires_at
    
    @staticmethod
    def get_active_auth():
        """Get the most recent active Spotify auth token (shared account approach)"""
        try:
            auth = SpotifyAuth.query.order_by(SpotifyAuth.created_at.desc()).first()
            if auth and auth.is_valid():
                return auth
            return None
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Error getting active Spotify auth: {str(e)}")
            return None
    
    @staticmethod
    def get_by_user_id(user_id):
        """Get Spotify auth for a specific user"""
        try:
            return SpotifyAuth.query.filter_by(user_id=user_id).order_by(SpotifyAuth.created_at.desc()).first()
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Error getting Spotify auth for user {user_id}: {str(e)}")
            return None
    
    @staticmethod
    def create_or_update(user_id, access_token, refresh_token=None, expires_in=None, scope=None):
        """Create or update Spotify auth token"""
        try:
            # For shared account, we'll just create a new entry each time
            # Optionally, we could update the most recent one
            auth = SpotifyAuth(
                user_id=user_id,
                access_token=access_token,
                refresh_token=refresh_token,
                scope=scope
            )
            
            if expires_in:
                auth.token_expires_at = datetime.now(timezone.utc).replace(microsecond=0) + \
                    timedelta(seconds=expires_in - 60)  # Subtract 60 seconds as buffer
            
            db.session.add(auth)
            db.session.commit()
            return auth, None
        except Exception as e:
            db.session.rollback()
            from flask import current_app
            current_app.logger.error(f"Error creating/updating Spotify auth: {str(e)}")
            return None, str(e)
    
    def update_token(self, access_token, refresh_token=None, expires_in=None):
        """Update the token information"""
        try:
            self.access_token = access_token
            if refresh_token:
                self.refresh_token = refresh_token
            
            if expires_in:
                self.token_expires_at = datetime.now(timezone.utc).replace(microsecond=0) + \
                    timedelta(seconds=expires_in - 60)  # Subtract 60 seconds as buffer
            
            self.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            return True, None
        except Exception as e:
            db.session.rollback()
            from flask import current_app
            current_app.logger.error(f"Error updating Spotify auth token: {str(e)}")
            return False, str(e)

