"""
Migration script to extend source_type field length in research_briefs table.

This migration extends the source_type column from VARCHAR(10) to VARCHAR(20) to accommodate
the new 'manual' source type value.

Note: SQLite doesn't enforce VARCHAR length constraints, but this migration documents the
schema change and updates the model definition. The column definition will be updated in
the model file.

Usage:
    python migrations/extend_source_type_field_length.py

Note: This is primarily a documentation migration as SQLite doesn't enforce VARCHAR lengths.
The actual column definition is updated in flask_app/models/research_brief.py.
"""

import sys
import os

# Add parent directory to path to import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from flask_app.models import db
from sqlalchemy import text

def migrate():
    """Document the source_type field extension (SQLite doesn't enforce VARCHAR lengths)"""
    with app.app_context():
        try:
            # Check that the column exists
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('research_briefs')]
            
            if 'source_type' not in columns:
                print("✗ Column 'source_type' does not exist in research_briefs table")
                print("  This migration requires the research_briefs table to exist.")
                return False
            
            # SQLite doesn't support modifying column types directly
            # The actual change is in the model definition
            # This migration serves as documentation
            print("✓ Column 'source_type' exists in research_briefs table")
            print("✓ Model definition updated to VARCHAR(20) to support 'manual' source type")
            print("  Note: SQLite doesn't enforce VARCHAR length constraints.")
            print("  The model in flask_app/models/research_brief.py has been updated.")
            return True
            
        except Exception as e:
            print(f"✗ Error checking column: {str(e)}")
            return False

if __name__ == '__main__':
    print("Running migration: Extend source_type field length...")
    success = migrate()
    sys.exit(0 if success else 1)

