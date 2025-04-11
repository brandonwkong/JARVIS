import sqlite3
from datetime import datetime

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('brandon_ai.db', check_same_thread=False)
        self.create_tables()
        print("Database initialized")

    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Table for learned information
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS learned_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            content TEXT,
            timestamp DATETIME,
            verified BOOLEAN DEFAULT TRUE
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
        print(f"\n=== ADDING TO DATABASE ===")
        print(f"Category: {category}")
        print(f"Content: {content}")
        
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT INTO learned_info (category, content, timestamp, verified) VALUES (?, ?, ?, ?)',
            (category, content, datetime.now(), True)
        )
        self.conn.commit()
        print("Information added to database successfully")
        print("===========================\n")

    def get_all_verified_info(self):
        print("\n=== RETRIEVING FROM DATABASE ===")
        cursor = self.conn.cursor()
        cursor.execute('SELECT category, content FROM learned_info')
        results = cursor.fetchall()
        print(f"Retrieved {len(results)} items from database")
        for cat, content in results:
            print(f"- {cat}: {content}")
        print("===============================\n")
        return results