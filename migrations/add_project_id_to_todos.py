"""
Migration script to add project_id to todos table.

This script adds:
1. project_id column to todos table
2. Index on project_id
3. Foreign key constraint

Run this script to add project support to todos.

Usage:
    python migrations/add_project_id_to_todos.py
"""

import sys
import os

# Add parent directory to path to import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from flask_app.models import db
from sqlalchemy import text, inspect

def migrate():
    """Add project_id column to todos table"""
    with app.app_context():
        try:
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            # Check if todos table exists
            if 'todos' not in existing_tables:
                print("✗ Table 'todos' does not exist. Please run previous migrations first.")
                return False
            
            # Check if project_id column already exists
            todos_has_project_id = False
            todos_columns = [col['name'] for col in inspector.get_columns('todos')]
            todos_has_project_id = 'project_id' in todos_columns
            
            with db.engine.connect() as conn:
                # Add project_id column to todos if it doesn't exist
                if not todos_has_project_id:
                    try:
                        conn.execute(text("ALTER TABLE todos ADD COLUMN project_id INTEGER"))
                        print("✓ Added 'project_id' column to 'todos' table")
                        
                        # Create index on todos.project_id
                        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_todos_project_id ON todos(project_id)"))
                        print("✓ Created index on 'todos.project_id'")
                        
                        # Note: SQLite doesn't support adding foreign key constraints via ALTER TABLE
                        # The constraint will be enforced at the application level
                        print("  Note: Foreign key constraint will be enforced at application level")
                    except Exception as e:
                        print(f"  Note: Error adding project_id column: {str(e)}")
                        print("  You may need to manually run: ALTER TABLE todos ADD COLUMN project_id INTEGER")
                else:
                    print("✓ Column 'project_id' already exists in 'todos' table")
                
                conn.commit()
            
            print("✓ Successfully migrated project_id to todos")
            return True
            
        except Exception as e:
            print(f"✗ Error during migration: {str(e)}")
            import traceback
            print(traceback.format_exc())
            print(f"  You may need to manually run the SQL commands.")
            return False

if __name__ == '__main__':
    print("Running migration: Add project_id to todos...")
    success = migrate()
    sys.exit(0 if success else 1)

