# auth_utils.py
import sqlite3
import os

DB_PATH = os.getenv("AUTH_DB_PATH", "auth.db")

def create_db():
    """Create the SQLite DB and token table if not exists."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tokens (
            token TEXT PRIMARY KEY
        );
    """)
    conn.commit()
    conn.close()



def add_token(token):
    """Add a token to the database (if not already present)."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO tokens (token) VALUES (?)", (token,))
    conn.commit()
    conn.close()

def is_valid_token(token):
    """Check if a token exists in the DB."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT token FROM tokens WHERE token = ?", (token,))
    result = cur.fetchone()
    conn.close()
    return result is not None

def get_auth_token():
    """Get the first token from DB (for client use)."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT token FROM tokens LIMIT 1")
    result = cur.fetchone()
    conn.close()
    return result[0] if result else None
