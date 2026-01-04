import sys
import os
import subprocess
import tempfile
from pathlib import Path  # For safe paths
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit, QLabel, QFileDialog, QHBoxLayout)
from PyQt5.QtCore import QProcess
from database import Database

class IDEWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ultimate Coding System")
        self.setGeometry(100, 100, 1000, 700)  # Bigger for split-view prep

        # Instance vars for profile/AI
        self.db = None
        self.user_id = None
        self.user_name = "User"
        self.current_file = None  # For save/load tracking

        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Code Editor (enhanced placeholder)
        self.code_editor = QTextEdit()
        self.code_editor.setPlaceholderText("Write your Python code here...\nTip: Try print('Hello, Ultimate Coding System!')")
        layout.addWidget(self.code_editor)

        # Buttons Row
        buttons_layout = self._create_buttons_row()
        layout.addLayout(buttons_layout)

        # Output Console
        self.output_label = QLabel("Output will appear here.\nStatus: Ready.")
        self.output_label.setStyleSheet("font-family: monospace; padding: 10px; background: #f0f0f0;")
        layout.addWidget(self.output_label)

        # Profile Section (Safer version - handles OneDrive/permissions)
        self._setup_profile(layout)

    def _create_buttons_row(self):
        """Helper: Row of buttons (Save, Load, Run, Refresh) - Good for Code Readability."""
        buttons_layout = QHBoxLayout()

        # Save Button
        save_btn = QPushButton("Save File")
        save_btn.clicked.connect(self.save_file)
        buttons_layout.addWidget(save_btn)

        # Load Button
        load_btn = QPushButton("Load File")
        load_btn.clicked.connect(self.load_file)
        buttons_layout.addWidget(load_btn)

        # Run Button (Safer subprocess version)
        run_btn = QPushButton("Run Code")
        run_btn.clicked.connect(self.run_code)
        buttons_layout.addWidget(run_btn)

        # Refresh Profile Button (Your mini-project!)
        refresh_btn = QPushButton("Refresh Profile")
        refresh_btn.clicked.connect(self.refresh_profile)
        buttons_layout.addWidget(refresh_btn)

        buttons_layout.addStretch()  # Pushes buttons left
        return buttons_layout

    def _setup_profile(self, layout):
        """Safe profile setup with full error handling."""
        try:
            self.db = Database()
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]

            if user_count == 0:
                self.user_id = self.db.create_user("Default User")
                self.user_name = "Default User"
                print("Created new user: Default User (ID: {})".format(self.user_id))
            else:
                cursor.execute("SELECT id, name FROM users LIMIT 1")
                user_row = cursor.fetchone()
                self.user_id = user_row[0]
                self.user_name = user_row[1]
                print(f"Loaded user: {self.user_name} (ID: {self.user_id})")

            self.profile_label = self._render_skills_label()
            layout.addWidget(self.profile_label)

        except PermissionError as e:
            error_msg = f"Permission Error: {str(e)}\n\nFix: Move project OUT of OneDrive (e.g., C:\\Dev\\).\nOr run as admin."
            self._show_error_label(layout, error_msg)
        except Exception as e:
            error_msg = f"Setup Error: {str(e)}\nCheck terminal for details."
            self._show_error_label(layout, error_msg)
            print("Full traceback:")
            import traceback
            traceback.print_exc()

    def _render_skills_label(self):
        """Render skills with nice formatting."""
        skills = self.db.get_skills(self.user_id)
        skills_text = "Skills (0-100):\n" + "\n".join([f"  • {name}: {level}/100" for name, level in skills])
        label = QLabel(f"👋 Welcome, {self.user_name}!\n\n{skills_text}")
        label.setStyleSheet("""
            font-size: 12px; 
            padding: 15px; 
            background: linear-gradient(to bottom, #e3f2fd, #bbdefb);
            border: 1px solid #2196f3;
            border-radius: 8px;
        """)
        return label

    def _show_error_label(self, layout, msg):
        """Helper for error display."""
        error_label = QLabel(msg)
        error_label.setStyleSheet("color: red; font-weight: bold; padding: 15px; background: #ffebee;")
        layout.addWidget(error_label)

    def refresh_profile(self):
        """Mini-project: Refresh skills display."""
        if self.db and self.user_id:
            self.profile_label.setText(self._render_skills_label().text())
            self.output_label.setText("Profile refreshed! Skills unchanged until AI updates.")
        else:
            self.output_label.setText("No profile loaded.")

    # File Operations (Phase 1 Polish: Save/Load)
    def save_file(self):
        if self.current_file:
            with open(self.current_file, 'w') as f:
                f.write(self.code_editor.toPlainText())
            self.output_label.setText(f"Saved: {self.current_file}")
        else:
            self.save_file_as()

    def save_file_as(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Python Files (*.py);;All Files (*)")
        if file_path:
            self.current_file = file_path
            self.save_file()

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load File", "", "Python Files (*.py);;All Files (*)")
        if file_path:
            with open(file_path, 'r') as f:
                self.code_editor.setText(f.read())
            self.current_file = file_path
            self.output_label.setText(f"Loaded: {file_path}")

    # Safer Run Code (Replaces exec - Security + Real Output)
    def run_code(self):
        code = self.code_editor.toPlainText().strip()
        if not code:
            self.output_label.setText("No code to run.")
            return

        try:
            # Write code to temp file (secure, captures output)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(code)
                temp_path = temp_file.name

            # Run with subprocess (captures stdout/stderr)
            process = subprocess.Popen(
                [sys.executable, temp_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.path.dirname(temp_path)  # Good practice
            )
            stdout, stderr = process.communicate()

            os.unlink(temp_path)  # Clean up

            if process.returncode == 0:
                output = stdout or "Code ran successfully! (No output)"
                self.output_label.setText(f"✅ SUCCESS\n{output}")
            else:
                self.output_label.setText(f"❌ ERROR (Code {process.returncode})\n{stderr or stdout}")
        except Exception as e:
            self.output_label.setText(f"Runtime Error: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = IDEWindow()
    window.show()
    sys.exit(app.exec_())