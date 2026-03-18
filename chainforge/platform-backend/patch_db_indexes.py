import sqlite3
import os

db_path = "chainforge.db"

if not os.path.exists(db_path):
    print(f"Database {db_path} not found. Skipping manual patch.")
else:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if index already exists
        cursor.execute("PRAGMA index_list('projects')")
        indexes = cursor.fetchall()
        index_names = [idx[1] for idx in indexes]
        
        if "ix_projects_owner_id" not in index_names:
            print("Adding index ix_projects_owner_id to projects table...")
            cursor.execute("CREATE INDEX ix_projects_owner_id ON projects (owner_id)")
            conn.commit()
            print("Index added successfully.")
        else:
            print("Index ix_projects_owner_id already exists.")
            
        conn.close()
    except Exception as e:
        print(f"Error patching database: {e}")
