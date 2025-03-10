import sqlite3
from datetime import datetime

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('brandon_ai.db', check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Table for learned information
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS learned_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            content TEXT,
            timestamp DATETIME,
            verified BOOLEAN DEFAULT FALSE
        )''')

        # Table for conversation history
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            content TEXT,
            timestamp DATETIME
        )''')

        self.conn.commit()

    def add_learned_info(self, category, content):
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT INTO learned_info (category, content, timestamp) VALUES (?, ?, ?)',
            (category, content, datetime.now())
        )
        self.conn.commit()

    def get_all_verified_info(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT category, content FROM learned_info WHERE verified = TRUE')
        return cursor.fetchall()

    def add_conversation(self, role, content):
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT INTO admin_conversations (role, content, timestamp) VALUES (?, ?, ?)',
            (role, content, datetime.now())
        )
        self.conn.commit()

    def get_recent_conversations(self, limit=10):
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT role, content FROM admin_conversations ORDER BY timestamp DESC LIMIT ?',
            (limit,)
        )
        return cursor.fetchall()