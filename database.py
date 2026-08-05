import sqlite3
from typing import List, Tuple
from contextlib import closing

DB_PATH = "alerts.db"

def init_db():
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:
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
                    post_id TEXT PRIMARY KEY,
                    url TEXT,
                    timestamp DATETIME DEFAULT (datetime('now', 'localtime'))
                )
            ''')
            # 기존 DB에 url 컬럼이 없는 경우 마이그레이션
            try:
                cursor.execute('ALTER TABLE sent_alerts ADD COLUMN url TEXT')
            except sqlite3.OperationalError:
                pass  # 이미 컬럼이 존재함

def add_keyword(user_id: int, channel_id: int, keyword: str) -> bool:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO keywords (user_id, channel_id, keyword) VALUES (?, ?, ?)', 
                               (user_id, channel_id, keyword))
            return True
        except sqlite3.IntegrityError:
            return False

def remove_keyword(user_id: int, channel_id: int, keyword: str) -> bool:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM keywords WHERE user_id = ? AND channel_id = ? AND keyword = ?', 
                           (user_id, channel_id, keyword))
            return cursor.rowcount > 0

def remove_all_keywords(user_id: int, channel_id: int) -> int:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM keywords WHERE user_id = ? AND channel_id = ?', 
                           (user_id, channel_id))
            return cursor.rowcount

def get_all_keywords() -> List[Tuple[int, int, str]]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, channel_id, keyword FROM keywords')
        return cursor.fetchall()

def get_user_keywords(user_id: int, channel_id: int) -> List[str]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT keyword FROM keywords WHERE user_id = ? AND channel_id = ?', 
                       (user_id, channel_id))
        return [row[0] for row in cursor.fetchall()]

def is_alert_sent(post_id: str) -> bool:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM sent_alerts WHERE post_id = ?', (post_id,))
        return cursor.fetchone() is not None

def mark_alert_sent(post_id: str, url: str = ''):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR IGNORE INTO sent_alerts (post_id, url, timestamp) VALUES (?, ?, datetime("now", "localtime"))', (post_id, url))
