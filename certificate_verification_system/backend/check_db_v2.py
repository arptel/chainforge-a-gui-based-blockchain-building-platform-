import sqlite3
import os

# Absolute path to project root data
DB_PATH = r"c:\Users\ARTH PATEL\OneDrive\Desktop\ARTH\Sem-6\Blockchain\certificate_verification_system\data\users.sqlite"

if not os.path.exists(DB_PATH):
    print(f"DB not found at {DB_PATH}")
else:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username, password FROM users;")
    rows = cursor.fetchall()
    print("--- USER LIST ---")
    for row in rows:
        print(f"[{row[0]}] -> [{row[1]}]")
    print("-----------------")
    conn.close()
