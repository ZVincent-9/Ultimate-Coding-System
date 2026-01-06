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
        # Existing users and skills tables...

        # New: Projects table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY,
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
        self._seed_projects()  # Add starter projects

    def _seed_projects(self):
        """Seed some beginner-to-advanced projects."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM projects")
        if cursor.fetchone()[0] > 0:
            return  # Already seeded

        starter_projects = [
            ("Hello World CLI", "Build a command-line app that greets the user and accepts input.", 10, 0, 0, 5, 0, 10, 0, 0, 0, 15),
            ("Todo List App", "Create a console-based todo list with add/remove/view.", 20, 30, 10, 20, 0, 40, 0, 10, 5, 30),
            ("Binary Search Implementation", "Implement and test binary search on sorted lists.", 15, 20, 60, 30, 0, 50, 0, 20, 10, 25),
            ("Simple REST API with Flask", "Build a Flask API with CRUD endpoints.", 40, 40, 20, 40, 30, 50, 10, 30, 20, 40),
            ("Scalable Chat Server", "Design a multi-client chat server with threading.", 50, 50, 40, 60, 70, 60, 20, 40, 50, 50),
        ]
        cursor.executemany('''
            INSERT INTO projects (title, description, difficulty_python_syntax, difficulty_data_structures,
            difficulty_algorithms, difficulty_debugging, difficulty_system_design, difficulty_problem_solving,
            difficulty_version_control, difficulty_testing_qa, difficulty_performance_optimization,
            difficulty_code_readability)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', starter_projects)
        self.conn.commit()

    def get_all_projects(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, title, description FROM projects")
        return cursor.fetchall()

    def update_skill_level(self, user_id, skill_name, new_level):
        """Cap at 100."""
        new_level = min(100, max(0, new_level))
        cursor = self.conn.cursor()
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