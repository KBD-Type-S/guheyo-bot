import sqlite3
from typing import List, Tuple

DB_PATH = "alerts.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS keywords (
                user_id INTEGER,
                channel_id INTEGER,
                keyword TEXT,
                PRIMARY KEY (user_id, channel_id, keyword)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sent_alerts (
                post_id TEXT PRIMARY KEY
            )
        ''')
        conn.commit()

def add_keyword(user_id: int, channel_id: int, keyword: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO keywords (user_id, channel_id, keyword) VALUES (?, ?, ?)', 
                           (user_id, channel_id, keyword))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def remove_keyword(user_id: int, channel_id: int, keyword: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM keywords WHERE user_id = ? AND channel_id = ? AND keyword = ?', 
                       (user_id, channel_id, keyword))
        deleted = cursor.rowcount > 0
        conn.commit()
        return deleted

def remove_all_keywords(user_id: int, channel_id: int) -> int:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM keywords WHERE user_id = ? AND channel_id = ?', 
                       (user_id, channel_id))
        deleted_count = cursor.rowcount
        conn.commit()
        return deleted_count

def get_all_keywords() -> List[Tuple[int, int, str]]:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, channel_id, keyword FROM keywords')
        return cursor.fetchall()

def get_user_keywords(user_id: int, channel_id: int) -> List[str]:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT keyword FROM keywords WHERE user_id = ? AND channel_id = ?', 
                       (user_id, channel_id))
        return [row[0] for row in cursor.fetchall()]

def is_alert_sent(post_id: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM sent_alerts WHERE post_id = ?', (post_id,))
        return cursor.fetchone() is not None

def mark_alert_sent(post_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO sent_alerts (post_id) VALUES (?)', (post_id,))
        conn.commit()
