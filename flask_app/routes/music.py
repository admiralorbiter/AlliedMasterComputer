# flask_app/routes/music.py

from flask import flash, redirect, render_template, url_for, request, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from flask_app.models import Song, MusicImportJob, db
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
            
            # Convert explicit filter string to bool
            explicit_bool = None
            if explicit_filter == 'true':
                explicit_bool = True
            elif explicit_filter == 'false':
                explicit_bool = False
            
            # Search songs with filters
            songs = Song.search(
                query=query if query else None,
                explicit_filter=explicit_bool,
                min_popularity=min_popularity,
                page=page,
                per_page=20
            )
            
            if songs is None:
                flash('An error occurred while loading the music library.', 'danger')
                songs = Song.query.paginate(page=page, per_page=20, error_out=False)
            
            current_app.logger.info(f"Music library accessed by {current_user.username}")
            return render_template('music/library.html', songs=songs, query=query, 
                                 explicit_filter=explicit_filter, min_popularity=min_popularity)
            
        except Exception as e:
            current_app.logger.error(f"Error in music library: {str(e)}")
            flash('An error occurred while loading the music library.', 'danger')
            songs = Song.query.paginate(page=1, per_page=20, error_out=False)
            return render_template('music/library.html', songs=songs, query='', 
                                 explicit_filter=None, min_popularity=None)
    
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

def import_csv_background(job_id, file_path, app):
    """Wrapper to import CSV in background thread"""
    from flask_app.utils.music_importer import import_csv_file
    import_csv_file(job_id, file_path, app)

