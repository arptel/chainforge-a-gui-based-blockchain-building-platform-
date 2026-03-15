import sqlite3
import os

DB_PATH = r"c:\Users\ARTH PATEL\OneDrive\Desktop\ARTH\Sem-6\Blockchain\certificate_verification_system\data\users.sqlite"

if not os.path.exists(DB_PATH):
    print(f"DB not found at {DB_PATH}")
else:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username, password FROM users;")
    rows = cursor.fetchall()
    for row in rows:
        print(f"User: {row[0]}, Password: {row[1]}")
    conn.close()
