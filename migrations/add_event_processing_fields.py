"""
Migration script to add event processing fields to events table.

This migration adds fields to support processing past events with outcomes:
- processed: boolean flag
- processed_at: timestamp when processed
- outcome: string indicating the outcome type
- outcome_reason: text for "didn't happen" reason
- outcome_notes: text for "happened with notes" option

Usage:
    python migrations/add_event_processing_fields.py

Or manually run the SQL (SQLite):
    ALTER TABLE events ADD COLUMN processed BOOLEAN DEFAULT 0 NOT NULL;
    ALTER TABLE events ADD COLUMN processed_at DATETIME;
    ALTER TABLE events ADD COLUMN outcome VARCHAR(50);
    ALTER TABLE events ADD COLUMN outcome_reason TEXT;
    ALTER TABLE events ADD COLUMN outcome_notes TEXT;
    CREATE INDEX IF NOT EXISTS ix_events_processed ON events(processed);
"""

import sys
import os

# Add parent directory to path to import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from flask_app.models import db
from sqlalchemy import text

def migrate():
    """Add event processing columns to events table"""
    with app.app_context():
        try:
            # Check if columns already exist (SQLite)
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('events')]
            
            with db.engine.connect() as conn:
                # Add processed column
                if 'processed' not in columns:
                    conn.execute(text("ALTER TABLE events ADD COLUMN processed BOOLEAN DEFAULT 0 NOT NULL"))
                    conn.commit()
                    print("[OK] Added 'processed' column to events table")
                else:
                    print("[OK] Column 'processed' already exists in events table")
                
                # Add processed_at column
                if 'processed_at' not in columns:
                    conn.execute(text("ALTER TABLE events ADD COLUMN processed_at DATETIME"))
                    conn.commit()
                    print("[OK] Added 'processed_at' column to events table")
                else:
                    print("[OK] Column 'processed_at' already exists in events table")
                
                # Add outcome column
                if 'outcome' not in columns:
                    conn.execute(text("ALTER TABLE events ADD COLUMN outcome VARCHAR(50)"))
                    conn.commit()
                    print("[OK] Added 'outcome' column to events table")
                else:
                    print("[OK] Column 'outcome' already exists in events table")
                
                # Add outcome_reason column
                if 'outcome_reason' not in columns:
                    conn.execute(text("ALTER TABLE events ADD COLUMN outcome_reason TEXT"))
                    conn.commit()
                    print("[OK] Added 'outcome_reason' column to events table")
                else:
                    print("[OK] Column 'outcome_reason' already exists in events table")
                
                # Add outcome_notes column
                if 'outcome_notes' not in columns:
                    conn.execute(text("ALTER TABLE events ADD COLUMN outcome_notes TEXT"))
                    conn.commit()
                    print("[OK] Added 'outcome_notes' column to events table")
                else:
                    print("[OK] Column 'outcome_notes' already exists in events table")
                
                # Create index on processed column if it doesn't exist
                indexes = [idx['name'] for idx in inspector.get_indexes('events')]
                if 'ix_events_processed' not in indexes:
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_events_processed ON events(processed)"))
                    conn.commit()
                    print("[OK] Created index on 'processed' column")
                else:
                    print("[OK] Index 'ix_events_processed' already exists")
            
            print("\n[OK] Migration completed successfully!")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error adding columns: {str(e)}")
            print(f"  You may need to manually run the SQL statements shown above.")
            return False

if __name__ == '__main__':
    print("Running migration: Add event processing fields to events...")
    success = migrate()
    sys.exit(0 if success else 1)

