"""
Migration script to add music library system.

This script creates:
1. songs table
2. music_import_jobs table

Run this script to add the music library system to existing databases.

Usage:
    python migrations/add_music_library.py

Or manually run the SQL (SQLite):
    CREATE TABLE IF NOT EXISTS songs (
        track_uri VARCHAR(255) PRIMARY KEY NOT NULL,
        track_name VARCHAR(500),
        album_name VARCHAR(500),
        artist_names VARCHAR(500),
        release_date VARCHAR(50),
        duration_ms INTEGER,
        popularity INTEGER,
        explicit BOOLEAN,
        added_by VARCHAR(100),
        added_at VARCHAR(100),
        genres TEXT,
        record_label VARCHAR(500),
        danceability FLOAT,
        energy FLOAT,
        "key" INTEGER,
        loudness FLOAT,
        mode INTEGER,
        speechiness FLOAT,
        acousticness FLOAT,
        instrumentalness FLOAT,
        liveness FLOAT,
        valence FLOAT,
        tempo FLOAT,
        time_signature INTEGER,
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL
    );
    
    CREATE INDEX IF NOT EXISTS idx_songs_track_name ON songs(track_name);
    CREATE INDEX IF NOT EXISTS idx_songs_artist_names ON songs(artist_names);
    CREATE INDEX IF NOT EXISTS idx_songs_popularity ON songs(popularity);
    CREATE INDEX IF NOT EXISTS idx_songs_explicit ON songs(explicit);
    
    CREATE TABLE IF NOT EXISTS music_import_jobs (
        id VARCHAR(36) PRIMARY KEY NOT NULL,
        status VARCHAR(20) NOT NULL,
        total_rows INTEGER NOT NULL,
        processed_rows INTEGER NOT NULL,
        inserted_count INTEGER NOT NULL,
        duplicate_count INTEGER NOT NULL,
        error_count INTEGER NOT NULL,
        original_filename VARCHAR(255) NOT NULL,
        stored_path VARCHAR(500) NOT NULL,
        started_at DATETIME,
        finished_at DATETIME,
        error_message TEXT,
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL
    );
"""

import sys
import os

# Add parent directory to path to import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from flask_app.models import db
from sqlalchemy import text, inspect

def migrate():
    """Run the migration"""
    with app.app_context():
        try:
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            # Check if tables exist
            songs_exists = 'songs' in existing_tables
            jobs_exists = 'music_import_jobs' in existing_tables
            
            with db.engine.connect() as conn:
                # Create songs table if it doesn't exist
                if not songs_exists:
                    conn.execute(text("""
                        CREATE TABLE songs (
                            track_uri VARCHAR(255) PRIMARY KEY NOT NULL,
                            track_name VARCHAR(500),
                            album_name VARCHAR(500),
                            artist_names VARCHAR(500),
                            release_date VARCHAR(50),
                            duration_ms INTEGER,
                            popularity INTEGER,
                            explicit BOOLEAN,
                            added_by VARCHAR(100),
                            added_at VARCHAR(100),
                            genres TEXT,
                            record_label VARCHAR(500),
                            danceability FLOAT,
                            energy FLOAT,
                            "key" INTEGER,
                            loudness FLOAT,
                            mode INTEGER,
                            speechiness FLOAT,
                            acousticness FLOAT,
                            instrumentalness FLOAT,
                            liveness FLOAT,
                            valence FLOAT,
                            tempo FLOAT,
                            time_signature INTEGER,
                            created_at DATETIME NOT NULL,
                            updated_at DATETIME NOT NULL
                        )
                    """))
                    print("[OK] Created 'songs' table")
                else:
                    print("[OK] Table 'songs' already exists")
                
                # Create indexes on songs table if it was just created
                if not songs_exists:
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_songs_track_name ON songs(track_name)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_songs_artist_names ON songs(artist_names)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_songs_popularity ON songs(popularity)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_songs_explicit ON songs(explicit)"))
                    print("[OK] Created indexes on 'songs' table")
                
                # Create music_import_jobs table if it doesn't exist
                if not jobs_exists:
                    conn.execute(text("""
                        CREATE TABLE music_import_jobs (
                            id VARCHAR(36) PRIMARY KEY NOT NULL,
                            status VARCHAR(20) NOT NULL,
                            total_rows INTEGER NOT NULL,
                            processed_rows INTEGER NOT NULL,
                            inserted_count INTEGER NOT NULL,
                            duplicate_count INTEGER NOT NULL,
                            error_count INTEGER NOT NULL,
                            original_filename VARCHAR(255) NOT NULL,
                            stored_path VARCHAR(500) NOT NULL,
                            started_at DATETIME,
                            finished_at DATETIME,
                            error_message TEXT,
                            created_at DATETIME NOT NULL,
                            updated_at DATETIME NOT NULL
                        )
                    """))
                    print("[OK] Created 'music_import_jobs' table")
                else:
                    print("[OK] Table 'music_import_jobs' already exists")
                
                conn.commit()
                print("\n[OK] Migration completed successfully!")
                return True
                
        except Exception as e:
            print(f"\n[ERROR] Migration failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    print("Running music library migration...")
    success = migrate()
    sys.exit(0 if success else 1)

