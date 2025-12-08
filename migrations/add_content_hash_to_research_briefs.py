"""
Migration script to add content_hash column to research_briefs table.

Run this script to add the content_hash column to existing databases.

Usage:
    python migrations/add_content_hash_to_research_briefs.py

Or manually run the SQL (SQLite):
    ALTER TABLE research_briefs ADD COLUMN content_hash VARCHAR(64);
    CREATE INDEX IF NOT EXISTS idx_research_briefs_content_hash ON research_briefs(content_hash);
"""

import sys
import os

# Add parent directory to path to import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from flask_app.models import db
from sqlalchemy import text

def migrate():
    """Add content_hash column and index to research_briefs table"""
    with app.app_context():
        try:
            # Check if column already exists (SQLite)
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('research_briefs')]
            
            if 'content_hash' in columns:
                print("✓ Column 'content_hash' already exists in research_briefs table")
                # Check if index exists
                indexes = [idx['name'] for idx in inspector.get_indexes('research_briefs')]
                if 'idx_research_briefs_content_hash' not in indexes:
                    with db.engine.connect() as conn:
                        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_research_briefs_content_hash ON research_briefs(content_hash)"))
                        conn.commit()
                    print("✓ Successfully added index on 'content_hash' column")
                return True
            
            # Add the column (SQLite supports ADD COLUMN)
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE research_briefs ADD COLUMN content_hash VARCHAR(64)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_research_briefs_content_hash ON research_briefs(content_hash)"))
                conn.commit()
            
            print("✓ Successfully added 'content_hash' column and index to research_briefs table")
            return True
            
        except Exception as e:
            print(f"✗ Error adding column: {str(e)}")
            print(f"  You may need to manually run:")
            print(f"    ALTER TABLE research_briefs ADD COLUMN content_hash VARCHAR(64);")
            print(f"    CREATE INDEX IF NOT EXISTS idx_research_briefs_content_hash ON research_briefs(content_hash);")
            return False

if __name__ == '__main__':
    print("Running migration: Add content_hash to research_briefs...")
    success = migrate()
    sys.exit(0 if success else 1)
