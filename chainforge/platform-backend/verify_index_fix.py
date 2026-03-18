import sqlite3
import os

db_path = "chainforge/platform-backend/chainforge.db"

if not os.path.exists(db_path):
    print(f"Database {db_path} not found.")
else:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA index_list('projects')")
        indexes = cursor.fetchall()
        
        print(f"Indexes on 'projects' table:")
        for idx in indexes:
            print(f"- {idx[1]}")
            
        index_names = [idx[1] for idx in indexes]
        if "ix_projects_owner_id" in index_names:
            print("\nVERIFICATION SUCCESS: ix_projects_owner_id exists.")
        else:
            print("\nVERIFICATION FAILED: ix_projects_owner_id NOT found.")
            
        conn.close()
    except Exception as e:
        print(f"Error verifying database: {e}")
