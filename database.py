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
        # Existing users + skills tables...

        # New: Projects table with difficulty per skill (0-100)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                difficulty_python_syntax INTEGER DEFAULT 0,
                difficulty_data_structures INTEGER DEFAULT 0,
                difficulty_algorithms INTEGER DEFAULT 0,
                difficulty_debugging INTEGER DEFAULT 0,
                difficulty_system_design INTEGER DEFAULT 0,
                difficulty_problem_solving INTEGER DEFAULT 0,
                difficulty_version_control INTEGER DEFAULT 0,
                difficulty_testing_qa INTEGER DEFAULT 0,
                difficulty_performance_optimization INTEGER DEFAULT 0,
                difficulty_code_readability INTEGER DEFAULT 0
            )
        ''')
        self.conn.commit()
        self._seed_initial_projects()

    def _seed_initial_projects(self):
        """Add 5 starter projects (beginner → advanced)."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM projects")
        if cursor.fetchone()[0] > 0:
            return  # Already seeded

        projects = [
            ("Hello World Enhancements", "Build a CLI that greets, takes name/input, and handles errors gracefully.", 
             15, 5, 0, 10, 0, 15, 0, 5, 0, 20),
            ("Todo List with Persistence", "Console todo app that saves to JSON file. Add/remove/list.", 
             25, 35, 15, 25, 0, 45, 5, 15, 10, 35),
            ("Binary Search Tree", "Implement BST with insert/search/delete and unit tests.", 
             20, 45, 70, 35, 0, 60, 0, 40, 15, 30),
            ("Flask REST API", "Build a simple CRUD API for a resource (e.g., books) with routes and validation.", 
             45, 40, 25, 45, 30, 55, 10, 35, 20, 45),
            ("Multi-threaded Chat Server", "TCP server handling multiple clients with threading and clean architecture.", 
             55, 50, 40, 65, 75, 65, 20, 45, 55, 55),
        ]
        cursor.executemany('''
            INSERT INTO projects 
            (title, description, difficulty_python_syntax, difficulty_data_structures, difficulty_algorithms,
             difficulty_debugging, difficulty_system_design, difficulty_problem_solving, difficulty_version_control,
             difficulty_testing_qa, difficulty_performance_optimization, difficulty_code_readability)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', projects)
        self.conn.commit()

    def get_all_projects(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, title, description FROM projects ORDER BY id")
        return cursor.fetchall()

    def update_skill_level(self, user_id, skill_name, delta):
        """Add delta (+/-) to skill, capped 0-100."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT level FROM skills WHERE user_id = ? AND skill_name = ?", (user_id, skill_name))
        current = cursor.fetchone()[0]
        new_level = max(0, min(100, current + delta))
        cursor.execute("UPDATE skills SET level = ? WHERE user_id = ? AND skill_name = ?", (new_level, user_id, skill_name))
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