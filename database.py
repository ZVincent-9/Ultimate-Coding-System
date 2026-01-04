import sqlite3
import os
from pathlib import Path

class Database:
    def __init__(self):
        # Use APPDATA for reliable, non-synced storage
        appdata = os.getenv('APPDATA')
        if not appdata:
            raise RuntimeError("APPDATA environment variable not found!")
        
        db_dir = Path(appdata) / "UltimateCodingSystem"
        db_dir.mkdir(parents=True, exist_ok=True)  # Safe creation
        
        db_path = db_dir / "user.db"
        self.conn = sqlite3.connect(db_path)
        print(f"Database stored at: {db_path}")  # For debugging
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS skills (
                user_id INTEGER,
                skill_name TEXT,
                level INTEGER DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        self.conn.commit()

    def create_user(self, name):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO users (name) VALUES (?)", (name,))
        user_id = cursor.lastrowid
        self.conn.commit()
        
        skills_list = [
            "Python Syntax", "Data Structures", "Algorithms", "Debugging",
            "System Design", "Problem Solving", "Version Control",
            "Testing and QA", "Performance Optimization", "Code Readability / Maintenance"
        ]
        for skill in skills_list:
            cursor.execute("INSERT INTO skills (user_id, skill_name, level) VALUES (?, ?, 0)", (user_id, skill))
        self.conn.commit()
        return user_id

    def get_skills(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT skill_name, level FROM skills WHERE user_id = ?", (user_id,))
        return cursor.fetchall()