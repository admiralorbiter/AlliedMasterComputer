"""
Migration script to add url column to research_briefs table.

This migration adds a url field to store article URLs separately from citations.

Usage:
    python migrations/add_url_to_research_briefs.py

Or manually run the SQL (SQLite):
    ALTER TABLE research_briefs ADD COLUMN url VARCHAR(500);
"""

import sys
import os

# Add parent directory to path to import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from flask_app.models import db
from sqlalchemy import text

def migrate():
    """Add url column to research_briefs table"""
    with app.app_context():
        try:
            # Check if column already exists (SQLite)
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('research_briefs')]
            
            if 'url' in columns:
                print("✓ Column 'url' already exists in research_briefs table")
                return True
            
            # Add the column (SQLite supports ADD COLUMN)
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE research_briefs ADD COLUMN url VARCHAR(500)"))
                conn.commit()
            
            print("✓ Successfully added 'url' column to research_briefs table")
            return True
            
        except Exception as e:
            print(f"✗ Error adding column: {str(e)}")
            print(f"  You may need to manually run: ALTER TABLE research_briefs ADD COLUMN url VARCHAR(500);")
            return False

if __name__ == '__main__':
    print("Running migration: Add url to research_briefs...")
    success = migrate()
    sys.exit(0 if success else 1)

