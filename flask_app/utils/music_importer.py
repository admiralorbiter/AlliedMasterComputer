# flask_app/utils/music_importer.py

import csv
import os
from datetime import datetime, timezone
from flask import current_app
from flask_app.models import db, Song, MusicImportJob

def safe_int(value, default=None):
    """Safely convert value to int"""
    if value is None or value == '':
        return default
    try:
        return int(float(value))  # Handle "123.0" strings
    except (ValueError, TypeError):
        return default

def safe_float(value, default=None):
    """Safely convert value to float"""
    if value is None or value == '':
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_bool(value, default=False):
    """Safely convert value to bool"""
    if value is None or value == '':
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 't')
    return bool(value)

def count_csv_rows(file_path):
    """Count total rows in CSV file (excluding header)"""
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:  # utf-8-sig handles BOM
            reader = csv.reader(f)
            # Skip header
            next(reader, None)
            return sum(1 for _ in reader)
    except Exception as e:
        current_app.logger.error(f"Error counting CSV rows: {str(e)}")
        return 0

def import_csv_file(job_id, file_path, app):
    """Import CSV file in background thread"""
    with app.app_context():
        job = MusicImportJob.find_by_id(job_id)
        if not job:
            current_app.logger.error(f"Import job {job_id} not found")
            return
        
        try:
            # Update status to running
            job.status = 'running'
            job.started_at = datetime.now(timezone.utc)
            job.total_rows = count_csv_rows(file_path)
            db.session.commit()
            
            current_app.logger.info(f"Starting import job {job_id} with {job.total_rows} rows")
            
            # Process CSV file
            with open(file_path, 'r', encoding='utf-8-sig') as f:  # utf-8-sig handles BOM
                reader = csv.DictReader(f)
                
                batch = []
                batch_size = 50  # Commit every 50 rows
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 because row 1 is header
                    try:
                        # Skip completely empty rows
                        if not row or not any(str(v).strip() for v in row.values() if v):
                            continue
                        
                        # Validate required field - handle BOM in column name
                        track_uri = row.get('Track URI', '').strip() or row.get('\ufeffTrack URI', '').strip()
                        if not track_uri:
                            job.error_count += 1
                            # Only log first 10 and then every 100th to reduce log spam
                            if job.error_count <= 10 or job.error_count % 100 == 0:
                                current_app.logger.warning(f"Row {row_num}: Missing Track URI, skipping")
                            continue
                        
                        # Check for duplicate
                        existing = Song.find_by_track_uri(track_uri)
                        if existing:
                            job.duplicate_count += 1
                            continue
                        
                        # Create new song record
                        song = Song(
                            track_uri=track_uri,
                            track_name=row.get('Track Name', '').strip() or None,
                            album_name=row.get('Album Name', '').strip() or None,
                            artist_names=row.get('Artist Name(s)', '').strip() or None,
                            release_date=row.get('Release Date', '').strip() or None,
                            duration_ms=safe_int(row.get('Duration (ms)')),
                            popularity=safe_int(row.get('Popularity')),
                            explicit=safe_bool(row.get('Explicit')),
                            added_by=row.get('Added By', '').strip() or None,
                            added_at=row.get('Added At', '').strip() or None,
                            genres=row.get('Genres', '').strip() or None,
                            record_label=row.get('Record Label', '').strip() or None,
                            danceability=safe_float(row.get('Danceability')),
                            energy=safe_float(row.get('Energy')),
                            key=safe_int(row.get('Key')),
                            loudness=safe_float(row.get('Loudness')),
                            mode=safe_int(row.get('Mode')),
                            speechiness=safe_float(row.get('Speechiness')),
                            acousticness=safe_float(row.get('Acousticness')),
                            instrumentalness=safe_float(row.get('Instrumentalness')),
                            liveness=safe_float(row.get('Liveness')),
                            valence=safe_float(row.get('Valence')),
                            tempo=safe_float(row.get('Tempo')),
                            time_signature=safe_int(row.get('Time Signature')),
                        )
                        
                        batch.append(song)
                        job.inserted_count += 1
                        
                        # Commit in batches
                        if len(batch) >= batch_size:
                            db.session.add_all(batch)
                            db.session.commit()
                            batch = []
                        
                        # Update progress every 25 rows
                        if row_num % 25 == 0:
                            job.processed_rows = row_num
                            db.session.commit()
                            current_app.logger.debug(f"Import progress: {row_num}/{job.total_rows}")
                    
                    except Exception as e:
                        job.error_count += 1
                        current_app.logger.error(f"Error processing row {row_num}: {str(e)}")
                        continue
                
                # Commit remaining batch
                if batch:
                    db.session.add_all(batch)
                    db.session.commit()
                
                # Final update
                job.processed_rows = job.total_rows
                job.status = 'completed'
                job.finished_at = datetime.now(timezone.utc)
                db.session.commit()
                
                current_app.logger.info(
                    f"Import job {job_id} completed: "
                    f"{job.inserted_count} inserted, {job.duplicate_count} duplicates, {job.error_count} errors"
                )
        
        except Exception as e:
            current_app.logger.error(f"Import job {job_id} failed: {str(e)}")
            job.status = 'failed'
            job.finished_at = datetime.now(timezone.utc)
            job.error_message = str(e)
            db.session.commit()
        
        finally:
            # Clean up uploaded file
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    current_app.logger.info(f"Cleaned up import file: {file_path}")
            except Exception as e:
                current_app.logger.warning(f"Failed to clean up import file {file_path}: {str(e)}")

