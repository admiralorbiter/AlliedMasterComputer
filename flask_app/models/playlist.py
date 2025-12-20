# flask_app/models/playlist.py

from .base import db, BaseModel
from sqlalchemy import Index

# Association table for many-to-many relationship between Playlist and Song
playlist_songs = db.Table(
    'playlist_songs',
    db.Column('playlist_id', db.Integer, db.ForeignKey('playlists.id', ondelete='CASCADE'), primary_key=True),
    db.Column('track_uri', db.String(255), db.ForeignKey('songs.track_uri', ondelete='CASCADE'), primary_key=True),
    db.Column('position', db.Integer, nullable=False, default=0),  # For ordering songs in playlist
    db.Index('idx_playlist_songs_playlist', 'playlist_id'),
    db.Index('idx_playlist_songs_track', 'track_uri'),
    db.Index('idx_playlist_songs_position', 'playlist_id', 'position')
)

class Playlist(BaseModel):
    """Model for storing user playlists"""
    __tablename__ = 'playlists'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Spotify integration fields
    spotify_playlist_id = db.Column(db.String(255), nullable=True)
    spotify_synced_at = db.Column(db.DateTime, nullable=True)
    
    # Relationship to User
    user = db.relationship('User', backref=db.backref('playlists', lazy='dynamic', cascade='all, delete-orphan'))
    
    # Many-to-many relationship with Song
    songs = db.relationship(
        'Song',
        secondary=playlist_songs,
        lazy='dynamic',
        order_by='playlist_songs.c.position'
    )
    
    def __repr__(self):
        return f'<Playlist {self.id}: {self.name}>'
    
    def to_dict(self):
        """Convert playlist to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'song_count': self.songs.count(),
            'spotify_playlist_id': self.spotify_playlist_id,
            'spotify_synced_at': self.spotify_synced_at.isoformat() if self.spotify_synced_at else None,
            'is_synced_to_spotify': self.is_synced_to_spotify(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def is_synced_to_spotify(self):
        """Check if playlist is synced to Spotify"""
        return self.spotify_playlist_id is not None and self.spotify_playlist_id != ''
    
    def get_total_duration_ms(self):
        """Calculate total duration of all songs in playlist in milliseconds"""
        try:
            from flask_app.models import Song
            total = db.session.query(db.func.sum(Song.duration_ms))\
                .join(playlist_songs)\
                .filter(playlist_songs.c.playlist_id == self.id)\
                .scalar()
            return total or 0
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Error calculating playlist duration: {str(e)}")
            return 0
    
    def get_total_duration_formatted(self):
        """Get formatted total duration (e.g., '2h 15m' or '45m')"""
        total_ms = self.get_total_duration_ms()
        if not total_ms:
            return "0m"
        
        total_seconds = total_ms // 1000
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
    
    @staticmethod
    def find_by_user(user_id):
        """Find all playlists for a user, ordered by created_at descending"""
        try:
            return Playlist.query.filter_by(user_id=user_id)\
                .order_by(Playlist.created_at.desc())\
                .all()
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Database error finding playlists for user {user_id}: {str(e)}")
            return []
    
    @staticmethod
    def find_by_id_and_user(playlist_id, user_id):
        """Find a playlist by ID ensuring it belongs to the user"""
        try:
            return Playlist.query.filter_by(id=playlist_id, user_id=user_id).first()
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Database error finding playlist {playlist_id} for user {user_id}: {str(e)}")
            return None
    
    @staticmethod
    def create_for_user(user_id, name, description=None):
        """Create a new playlist for a user"""
        try:
            playlist = Playlist(user_id=user_id, name=name, description=description)
            db.session.add(playlist)
            db.session.commit()
            return playlist, None
        except Exception as e:
            db.session.rollback()
            from flask import current_app
            current_app.logger.error(f"Database error creating playlist for user {user_id}: {str(e)}")
            return None, str(e)
    
    def add_song(self, track_uri, position=None):
        """Add a song to the playlist"""
        try:
            from flask_app.models import Song
            # Check if song exists
            song = Song.find_by_track_uri(track_uri)
            if not song:
                return False, "Song not found"
            
            # Check if song is already in playlist
            existing = db.session.query(playlist_songs)\
                .filter_by(playlist_id=self.id, track_uri=track_uri)\
                .first()
            if existing:
                return False, "Song already in playlist"
            
            # Get next position if not specified
            if position is None:
                max_position = db.session.query(db.func.max(playlist_songs.c.position))\
                    .filter_by(playlist_id=self.id)\
                    .scalar()
                position = (max_position or -1) + 1
            
            # Insert song
            db.session.execute(
                playlist_songs.insert().values(
                    playlist_id=self.id,
                    track_uri=track_uri,
                    position=position
                )
            )
            db.session.commit()
            return True, None
        except Exception as e:
            db.session.rollback()
            from flask import current_app
            current_app.logger.error(f"Error adding song to playlist: {str(e)}")
            return False, str(e)
    
    def remove_song(self, track_uri):
        """Remove a song from the playlist"""
        try:
            db.session.execute(
                playlist_songs.delete().where(
                    db.and_(
                        playlist_songs.c.playlist_id == self.id,
                        playlist_songs.c.track_uri == track_uri
                    )
                )
            )
            db.session.commit()
            return True, None
        except Exception as e:
            db.session.rollback()
            from flask import current_app
            current_app.logger.error(f"Error removing song from playlist: {str(e)}")
            return False, str(e)
    
    def get_songs_ordered(self):
        """Get all songs in the playlist in order"""
        try:
            from flask_app.models import Song
            return db.session.query(Song)\
                .join(playlist_songs)\
                .filter(playlist_songs.c.playlist_id == self.id)\
                .order_by(playlist_songs.c.position)\
                .all()
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Error getting ordered songs: {str(e)}")
            return []
    
    def reorder_songs(self, track_uris):
        """Reorder songs in playlist. track_uris should be a list in desired order"""
        try:
            # Update positions
            for position, track_uri in enumerate(track_uris):
                db.session.execute(
                    playlist_songs.update().where(
                        db.and_(
                            playlist_songs.c.playlist_id == self.id,
                            playlist_songs.c.track_uri == track_uri
                        )
                    ).values(position=position)
                )
            db.session.commit()
            return True, None
        except Exception as e:
            db.session.rollback()
            from flask import current_app
            current_app.logger.error(f"Error reordering songs: {str(e)}")
            return False, str(e)

