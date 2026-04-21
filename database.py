import sqlite3

DB_PATH = "users.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            username TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_user(user_id: int, first_name: str = None, last_name: str = None, username: str = None):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO users (user_id, first_name, last_name, username)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            first_name = excluded.first_name,
            last_name = excluded.last_name,
            username = excluded.username
    """, (user_id, first_name, last_name, username))
    conn.commit()
    conn.close()

def get_all_users() -> list[int]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT user_id FROM users").fetchall()
    conn.close()
    return [row[0] for row in rows]