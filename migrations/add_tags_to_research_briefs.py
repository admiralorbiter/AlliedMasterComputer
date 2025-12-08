"""
Migration script to add tags system to research briefs.

This script creates:
1. tags table
2. research_brief_tags association table
3. Indexes for performance

Run this script to add the tagging system to existing databases.

Usage:
    python migrations/add_tags_to_research_briefs.py

Or manually run the SQL (SQLite):
    CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL UNIQUE,
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL
    );
    
    CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name);
    
    CREATE TABLE IF NOT EXISTS research_brief_tags (
        research_brief_id INTEGER NOT NULL,
        tag_id INTEGER NOT NULL,
        PRIMARY KEY (research_brief_id, tag_id),
        FOREIGN KEY (research_brief_id) REFERENCES research_briefs(id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
    );
    
    CREATE INDEX IF NOT EXISTS idx_research_brief_tags_brief ON research_brief_tags(research_brief_id);
    CREATE INDEX IF NOT EXISTS idx_research_brief_tags_tag ON research_brief_tags(tag_id);
"""

import sys
import os

# Add parent directory to path to import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from flask_app.models import db
from sqlalchemy import text, inspect

def migrate():
    """Add tags table and association table"""
    with app.app_context():
        try:
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            # Check if tags table exists
            tags_exists = 'tags' in existing_tables
            association_exists = 'research_brief_tags' in existing_tables
            
            with db.engine.connect() as conn:
                # Create tags table if it doesn't exist
                if not tags_exists:
                    conn.execute(text("""
                        CREATE TABLE tags (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name VARCHAR(100) NOT NULL UNIQUE,
                            created_at DATETIME NOT NULL,
                            updated_at DATETIME NOT NULL
                        )
                    """))
                    print("✓ Created 'tags' table")
                else:
                    print("✓ Table 'tags' already exists")
                
                # Create index on tags.name if it doesn't exist
                if not tags_exists:
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name)"))
                    print("✓ Created index on 'tags.name'")
                
                # Create association table if it doesn't exist
                if not association_exists:
                    conn.execute(text("""
                        CREATE TABLE research_brief_tags (
                            research_brief_id INTEGER NOT NULL,
                            tag_id INTEGER NOT NULL,
                            PRIMARY KEY (research_brief_id, tag_id),
                            FOREIGN KEY (research_brief_id) REFERENCES research_briefs(id) ON DELETE CASCADE,
                            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
                        )
                    """))
                    print("✓ Created 'research_brief_tags' association table")
                else:
                    print("✓ Table 'research_brief_tags' already exists")
                
                # Create indexes on association table
                if not association_exists:
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_research_brief_tags_brief ON research_brief_tags(research_brief_id)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_research_brief_tags_tag ON research_brief_tags(tag_id)"))
                    print("✓ Created indexes on 'research_brief_tags' table")
                
                conn.commit()
            
            print("✓ Successfully migrated tags system")
            return True
            
        except Exception as e:
            print(f"✗ Error during migration: {str(e)}")
            import traceback
            print(traceback.format_exc())
            print(f"  You may need to manually run the SQL commands shown in the docstring.")
            return False

if __name__ == '__main__':
    print("Running migration: Add tags to research briefs...")
    success = migrate()
    sys.exit(0 if success else 1)