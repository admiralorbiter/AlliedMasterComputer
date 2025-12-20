# flask_app/routes/music.py

from flask import flash, redirect, render_template, url_for, request, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from flask_app.models import Song, MusicImportJob, Playlist, SpotifyAuth, db
from flask_app.utils.spotify_service import SpotifyService
import os
import threading
from datetime import datetime, timezone
from functools import wraps

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin privileges required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def register_music_routes(app):
    """Register music library routes"""
    
    @app.route('/music/library')
    @login_required
    def music_library():
        """Display music library page with paginated songs"""
        try:
            page = request.args.get('page', 1, type=int)
            query = request.args.get('q', '').strip()
            explicit_filter = request.args.get('explicit', type=str)
            min_popularity = request.args.get('min_popularity', type=int)
            sort_by = request.args.get('sort_by', type=str)
            sort_order = request.args.get('sort_order', 'asc', type=str)
            
            # Convert explicit filter string to bool
            explicit_bool = None
            if explicit_filter == 'true':
                explicit_bool = True
            elif explicit_filter == 'false':
                explicit_bool = False
            
            # Validate sort_order
            if sort_order not in ['asc', 'desc']:
                sort_order = 'asc'
            
            # Search songs with filters
            songs = Song.search(
                query=query if query else None,
                explicit_filter=explicit_bool,
                min_popularity=min_popularity,
                page=page,
                per_page=20,
                sort_by=sort_by,
                sort_order=sort_order
            )
            
            if songs is None:
                flash('An error occurred while loading the music library.', 'danger')
                songs = Song.query.paginate(page=page, per_page=20, error_out=False)
            
            current_app.logger.info(f"Music library accessed by {current_user.username}")
            return render_template('music/library.html', songs=songs, query=query, 
                                 explicit_filter=explicit_filter, min_popularity=min_popularity,
                                 sort_by=sort_by, sort_order=sort_order)
            
        except Exception as e:
            current_app.logger.error(f"Error in music library: {str(e)}")
            flash('An error occurred while loading the music library.', 'danger')
            songs = Song.query.paginate(page=1, per_page=20, error_out=False)
            return render_template('music/library.html', songs=songs, query='', 
                                 explicit_filter=None, min_popularity=None, sort_by=None, sort_order='asc')
    
    @app.route('/music/library/song')
    @login_required
    def music_song_details():
        """Get full song details as JSON for modal"""
        try:
            track_uri = request.args.get('track_uri')
            if not track_uri:
                return jsonify({'error': 'track_uri parameter required'}), 400
            
            song = Song.find_by_track_uri(track_uri)
            if not song:
                return jsonify({'error': 'Song not found'}), 404
            
            return jsonify(song.to_dict())
            
        except Exception as e:
            current_app.logger.error(f"Error getting song details: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/music/library/import', methods=['POST'])
    @login_required
    def music_import():
        """Start CSV import job"""
        try:
            if 'csv_file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['csv_file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            # Validate file extension
            if not file.filename.lower().endswith('.csv'):
                return jsonify({'error': 'File must be a CSV'}), 400
            
            # Create upload directory if it doesn't exist
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            music_upload_dir = os.path.join(upload_folder, 'music')
            os.makedirs(music_upload_dir, exist_ok=True)
            
            # Save file
            filename = secure_filename(file.filename)
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')
            stored_filename = f"{timestamp}_{filename}"
            file_path = os.path.join(music_upload_dir, stored_filename)
            file.save(file_path)
            
            # Create import job
            job = MusicImportJob(
                status='queued',
                original_filename=filename,
                stored_path=file_path,
                total_rows=0
            )
            db.session.add(job)
            db.session.commit()
            
            # Start background import thread
            import_thread = threading.Thread(
                target=import_csv_background,
                args=(job.id, file_path, current_app._get_current_object()),
                daemon=True
            )
            import_thread.start()
            
            current_app.logger.info(f"Import job {job.id} started for file {filename} by {current_user.username}")
            return jsonify({'job_id': job.id, 'status': 'queued'})
            
        except Exception as e:
            current_app.logger.error(f"Error starting import: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/music/library/import-status')
    @login_required
    def music_import_status():
        """Get import job status"""
        try:
            job_id = request.args.get('job_id')
            if not job_id:
                return jsonify({'error': 'job_id parameter required'}), 400
            
            job = MusicImportJob.find_by_id(job_id)
            if not job:
                return jsonify({'error': 'Import job not found'}), 404
            
            return jsonify(job.to_dict())
            
        except Exception as e:
            current_app.logger.error(f"Error getting import status: {str(e)}")
            return jsonify({'error': str(e)}), 500

    # ========== PLAYLIST ROUTES ==========
    
    @app.route('/music/playlists')
    @login_required
    def playlists_list():
        """List all user's playlists"""
        try:
            playlists = Playlist.find_by_user(current_user.id)
            current_app.logger.info(f"Playlists list accessed by {current_user.username}")
            return render_template('music/playlists.html', playlists=playlists)
        except Exception as e:
            current_app.logger.error(f"Error loading playlists: {str(e)}")
            flash('An error occurred while loading playlists.', 'danger')
            return render_template('music/playlists.html', playlists=[])
    
    @app.route('/music/playlists/<int:playlist_id>')
    @login_required
    def playlist_view(playlist_id):
        """View playlist details with songs"""
        try:
            playlist = Playlist.find_by_id_and_user(playlist_id, current_user.id)
            if not playlist:
                flash('Playlist not found.', 'danger')
                return redirect(url_for('playlists_list'))
            
            # Get songs in order
            songs = playlist.get_songs_ordered()
            current_app.logger.info(f"Playlist {playlist_id} viewed by {current_user.username}")
            return render_template('music/playlist_view.html', playlist=playlist, songs=songs)
        except Exception as e:
            current_app.logger.error(f"Error loading playlist: {str(e)}")
            flash('An error occurred while loading the playlist.', 'danger')
            return redirect(url_for('playlists_list'))
    
    @app.route('/music/playlists/create', methods=['POST'])
    @login_required
    def playlist_create():
        """Create new playlist"""
        try:
            data = request.get_json()
            name = (data.get('name') or '').strip()
            description = data.get('description')
            if description:
                description = description.strip() or None
            else:
                description = None
            
            if not name:
                return jsonify({'error': 'Playlist name is required'}), 400
            
            playlist, error = Playlist.create_for_user(current_user.id, name, description)
            if error:
                return jsonify({'error': error}), 500
            
            current_app.logger.info(f"Playlist {playlist.id} created by {current_user.username}")
            return jsonify(playlist.to_dict()), 201
        except Exception as e:
            current_app.logger.error(f"Error creating playlist: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/music/playlists/<int:playlist_id>/update', methods=['POST'])
    @login_required
    def playlist_update(playlist_id):
        """Update playlist name/description"""
        try:
            playlist = Playlist.find_by_id_and_user(playlist_id, current_user.id)
            if not playlist:
                return jsonify({'error': 'Playlist not found'}), 404
            
            data = request.get_json()
            name = (data.get('name') or '').strip()
            description = data.get('description')
            if description:
                description = description.strip() or None
            else:
                description = None
            
            if not name:
                return jsonify({'error': 'Playlist name is required'}), 400
            
            success, error = playlist.safe_update(name=name, description=description)
            if not success:
                return jsonify({'error': error}), 500
            
            current_app.logger.info(f"Playlist {playlist_id} updated by {current_user.username}")
            return jsonify(playlist.to_dict())
        except Exception as e:
            current_app.logger.error(f"Error updating playlist: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/music/playlists/<int:playlist_id>', methods=['DELETE'])
    @login_required
    def playlist_delete(playlist_id):
        """Delete playlist"""
        try:
            playlist = Playlist.find_by_id_and_user(playlist_id, current_user.id)
            if not playlist:
                return jsonify({'error': 'Playlist not found'}), 404
            
            success, error = playlist.safe_delete()
            if not success:
                return jsonify({'error': error}), 500
            
            current_app.logger.info(f"Playlist {playlist_id} deleted by {current_user.username}")
            return jsonify({'success': True})
        except Exception as e:
            current_app.logger.error(f"Error deleting playlist: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/music/playlists/<int:playlist_id>/add-songs', methods=['POST'])
    @login_required
    def playlist_add_songs(playlist_id):
        """Add songs to playlist (bulk)"""
        try:
            playlist = Playlist.find_by_id_and_user(playlist_id, current_user.id)
            if not playlist:
                return jsonify({'error': 'Playlist not found'}), 404
            
            data = request.get_json()
            track_uris = data.get('track_uris', [])
            
            if not track_uris or not isinstance(track_uris, list):
                return jsonify({'error': 'track_uris must be a non-empty list'}), 400
            
            added = []
            errors = []
            for track_uri in track_uris:
                success, error = playlist.add_song(track_uri)
                if success:
                    added.append(track_uri)
                else:
                    errors.append({'track_uri': track_uri, 'error': error})
            
            current_app.logger.info(f"Added {len(added)} songs to playlist {playlist_id} by {current_user.username}")
            return jsonify({
                'added': added,
                'errors': errors,
                'added_count': len(added),
                'error_count': len(errors)
            })
        except Exception as e:
            current_app.logger.error(f"Error adding songs to playlist: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/music/playlists/<int:playlist_id>/remove-song', methods=['DELETE'])
    @login_required
    def playlist_remove_song(playlist_id):
        """Remove song from playlist"""
        try:
            playlist = Playlist.find_by_id_and_user(playlist_id, current_user.id)
            if not playlist:
                return jsonify({'error': 'Playlist not found'}), 404
            
            track_uri = request.args.get('track_uri')
            if not track_uri:
                return jsonify({'error': 'track_uri parameter required'}), 400
            
            success, error = playlist.remove_song(track_uri)
            if not success:
                return jsonify({'error': error}), 500
            
            current_app.logger.info(f"Song {track_uri} removed from playlist {playlist_id} by {current_user.username}")
            return jsonify({'success': True})
        except Exception as e:
            current_app.logger.error(f"Error removing song from playlist: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/music/playlists/<int:playlist_id>/reorder', methods=['POST'])
    @login_required
    def playlist_reorder(playlist_id):
        """Reorder songs in playlist"""
        try:
            playlist = Playlist.find_by_id_and_user(playlist_id, current_user.id)
            if not playlist:
                return jsonify({'error': 'Playlist not found'}), 404
            
            data = request.get_json()
            track_uris = data.get('track_uris', [])
            
            if not track_uris or not isinstance(track_uris, list):
                return jsonify({'error': 'track_uris must be a non-empty list'}), 400
            
            success, error = playlist.reorder_songs(track_uris)
            if not success:
                return jsonify({'error': error}), 500
            
            current_app.logger.info(f"Playlist {playlist_id} reordered by {current_user.username}")
            return jsonify({'success': True})
        except Exception as e:
            current_app.logger.error(f"Error reordering playlist: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/music/playlists/user-playlists')
    @login_required
    def user_playlists_json():
        """Get user's playlists as JSON for dropdown"""
        try:
            playlists = Playlist.find_by_user(current_user.id)
            return jsonify([p.to_dict() for p in playlists])
        except Exception as e:
            current_app.logger.error(f"Error getting user playlists: {str(e)}")
            return jsonify({'error': str(e)}), 500

    # ========== SPOTIFY OAUTH ROUTES ==========
    
    @app.route('/music/spotify/authorize')
    @login_required
    @admin_required
    def spotify_authorize():
        """Initiate Spotify OAuth authorization (admin-only)"""
        try:
            spotify_service = SpotifyService()
            auth_url = spotify_service.get_authorize_url()
            current_app.logger.info(f"Spotify authorization initiated by {current_user.username}")
            return redirect(auth_url)
        except Exception as e:
            current_app.logger.error(f"Error initiating Spotify authorization: {str(e)}")
            flash(f'Error connecting to Spotify: {str(e)}', 'danger')
            return redirect(url_for('playlists_list'))
    
    @app.route('/music/spotify/callback')
    @login_required
    def spotify_callback():
        """Handle Spotify OAuth callback"""
        try:
            code = request.args.get('code')
            error = request.args.get('error')
            
            if error:
                current_app.logger.error(f"Spotify OAuth error: {error}")
                flash(f'Spotify authorization failed: {error}', 'danger')
                return redirect(url_for('playlists_list'))
            
            if not code:
                flash('No authorization code received from Spotify.', 'danger')
                return redirect(url_for('playlists_list'))
            
            spotify_service = SpotifyService()
            token_info, error = spotify_service.get_access_token_from_code(code, current_user.id)
            
            if error:
                current_app.logger.error(f"Error exchanging code for token: {error}")
                flash(f'Error completing Spotify authorization: {error}', 'danger')
                return redirect(url_for('playlists_list'))
            
            current_app.logger.info(f"Spotify authorization completed by {current_user.username}")
            flash('Successfully connected to Spotify!', 'success')
            return redirect(url_for('playlists_list'))
            
        except Exception as e:
            current_app.logger.error(f"Error in Spotify callback: {str(e)}")
            flash(f'Error completing Spotify authorization: {str(e)}', 'danger')
            return redirect(url_for('playlists_list'))
    
    @app.route('/music/spotify/status')
    @login_required
    def spotify_status():
        """Check Spotify authentication status"""
        try:
            auth = SpotifyAuth.get_active_auth()
            if auth:
                return jsonify({
                    'authenticated': True,
                    'user_id': auth.user_id,
                    'scope': auth.scope,
                    'expires_at': auth.token_expires_at.isoformat() if auth.token_expires_at else None,
                    'is_valid': auth.is_valid()
                })
            else:
                return jsonify({'authenticated': False})
        except Exception as e:
            current_app.logger.error(f"Error checking Spotify status: {str(e)}")
            return jsonify({'error': str(e), 'authenticated': False}), 500
    
    @app.route('/music/spotify/disconnect', methods=['POST'])
    @login_required
    @admin_required
    def spotify_disconnect():
        """Disconnect Spotify (remove tokens, admin-only)"""
        try:
            # Delete all Spotify auth records (for shared account)
            deleted_count = SpotifyAuth.query.delete()
            db.session.commit()
            
            current_app.logger.info(f"Spotify disconnected by {current_user.username}, removed {deleted_count} auth record(s)")
            return jsonify({'success': True, 'message': 'Disconnected from Spotify'})
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error disconnecting Spotify: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    # ========== SPOTIFY PLAYLIST SYNC ROUTES ==========
    
    @app.route('/music/playlists/<int:playlist_id>/export-to-spotify', methods=['POST'])
    @login_required
    def playlist_export_to_spotify(playlist_id):
        """Export local playlist to Spotify"""
        try:
            playlist = Playlist.find_by_id_and_user(playlist_id, current_user.id)
            if not playlist:
                return jsonify({'error': 'Playlist not found'}), 404
            
            # Check if already synced (optional: allow re-sync)
            data = request.get_json() or {}
            public = data.get('public', False)
            force_resync = data.get('force', False)
            
            if playlist.is_synced_to_spotify() and not force_resync:
                return jsonify({
                    'error': 'Playlist already synced to Spotify. Use force=true to re-sync.',
                    'spotify_playlist_id': playlist.spotify_playlist_id
                }), 400
            
            spotify_service = SpotifyService()
            spotify_playlist, error = spotify_service.sync_local_to_spotify(playlist, public=public)
            
            if error:
                return jsonify({'error': error}), 500
            
            # Update playlist with Spotify info
            success, error = playlist.safe_update(
                spotify_playlist_id=spotify_playlist['id'],
                spotify_synced_at=datetime.now(timezone.utc)
            )
            
            if not success:
                current_app.logger.error(f"Error updating playlist with Spotify ID: {error}")
            
            current_app.logger.info(f"Playlist {playlist_id} exported to Spotify by {current_user.username}")
            return jsonify({
                'success': True,
                'spotify_playlist': spotify_playlist,
                'playlist': playlist.to_dict()
            })
            
        except Exception as e:
            current_app.logger.error(f"Error exporting playlist to Spotify: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/music/spotify/playlists')
    @login_required
    def spotify_playlists():
        """Get user's Spotify playlists"""
        try:
            limit = request.args.get('limit', 50, type=int)
            offset = request.args.get('offset', 0, type=int)
            
            spotify_service = SpotifyService()
            playlists, error = spotify_service.get_user_playlists(limit=limit, offset=offset)
            
            if error:
                return jsonify({'error': error}), 500
            
            return jsonify({
                'playlists': playlists.get('items', []),
                'total': playlists.get('total', 0),
                'limit': playlists.get('limit', limit),
                'offset': playlists.get('offset', offset)
            })
            
        except Exception as e:
            current_app.logger.error(f"Error getting Spotify playlists: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/music/spotify/playlists/<spotify_playlist_id>/import', methods=['POST'])
    @login_required
    def spotify_playlist_import(spotify_playlist_id):
        """Import Spotify playlist to local system"""
        try:
            data = request.get_json() or {}
            playlist_name = data.get('name')  # Optional override
            
            spotify_service = SpotifyService()
            result, error = spotify_service.sync_spotify_to_local(
                spotify_playlist_id=spotify_playlist_id,
                local_user_id=current_user.id,
                playlist_name=playlist_name
            )
            
            if error:
                return jsonify({'error': error}), 500
            
            current_app.logger.info(f"Imported Spotify playlist {spotify_playlist_id} by {current_user.username}")
            return jsonify({
                'success': True,
                'playlist': result['playlist'].to_dict(),
                'added_count': result['added_count'],
                'skipped_count': result['skipped_count']
            }), 201
            
        except Exception as e:
            current_app.logger.error(f"Error importing Spotify playlist: {str(e)}")
            return jsonify({'error': str(e)}), 500

def import_csv_background(job_id, file_path, app):
    """Wrapper to import CSV in background thread"""
    from flask_app.utils.music_importer import import_csv_file
    import_csv_file(job_id, file_path, app)

