# flask_app/routes/music.py

from flask import flash, redirect, render_template, url_for, request, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from flask_app.models import Song, MusicImportJob, Playlist, db
import os
import threading
from datetime import datetime, timezone

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

def import_csv_background(job_id, file_path, app):
    """Wrapper to import CSV in background thread"""
    from flask_app.utils.music_importer import import_csv_file
    import_csv_file(job_id, file_path, app)

