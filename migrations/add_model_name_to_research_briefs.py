"""
Migration script to add model_name column to research_briefs table.

Run this script to add the model_name column to existing databases.

Usage:
    python migrations/add_model_name_to_research_briefs.py

Or manually run the SQL (SQLite):
    ALTER TABLE research_briefs ADD COLUMN model_name VARCHAR(50);
"""

import sys
import os

# Add parent directory to path to import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from flask_app.models import db
from sqlalchemy import text

def migrate():
    """Add model_name column to research_briefs table"""
    with app.app_context():
        try:
            # Check if column already exists (SQLite)
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('research_briefs')]
            
            if 'model_name' in columns:
                print("✓ Column 'model_name' already exists in research_briefs table")
                return True
            
            # Add the column (SQLite supports ADD COLUMN)
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE research_briefs ADD COLUMN model_name VARCHAR(50)"))
                conn.commit()
            
            print("✓ Successfully added 'model_name' column to research_briefs table")
            return True
            
        except Exception as e:
            print(f"✗ Error adding column: {str(e)}")
            print(f"  You may need to manually run: ALTER TABLE research_briefs ADD COLUMN model_name VARCHAR(50);")
            return False

if __name__ == '__main__':
    print("Running migration: Add model_name to research_briefs...")
    success = migrate()
    sys.exit(0 if success else 1)
