"""
Migration script to add project management features.

This script creates:
1. project_notes table
2. project_links table
3. project_research_briefs association table (many-to-many)

Run this script to add the project management features to existing databases.

Usage:
    python migrations/add_project_management_features.py
"""

import sys
import os

# Add parent directory to path to import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from flask_app.models import db
from sqlalchemy import text, inspect

def migrate():
    """Add project notes, links, and research brief associations"""
    with app.app_context():
        try:
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            # Check if tables exist
            notes_exists = 'project_notes' in existing_tables
            links_exists = 'project_links' in existing_tables
            association_exists = 'project_research_briefs' in existing_tables
            
            with db.engine.connect() as conn:
                # Create project_notes table if it doesn't exist
                if not notes_exists:
                    conn.execute(text("""
                        CREATE TABLE project_notes (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            project_id INTEGER NOT NULL,
                            user_id INTEGER NOT NULL,
                            content TEXT NOT NULL,
                            created_at DATETIME NOT NULL,
                            updated_at DATETIME NOT NULL,
                            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                        )
                    """))
                    print("✓ Created 'project_notes' table")
                else:
                    print("✓ Table 'project_notes' already exists")
                
                # Create indexes on project_notes if it doesn't exist
                if not notes_exists:
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_project_notes_project_id ON project_notes(project_id)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_project_notes_user_id ON project_notes(user_id)"))
                    print("✓ Created indexes on 'project_notes' table")
                
                # Create project_links table if it doesn't exist
                if not links_exists:
                    conn.execute(text("""
                        CREATE TABLE project_links (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            project_id INTEGER NOT NULL,
                            user_id INTEGER NOT NULL,
                            title VARCHAR(200) NOT NULL,
                            url VARCHAR(500) NOT NULL,
                            created_at DATETIME NOT NULL,
                            updated_at DATETIME NOT NULL,
                            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                        )
                    """))
                    print("✓ Created 'project_links' table")
                else:
                    print("✓ Table 'project_links' already exists")
                
                # Create indexes on project_links if it doesn't exist
                if not links_exists:
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_project_links_project_id ON project_links(project_id)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_project_links_user_id ON project_links(user_id)"))
                    print("✓ Created indexes on 'project_links' table")
                
                # Create project_research_briefs association table if it doesn't exist
                if not association_exists:
                    conn.execute(text("""
                        CREATE TABLE project_research_briefs (
                            project_id INTEGER NOT NULL,
                            research_brief_id INTEGER NOT NULL,
                            PRIMARY KEY (project_id, research_brief_id),
                            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                            FOREIGN KEY (research_brief_id) REFERENCES research_briefs(id) ON DELETE CASCADE
                        )
                    """))
                    print("✓ Created 'project_research_briefs' association table")
                else:
                    print("✓ Table 'project_research_briefs' already exists")
                
                # Create indexes on association table if it doesn't exist
                if not association_exists:
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_project_research_briefs_project ON project_research_briefs(project_id)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_project_research_briefs_brief ON project_research_briefs(research_brief_id)"))
                    print("✓ Created indexes on 'project_research_briefs' table")
                
                conn.commit()
            
            print("✓ Successfully migrated project management features")
            return True
            
        except Exception as e:
            print(f"✗ Error during migration: {str(e)}")
            import traceback
            print(traceback.format_exc())
            print(f"  You may need to manually run the SQL commands.")
            return False

if __name__ == '__main__':
    print("Running migration: Add project management features...")
    success = migrate()
    sys.exit(0 if success else 1)

