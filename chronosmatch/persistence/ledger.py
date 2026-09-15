import sqlite3

def trade_count(db_path):
    with sqlite3.connect(db_path) as conn:
        return conn.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
