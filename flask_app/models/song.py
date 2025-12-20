# flask_app/models/song.py

from .base import db, BaseModel
from sqlalchemy import Index

class Song(BaseModel):
    """Model for storing imported music tracks from CSV files"""
    __tablename__ = 'songs'
    
    # Primary key is track_uri (Spotify track URI)
    track_uri = db.Column(db.String(255), primary_key=True, nullable=False)
    
    # Basic track information
    track_name = db.Column(db.String(500), nullable=True)
    album_name = db.Column(db.String(500), nullable=True)
    artist_names = db.Column(db.String(500), nullable=True)
    release_date = db.Column(db.String(50), nullable=True)  # Keep as string since format may vary
    duration_ms = db.Column(db.Integer, nullable=True)
    popularity = db.Column(db.Integer, nullable=True)
    explicit = db.Column(db.Boolean, nullable=True, default=False)
    
    # Import metadata
    added_by = db.Column(db.String(100), nullable=True)
    added_at = db.Column(db.String(100), nullable=True)  # Keep as string since format may vary
    
    # Genre and label
    genres = db.Column(db.Text, nullable=True)  # Comma-separated genres
    record_label = db.Column(db.String(500), nullable=True)
    
    # Audio features (Spotify audio analysis)
    danceability = db.Column(db.Float, nullable=True)
    energy = db.Column(db.Float, nullable=True)
    key = db.Column(db.Integer, nullable=True)  # 0-11 representing pitch class
    loudness = db.Column(db.Float, nullable=True)  # Typically -60 to 0 dB
    mode = db.Column(db.Integer, nullable=True)  # 0 = minor, 1 = major
    speechiness = db.Column(db.Float, nullable=True)
    acousticness = db.Column(db.Float, nullable=True)
    instrumentalness = db.Column(db.Float, nullable=True)
    liveness = db.Column(db.Float, nullable=True)
    valence = db.Column(db.Float, nullable=True)  # Musical positiveness
    tempo = db.Column(db.Float, nullable=True)  # BPM
    time_signature = db.Column(db.Integer, nullable=True)  # Typically 3, 4, or 5
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_songs_track_name', 'track_name'),
        Index('idx_songs_artist_names', 'artist_names'),
        Index('idx_songs_popularity', 'popularity'),
        Index('idx_songs_explicit', 'explicit'),
    )
    
    def __repr__(self):
        return f'<Song {self.track_uri}: {self.track_name[:50] if self.track_name else "Unknown"}>'
    
    def to_dict(self):
        """Convert song to dictionary for JSON serialization"""
        return {
            'track_uri': self.track_uri,
            'track_name': self.track_name,
            'album_name': self.album_name,
            'artist_names': self.artist_names,
            'release_date': self.release_date,
            'duration_ms': self.duration_ms,
            'popularity': self.popularity,
            'explicit': self.explicit,
            'added_by': self.added_by,
            'added_at': self.added_at,
            'genres': self.genres,
            'record_label': self.record_label,
            'danceability': self.danceability,
            'energy': self.energy,
            'key': self.key,
            'loudness': self.loudness,
            'mode': self.mode,
            'speechiness': self.speechiness,
            'acousticness': self.acousticness,
            'instrumentalness': self.instrumentalness,
            'liveness': self.liveness,
            'valence': self.valence,
            'tempo': self.tempo,
            'time_signature': self.time_signature,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @staticmethod
    def find_by_track_uri(track_uri):
        """Find a song by track URI"""
        try:
            return Song.query.filter_by(track_uri=track_uri).first()
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Database error finding song by track_uri {track_uri}: {str(e)}")
            return None
    
    @staticmethod
    def search(query, explicit_filter=None, min_popularity=None, page=1, per_page=20):
        """Search songs with filters and pagination"""
        try:
            q = Song.query
            
            # Text search across track name, artist, album
            if query:
                search_term = f"%{query}%"
                q = q.filter(
                    db.or_(
                        Song.track_name.ilike(search_term),
                        Song.artist_names.ilike(search_term),
                        Song.album_name.ilike(search_term)
                    )
                )
            
            # Filter by explicit content
            if explicit_filter is not None:
                q = q.filter(Song.explicit == explicit_filter)
            
            # Filter by minimum popularity
            if min_popularity is not None:
                q = q.filter(Song.popularity >= min_popularity)
            
            # Order by popularity descending, then by track name
            q = q.order_by(Song.popularity.desc().nullslast(), Song.track_name.asc())
            
            return q.paginate(page=page, per_page=per_page, error_out=False)
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Database error searching songs: {str(e)}")
            return None

