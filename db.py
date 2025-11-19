import sqlite3
from typing import List, Optional, Tuple
from config import DB_PATH

def init_db():
    """Initialize the database with tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table for coins (global)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS coins (
            coin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            coin_name TEXT UNIQUE NOT NULL
        )
    ''')
    
    # Table for user subscriptions (many-to-many)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_coins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            username TEXT,
            coin_id INTEGER NOT NULL,
            FOREIGN KEY (coin_id) REFERENCES coins (coin_id),
            UNIQUE(chat_id, coin_id)
        )
    ''')
    
    # Insert default coins if not exist
    default_coins = [("SOL",), ("ETH",), ("BTC",), ("BNB",)]
    for coin_name in default_coins:
        cursor.execute('INSERT OR IGNORE INTO coins (coin_name) VALUES (?)', coin_name)
    
    conn.commit()
    conn.close()

def add_user_if_not_exists(chat_id: int, username: str):
    """Ensure user exists in DB (but since we use user_coins, it's implicit)."""
    pass  # Handled via inserts below

def get_user_coins(chat_id: int) -> List[str]:
    """Get list of coin names for a user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.coin_name FROM user_coins uc
        JOIN coins c ON uc.coin_id = c.coin_id
        WHERE uc.chat_id = ?
    ''', (chat_id,))
    coins = [row[0] for row in cursor.fetchall()]
    conn.close()
    return coins

def add_coin_to_user(chat_id: int, username: str, coin_name: str) -> bool:
    """Add a coin to user's list. Returns True if added (new or existing)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get or create coin_id
    cursor.execute('SELECT coin_id FROM coins WHERE coin_name = ?', (coin_name.upper(),))
    result = cursor.fetchone()
    if result:
        coin_id = result[0]
    else:
        cursor.execute('INSERT INTO coins (coin_name) VALUES (?)', (coin_name.upper(),))
        coin_id = cursor.lastrowid
    
    # Add to user_coins if not already
    try:
        cursor.execute('''
            INSERT INTO user_coins (chat_id, username, coin_id)
            VALUES (?, ?, ?)
        ''', (chat_id, username, coin_id))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        # Already exists
        conn.close()
        return False

def remove_coin_from_user(chat_id: int, coin_name: str) -> bool:
    """Remove a coin from user's list. Returns True if removed."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM user_coins uc
        JOIN coins c ON uc.coin_id = c.coin_id
        WHERE uc.chat_id = ? AND c.coin_name = ?
    ''', (chat_id, coin_name.upper()))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def initialize_user_defaults(chat_id: int, username: str):
    """Add default coins to a new user."""
    default_coins = ["SOL", "ETH", "BTC", "BNB"]
    for coin in default_coins:
        add_coin_to_user(chat_id, username, coin)

def get_all_user_chats() -> List[Tuple[int, str]]:
    """Get all unique (chat_id, username) for daily broadcast."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DISTINCT chat_id, username FROM user_coins
    ''')
    users = cursor.fetchall()
    conn.close()
    return users
