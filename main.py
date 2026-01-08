import sys
import os
import subprocess
import tempfile
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit, QLabel, QFileDialog, QHBoxLayout, QSplitter, QFrame)
from PyQt5.QtCore import Qt
from database import Database
from dotenv import load_dotenv

    
load_dotenv()  # Loads .env into os.environ

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("Groq not installed. Run: pip install groq")

class IDEWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ultimate Coding System")
        self.setGeometry(100, 100, 1200, 800)

        self.db = None
        self.user_id = None
        self.user_name = "User"
        self.current_file = None

        # Main horizontal splitter: Editor LEFT | Chat RIGHT
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # === LEFT: Code Editor Panel ===
        left_panel = QFrame()
        left_panel.setFrameShape(QFrame.StyledPanel)
        left_layout = QVBoxLayout(left_panel)

        self.code_editor = QTextEdit()
        self.code_editor.setPlaceholderText("Write your Python code here...\nAsk the AI tutor for help anytime →")
        left_layout.addWidget(self.code_editor)

        buttons_row = self._create_buttons_row()
        left_layout.addLayout(buttons_row)

        project_btn = QPushButton("Show Projects")
        project_btn.clicked.connect(self.show_projects)
        buttons_row.addWidget(project_btn)

        self.output_label = QLabel("Output will appear here.\nStatus: Ready.")
        self.output_label.setStyleSheet("font-family: monospace; padding: 10px; background: #1e1e1e; color: #d4d4d4;")
        self.output_label.setAlignment(Qt.AlignTop)
        left_layout.addWidget(self.output_label)

        # Profile display
        self._setup_profile(left_layout)

        splitter.addWidget(left_panel)

        # === RIGHT: AI Tutor Chat Panel ===
        right_panel = QFrame()
        right_panel.setFrameShape(QFrame.StyledPanel)
        right_layout = QVBoxLayout(right_panel)

        chat_title = QLabel("🧠 AI Tutor")
        chat_title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px; background: #2196f3; color: white;")
        chat_title.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(chat_title)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("background: #f8f9fa; font-family: monospace;")
        right_layout.addWidget(self.chat_display)

        input_layout = QHBoxLayout()
        self.chat_input = QTextEdit()
        self.chat_input.setFixedHeight(80)
        self.chat_input.setPlaceholderText("Ask about code, concepts, projects, or request feedback...")
        input_layout.addWidget(self.chat_input)

        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self.send_to_ai)
        send_btn.setFixedWidth(100)
        input_layout.addWidget(send_btn)

        right_layout.addLayout(input_layout)

        if not GROQ_AVAILABLE:
            self.chat_display.setPlainText("⚠️ Groq library not found.\nRun: pip install groq\nThen restart the app.")

        splitter.addWidget(right_panel)

        # Initial splitter ratio (60% editor, 40% chat)
        splitter.setSizes([700, 500])

        # Welcome message
        self._add_chat_message("assistant", "Hello! I'm your AI tutor. I can:\n• Review your code\n• Explain concepts\n• Suggest projects based on your skills\n• Help you level up from beginner to architect\n\nTry asking: 'Review my code' or 'Suggest a beginner project'")

    def _add_chat_message(self, role: str, content: str):
        """Helper to append formatted chat messages."""
        color = "#0d47a1" if role == "assistant" else "#2e7d32"
        prefix = "👤 You:" if role == "user" else "🧠 Tutor:"
        formatted = f"<p style='color:{color}; margin:5px;'><b>{prefix}</b><br>{content.replace('\n', '<br>')}</p><hr>"
        self.chat_display.append(formatted)

    def send_to_ai(self):
        user_message = self.chat_input.toPlainText().strip()
        if not user_message:
            return

        self._add_chat_message("user", user_message)
        self.chat_input.clear()

        if not GROQ_AVAILABLE:
            self._add_chat_message("assistant", "Error: Groq not available. Install with 'pip install groq'")
            return

        # Get current code for context
        current_code = self.code_editor.toPlainText()

        # Simple prompt (we'll enhance later)
        system_prompt = f"""
        You are an encouraging Python tutor guiding {self.user_name} from beginner to senior architect.
        Current skills (0-100): {dict(self.db.get_skills(self.user_id))}

        Guidelines:
        - Be specific, positive, and educational.
        - When reviewing code or answering questions, end your response with a JSON block for skill changes:
        {{"updates": {{"Skill Name": +delta or -delta, ...}}}}
        Example: {{"updates": {{"Python Syntax": +1, "Debugging": +3, "Code Readability / Maintenance": +2}}}}
        Only include skills that improved (positive delta) or need work (small negative if major issues).
        - When asked for projects or "suggest project", recommend 2-3 from this list that target weak skills (<50):
        {[(p[1], p[2]) for p in self.db.get_all_projects()]}
        - If user says "start project X", "working on Y", or "completed Z", update status and respond encouragingly.
        Example response: "Great! Marked 'Todo List' as started. Let's crush it!"
        Keep JSON on its own line at the end.
        """.strip()

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Current code:\n```python\n{current_code}\n```\n\nUser question: {user_message}"}
        ]

        self._add_chat_message("assistant", "Thinking...")

        try:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not set in .env or environment")

            client = Groq(api_key=api_key)  # ← This line was missing!

            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # Confirmed active Jan 2026
                messages=messages,
                temperature=0.7,
                max_tokens=1500  # Room for JSON
            )
            response = completion.choices[0].message.content

            # Parse skill updates (simple JSON search)
            import json
            import re
            json_match = re.search(r'\{.*"updates".*\}', response, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                    for skill, delta in data.get("updates", {}).items():
                        if skill in [row[0] for row in self.db.get_skills(self.user_id)]:
                            self.db.update_skill_level(self.user_id, skill, delta)
                    self.refresh_profile()  # Live update
                    response += "\n\n🎉 Your skills have been updated!"
                except Exception as e:
                    print("JSON parse error:", e)  # Debug silently

            # Simple project status detection (enhance later)
            lower_response = response.lower()
            if "completed" in lower_response or "finished" in lower_response:
                # Extract project title logic later; for now manual
                response += "\n\n🏆 Amazing work! +Extra skill boost for completion coming soon."

            # Remove "Thinking..." before final response
            self.chat_display.textCursor().deletePreviousChar()
            self._add_chat_message("assistant", response)

        except Exception as e:
            error_msg = f"API Error: {str(e)}\n\nTip: Check .env has GROQ_API_KEY and internet connection."
            self.chat_display.textCursor().deletePreviousChar()  # Remove "Thinking..."
            self._add_chat_message("assistant", error_msg)


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

    def show_projects(self):
        projects = self.db.get_user_projects(self.user_id)
        msg = "Your Project Curriculum:\n\n"
        for pid, title, desc, status, notes in projects:
            status_emoji = {"completed": "✅", "started": "🔄", "suggested": "➡️"}.get(status, "➡️")
            msg += f"{status_emoji} **{title}** ({status})\n{desc}\n"
            if notes:
                msg += f"   Notes: {notes}\n"
            msg += "\n"

        msg += "Ask me: 'Start the Todo List project' or 'I completed Binary Search Tree' to update status!"
        self._add_chat_message("assistant", msg)

    def browse_projects(self):
        projects = self.db.get_all_projects()
        proj_text = "Available Projects:\n\n" + "\n\n".join([f"{i+1}. {title}\n{desc}" for i, (_, title, desc) in enumerate(projects)])
        self._add_chat_message("assistant", f"Here are projects matched to your level:\n\n{proj_text}\n\nAsk me about any or say 'Assign me project X'!")

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