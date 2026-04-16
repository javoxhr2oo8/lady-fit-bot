import sqlite3

DB_PATH = "users.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        )
    """)
    conn.commit()
    conn.close()

def add_user(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def get_all_users() -> list[int]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT user_id FROM users").fetchall()
    conn.close()
    return [row[0] for row in rows]