"""
Migration script to add goals and projects system.

This script creates:
1. projects table
2. goals table
3. Adds goal_id column to todos table

Run this script to add the goals and projects system to existing databases.

Usage:
    python migrations/add_goals_and_projects.py

Or manually run the SQL (SQLite):
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name VARCHAR(200) NOT NULL,
        description TEXT,
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    
    CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
    
    CREATE TABLE IF NOT EXISTS goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title VARCHAR(200) NOT NULL,
        description TEXT,
        goal_type VARCHAR(20) NOT NULL,
        project_id INTEGER,
        completed BOOLEAN NOT NULL DEFAULT 0,
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
    );
    
    CREATE INDEX IF NOT EXISTS idx_goals_user_id ON goals(user_id);
    CREATE INDEX IF NOT EXISTS idx_goals_goal_type ON goals(goal_type);
    CREATE INDEX IF NOT EXISTS idx_goals_project_id ON goals(project_id);
    CREATE INDEX IF NOT EXISTS idx_goals_completed ON goals(completed);
    
    ALTER TABLE todos ADD COLUMN goal_id INTEGER;
    CREATE INDEX IF NOT EXISTS idx_todos_goal_id ON todos(goal_id);
"""

import sys
import os

# Add parent directory to path to import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from flask_app.models import db
from sqlalchemy import text, inspect

def migrate():
    """Add projects and goals tables, and goal_id to todos"""
    with app.app_context():
        try:
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            # Check if tables exist
            projects_exists = 'projects' in existing_tables
            goals_exists = 'goals' in existing_tables
            
            # Check if goal_id column exists in todos
            todos_has_goal_id = False
            if 'todos' in existing_tables:
                todos_columns = [col['name'] for col in inspector.get_columns('todos')]
                todos_has_goal_id = 'goal_id' in todos_columns
            
            with db.engine.connect() as conn:
                # Create projects table if it doesn't exist
                if not projects_exists:
                    conn.execute(text("""
                        CREATE TABLE projects (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            name VARCHAR(200) NOT NULL,
                            description TEXT,
                            created_at DATETIME NOT NULL,
                            updated_at DATETIME NOT NULL,
                            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                        )
                    """))
                    print("✓ Created 'projects' table")
                else:
                    print("✓ Table 'projects' already exists")
                
                # Create index on projects.user_id if it doesn't exist
                if not projects_exists:
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id)"))
                    print("✓ Created index on 'projects.user_id'")
                
                # Create goals table if it doesn't exist
                if not goals_exists:
                    conn.execute(text("""
                        CREATE TABLE goals (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            title VARCHAR(200) NOT NULL,
                            description TEXT,
                            goal_type VARCHAR(20) NOT NULL,
                            project_id INTEGER,
                            completed BOOLEAN NOT NULL DEFAULT 0,
                            created_at DATETIME NOT NULL,
                            updated_at DATETIME NOT NULL,
                            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
                        )
                    """))
                    print("✓ Created 'goals' table")
                else:
                    print("✓ Table 'goals' already exists")
                
                # Create indexes on goals table if it doesn't exist
                if not goals_exists:
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_goals_user_id ON goals(user_id)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_goals_goal_type ON goals(goal_type)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_goals_project_id ON goals(project_id)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_goals_completed ON goals(completed)"))
                    print("✓ Created indexes on 'goals' table")
                
                # Add goal_id column to todos if it doesn't exist
                if not todos_has_goal_id:
                    try:
                        conn.execute(text("ALTER TABLE todos ADD COLUMN goal_id INTEGER"))
                        print("✓ Added 'goal_id' column to 'todos' table")
                        
                        # Create index on todos.goal_id
                        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_todos_goal_id ON todos(goal_id)"))
                        print("✓ Created index on 'todos.goal_id'")
                    except Exception as e:
                        # SQLite might not support adding foreign key constraints in ALTER TABLE
                        # We'll just add the column without the constraint
                        print(f"  Note: Added goal_id column (foreign key constraint may need to be added manually)")
                else:
                    print("✓ Column 'goal_id' already exists in 'todos' table")
                
                conn.commit()
            
            print("✓ Successfully migrated goals and projects system")
            return True
            
        except Exception as e:
            print(f"✗ Error during migration: {str(e)}")
            import traceback
            print(traceback.format_exc())
            print(f"  You may need to manually run the SQL commands shown in the docstring.")
            return False

if __name__ == '__main__':
    print("Running migration: Add goals and projects...")
    success = migrate()
    sys.exit(0 if success else 1)

