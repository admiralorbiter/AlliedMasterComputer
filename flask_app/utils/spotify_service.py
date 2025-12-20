# flask_app/utils/spotify_service.py

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import current_app, url_for
from flask_app.models import SpotifyAuth
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)

class SpotifyService:
    """Service class for Spotify API operations"""
    
    def __init__(self):
        """Initialize Spotify service with config"""
        self.client_id = current_app.config.get('SPOTIPY_CLIENT_ID')
        self.client_secret = current_app.config.get('SPOTIPY_CLIENT_SECRET')
        self.redirect_uri = current_app.config.get('SPOTIPY_REDIRECT_URI')
        self.scope = current_app.config.get('SPOTIPY_SCOPE', 'playlist-modify-public,playlist-modify-private,playlist-read-private,playlist-read-collaborative')
        self._client = None
        self._oauth_manager = None
    
    def get_oauth_manager(self):
        """Get or create Spotify OAuth manager"""
        if not self._oauth_manager:
            if not all([self.client_id, self.client_secret, self.redirect_uri]):
                raise ValueError("Spotify OAuth configuration missing. Please set SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, and SPOTIPY_REDIRECT_URI")
            
            # Use cache_path=None to prevent file-based caching, we'll handle tokens in DB
            self._oauth_manager = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=self.scope,
                cache_path=None  # We manage tokens in database
            )
        return self._oauth_manager
    
    def get_client(self, token_info=None):
        """Get Spotify client with valid token"""
        try:
            # If token_info not provided, get from database
            if not token_info:
                auth = SpotifyAuth.get_active_auth()
                if not auth:
                    raise ValueError("No valid Spotify authentication found. Please connect to Spotify first.")
                
                if auth.is_expired():
                    # Try to refresh token
                    token_info = self.refresh_token(auth)
                    if not token_info:
                        raise ValueError("Spotify token expired and refresh failed. Please reconnect to Spotify.")
                else:
                    token_info = {
                        'access_token': auth.access_token,
                        'refresh_token': auth.refresh_token,
                        'expires_at': int(auth.token_expires_at.timestamp()) if auth.token_expires_at else None,
                        'scope': auth.scope
                    }
            
            # Create client with token
            self._client = spotipy.Spotify(auth=token_info['access_token'])
            return self._client
            
        except Exception as e:
            logger.error(f"Error getting Spotify client: {str(e)}")
            raise
    
    def refresh_token(self, auth):
        """Refresh Spotify access token"""
        try:
            if not auth.refresh_token:
                logger.error("No refresh token available")
                return None
            
            oauth_manager = self.get_oauth_manager()
            token_info = oauth_manager.refresh_access_token(auth.refresh_token)
            
            # Update auth in database
            expires_in = token_info.get('expires_in', 3600)
            success, error = auth.update_token(
                access_token=token_info['access_token'],
                refresh_token=token_info.get('refresh_token') or auth.refresh_token,
                expires_in=expires_in
            )
            
            if not success:
                logger.error(f"Error updating token in database: {error}")
                return None
            
            return token_info
            
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return None
    
    def get_authorize_url(self):
        """Get Spotify authorization URL"""
        try:
            oauth_manager = self.get_oauth_manager()
            auth_url = oauth_manager.get_authorize_url()
            return auth_url
        except Exception as e:
            logger.error(f"Error getting authorize URL: {str(e)}")
            raise
    
    def get_access_token_from_code(self, code, user_id):
        """Exchange authorization code for access token"""
        try:
            oauth_manager = self.get_oauth_manager()
            token_info = oauth_manager.get_access_token(code)
            
            # Store token in database
            expires_in = token_info.get('expires_in', 3600)
            auth, error = SpotifyAuth.create_or_update(
                user_id=user_id,
                access_token=token_info['access_token'],
                refresh_token=token_info.get('refresh_token'),
                expires_in=expires_in,
                scope=token_info.get('scope')
            )
            
            if error:
                logger.error(f"Error storing token: {error}")
                return None, error
            
            return token_info, None
            
        except Exception as e:
            logger.error(f"Error getting access token: {str(e)}")
            return None, str(e)
    
    def create_playlist_on_spotify(self, name, description=None, public=False):
        """Create a playlist on Spotify"""
        try:
            client = self.get_client()
            user = client.current_user()
            user_id = user['id']
            
            playlist = client.user_playlist_create(
                user=user_id,
                name=name,
                public=public,
                description=description
            )
            
            logger.info(f"Created Spotify playlist: {playlist['id']}")
            return playlist, None
            
        except Exception as e:
            logger.error(f"Error creating playlist on Spotify: {str(e)}")
            return None, str(e)
    
    def add_tracks_to_playlist(self, playlist_id, track_uris):
        """Add tracks to a Spotify playlist"""
        try:
            if not track_uris:
                return True, None
            
            client = self.get_client()
            
            # Spotify API limits to 100 tracks per request
            batch_size = 100
            for i in range(0, len(track_uris), batch_size):
                batch = track_uris[i:i + batch_size]
                client.playlist_add_items(playlist_id=playlist_id, items=batch)
            
            logger.info(f"Added {len(track_uris)} tracks to Spotify playlist {playlist_id}")
            return True, None
            
        except Exception as e:
            logger.error(f"Error adding tracks to Spotify playlist: {str(e)}")
            return False, str(e)
    
    def get_user_playlists(self, limit=50, offset=0):
        """Get user's Spotify playlists"""
        try:
            client = self.get_client()
            playlists = client.current_user_playlists(limit=limit, offset=offset)
            return playlists, None
            
        except Exception as e:
            logger.error(f"Error getting user playlists: {str(e)}")
            return None, str(e)
    
    def get_playlist_tracks(self, playlist_id, limit=100, offset=0):
        """Get tracks from a Spotify playlist"""
        try:
            client = self.get_client()
            results = client.playlist_items(
                playlist_id=playlist_id,
                limit=limit,
                offset=offset
            )
            return results, None
            
        except Exception as e:
            logger.error(f"Error getting playlist tracks: {str(e)}")
            return None, str(e)
    
    def sync_local_to_spotify(self, local_playlist, public=False):
        """Export local playlist to Spotify"""
        try:
            # Get ordered songs from local playlist
            songs = local_playlist.get_songs_ordered()
            if not songs:
                return None, "Playlist is empty"
            
            # Extract track URIs (format: spotify:track:...)
            track_uris = [song.track_uri for song in songs]
            
            # Create playlist on Spotify
            spotify_playlist, error = self.create_playlist_on_spotify(
                name=local_playlist.name,
                description=local_playlist.description,
                public=public
            )
            
            if error:
                return None, error
            
            # Add tracks to Spotify playlist
            success, error = self.add_tracks_to_playlist(spotify_playlist['id'], track_uris)
            if not success:
                # If adding tracks failed, we should handle cleanup (optional)
                return None, error
            
            # Return playlist info
            return {
                'id': spotify_playlist['id'],
                'name': spotify_playlist['name'],
                'external_urls': spotify_playlist.get('external_urls', {}),
                'uri': spotify_playlist.get('uri')
            }, None
            
        except Exception as e:
            logger.error(f"Error syncing local playlist to Spotify: {str(e)}")
            return None, str(e)
    
    def sync_spotify_to_local(self, spotify_playlist_id, local_user_id, playlist_name=None):
        """Import Spotify playlist to local system"""
        try:
            from flask_app.models import Playlist, Song
            
            client = self.get_client()
            
            # Get playlist info
            playlist_info = client.playlist(playlist_id=spotify_playlist_id, fields='id,name,description')
            playlist_name = playlist_name or playlist_info.get('name', 'Imported Playlist')
            playlist_description = playlist_info.get('description')
            
            # Create local playlist
            local_playlist, error = Playlist.create_for_user(
                user_id=local_user_id,
                name=playlist_name,
                description=playlist_description
            )
            
            if error:
                return None, error
            
            # Get all tracks from Spotify playlist (handle pagination)
            tracks = []
            offset = 0
            limit = 100
            
            while True:
                results = client.playlist_items(
                    playlist_id=spotify_playlist_id,
                    limit=limit,
                    offset=offset
                )
                tracks.extend(results['items'])
                
                # Check if there are more items
                if len(results['items']) < limit or not results.get('next'):
                    break
                offset += limit
            
            # Extract track URIs and add to local playlist
            added_count = 0
            skipped_count = 0
            
            for item in tracks:
                track = item.get('track')
                if not track or track['type'] != 'track':
                    continue
                
                track_uri = track['uri']  # Format: spotify:track:...
                
                # Check if track exists in local library
                song = Song.find_by_track_uri(track_uri)
                if song:
                    success, error = local_playlist.add_song(track_uri)
                    if success:
                        added_count += 1
                    else:
                        skipped_count += 1
                else:
                    skipped_count += 1
            
            return {
                'playlist': local_playlist,
                'added_count': added_count,
                'skipped_count': skipped_count
            }, None
            
        except Exception as e:
            logger.error(f"Error syncing Spotify playlist to local: {str(e)}")
            return None, str(e)

