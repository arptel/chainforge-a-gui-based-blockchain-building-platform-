import sqlite3, os, glob, json

data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
files = sorted(glob.glob(os.path.join(data_dir, "node_*.sqlite")))

lines = []
for f in files:
    try:
        conn = sqlite3.connect(f)
        bc = conn.execute("SELECT COUNT(*) FROM blocks").fetchone()[0]
        # Get highest idx
        highest_idx_row = conn.execute("SELECT MAX(idx) FROM blocks").fetchone()
        highest_idx = highest_idx_row[0] if highest_idx_row and highest_idx_row[0] is not None else -1
        mtime = os.path.getmtime(f)
        lines.append(f"{os.path.basename(f)}: {bc} blocks, MaxIdx: {highest_idx}, MTime: {mtime}")
        
        # List all block indexes and hashes
        rows = conn.execute("SELECT idx, hash FROM blocks ORDER BY idx ASC").fetchall()
        for r in rows:
            lines.append(f"  - Block {r[0]}: {r[1]}")
    except Exception as e:
        lines.append(f"{os.path.basename(f)}: ERROR: {e}")

with open(os.path.join(data_dir, "report2.txt"), "w") as out:
    out.write("\n".join(lines))
print("DONE - wrote report2.txt")
