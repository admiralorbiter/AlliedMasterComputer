"""
Migration script to add playlist system.

This script creates:
1. playlists table
2. playlist_songs association table

Run this script to add the playlist system to existing databases.

Usage:
    python migrations/add_playlists.py

Or manually run the SQL (SQLite):
    CREATE TABLE IF NOT EXISTS playlists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name VARCHAR(200) NOT NULL,
        description TEXT,
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    
    CREATE INDEX IF NOT EXISTS idx_playlists_user_id ON playlists(user_id);
    
    CREATE TABLE IF NOT EXISTS playlist_songs (
        playlist_id INTEGER NOT NULL,
        track_uri VARCHAR(255) NOT NULL,
        position INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY (playlist_id, track_uri),
        FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
        FOREIGN KEY (track_uri) REFERENCES songs(track_uri) ON DELETE CASCADE
    );
    
    CREATE INDEX IF NOT EXISTS idx_playlist_songs_playlist ON playlist_songs(playlist_id);
    CREATE INDEX IF NOT EXISTS idx_playlist_songs_track ON playlist_songs(track_uri);
    CREATE INDEX IF NOT EXISTS idx_playlist_songs_position ON playlist_songs(playlist_id, position);
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
            playlists_exists = 'playlists' in existing_tables
            playlist_songs_exists = 'playlist_songs' in existing_tables
            
            with db.engine.connect() as conn:
                # Create playlists table if it doesn't exist
                if not playlists_exists:
                    conn.execute(text("""
                        CREATE TABLE playlists (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            name VARCHAR(200) NOT NULL,
                            description TEXT,
                            created_at DATETIME NOT NULL,
                            updated_at DATETIME NOT NULL,
                            FOREIGN KEY (user_id) REFERENCES users(id)
                        )
                    """))
                    print("[OK] Created 'playlists' table")
                else:
                    print("[OK] Table 'playlists' already exists")
                
                # Create index on playlists table if it was just created
                if not playlists_exists:
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_playlists_user_id ON playlists(user_id)"))
                    print("[OK] Created index on 'playlists' table")
                
                # Create playlist_songs association table if it doesn't exist
                if not playlist_songs_exists:
                    conn.execute(text("""
                        CREATE TABLE playlist_songs (
                            playlist_id INTEGER NOT NULL,
                            track_uri VARCHAR(255) NOT NULL,
                            position INTEGER NOT NULL DEFAULT 0,
                            PRIMARY KEY (playlist_id, track_uri),
                            FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
                            FOREIGN KEY (track_uri) REFERENCES songs(track_uri) ON DELETE CASCADE
                        )
                    """))
                    print("[OK] Created 'playlist_songs' table")
                else:
                    print("[OK] Table 'playlist_songs' already exists")
                
                # Create indexes on playlist_songs table if it was just created
                if not playlist_songs_exists:
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_playlist_songs_playlist ON playlist_songs(playlist_id)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_playlist_songs_track ON playlist_songs(track_uri)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_playlist_songs_position ON playlist_songs(playlist_id, position)"))
                    print("[OK] Created indexes on 'playlist_songs' table")
                
                conn.commit()
                print("\n[OK] Migration completed successfully!")
                return True
                
        except Exception as e:
            print(f"\n[ERROR] Migration failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    print("Running playlist migration...")
    success = migrate()
    sys.exit(0 if success else 1)

