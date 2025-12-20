"""
Migration script to add Spotify integration.

This script:
1. Adds spotify_playlist_id and spotify_synced_at fields to playlists table
2. Creates spotify_auth table for storing OAuth tokens

Run this script to add Spotify integration to existing databases.

Usage:
    python migrations/add_spotify_integration.py

Or manually run the SQL (SQLite):
    -- Add columns to playlists table
    ALTER TABLE playlists ADD COLUMN spotify_playlist_id VARCHAR(255);
    ALTER TABLE playlists ADD COLUMN spotify_synced_at DATETIME;
    
    -- Create spotify_auth table
    CREATE TABLE IF NOT EXISTS spotify_auth (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        access_token TEXT NOT NULL,
        refresh_token TEXT,
        token_expires_at DATETIME,
        scope TEXT,
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    
    CREATE INDEX IF NOT EXISTS idx_spotify_auth_user_id ON spotify_auth(user_id);
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
            spotify_auth_exists = 'spotify_auth' in existing_tables
            
            with db.engine.connect() as conn:
                # Add Spotify fields to playlists table
                if playlists_exists:
                    inspector = db.inspect(db.engine)
                    playlists_columns = [col['name'] for col in inspector.get_columns('playlists')]
                    
                    if 'spotify_playlist_id' not in playlists_columns:
                        try:
                            conn.execute(text("ALTER TABLE playlists ADD COLUMN spotify_playlist_id VARCHAR(255)"))
                            conn.commit()
                            print("[OK] Added 'spotify_playlist_id' column to 'playlists' table")
                        except Exception as e:
                            # Column might already exist in some databases
                            error_msg = str(e).lower()
                            if 'duplicate column' not in error_msg and 'already exists' not in error_msg:
                                print(f"[WARNING] Could not add spotify_playlist_id: {str(e)}")
                            else:
                                print("[OK] Column 'spotify_playlist_id' already exists (handled)")
                    else:
                        print("[OK] Column 'spotify_playlist_id' already exists in 'playlists' table")
                    
                    if 'spotify_synced_at' not in playlists_columns:
                        try:
                            conn.execute(text("ALTER TABLE playlists ADD COLUMN spotify_synced_at DATETIME"))
                            conn.commit()
                            print("[OK] Added 'spotify_synced_at' column to 'playlists' table")
                        except Exception as e:
                            error_msg = str(e).lower()
                            if 'duplicate column' not in error_msg and 'already exists' not in error_msg:
                                print(f"[WARNING] Could not add spotify_synced_at: {str(e)}")
                            else:
                                print("[OK] Column 'spotify_synced_at' already exists (handled)")
                    else:
                        print("[OK] Column 'spotify_synced_at' already exists in 'playlists' table")
                else:
                    print("[WARNING] Table 'playlists' does not exist. Please run playlist migration first.")
                
                # Create spotify_auth table if it doesn't exist
                if not spotify_auth_exists:
                    conn.execute(text("""
                        CREATE TABLE spotify_auth (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            access_token TEXT NOT NULL,
                            refresh_token TEXT,
                            token_expires_at DATETIME,
                            scope TEXT,
                            created_at DATETIME NOT NULL,
                            updated_at DATETIME NOT NULL,
                            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                        )
                    """))
                    print("[OK] Created 'spotify_auth' table")
                else:
                    print("[OK] Table 'spotify_auth' already exists")
                
                # Create index on spotify_auth table if it was just created
                if not spotify_auth_exists:
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_spotify_auth_user_id ON spotify_auth(user_id)"))
                    print("[OK] Created index on 'spotify_auth' table")
                
                conn.commit()
                print("\n[OK] Migration completed successfully!")
                return True
                
        except Exception as e:
            print(f"\n[ERROR] Migration failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    print("Running Spotify integration migration...")
    success = migrate()
    sys.exit(0 if success else 1)

