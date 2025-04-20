import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional, List


type TaskType = Literal[
    "todo",  # Basic check box task, created by the user or agent
    "email",  # Task to draft and send an email, only created by the agent
    # "reminder",  # Task to create a reminder, only created by the agent
    "calendar",  # Task to create a calendar event, only created by the agent
    "create_task",  # Task to create a new task, only created by the agent
]

# --- Singleton DB Instance ---
_db_instance = None

def get_db(db_path="flowstate.db") -> 'FlowstateDB':
    """
    Returns a singleton instance of FlowstateDB.
    This ensures we reuse the same database connection throughout the application.
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = FlowstateDB(db_path)
    return _db_instance

# --- Dataclasses ---

@dataclass
class User:
    id: Optional[int]
    username: str
    created_at: str

@dataclass
class Project:
    id: Optional[int]
    user_id: int
    name: str
    created_at: str

@dataclass
class Task:
    id: Optional[int]
    project_id: int
    title: str
    description: Optional[str]
    due_date: Optional[str]
    priority: int
    task_type: TaskType
    created_at: str

# --- Database Layer ---

class FlowstateDB:
    def __init__(self, db_path="flowstate.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        c = self.conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                due_date TEXT,
                priority INTEGER NOT NULL,
                task_type TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            )
        ''')
        self.conn.commit()

    # --- User Methods ---

    def insert_user(self, username: str) -> int:
        now = datetime.utcnow().isoformat()
        c = self.conn.cursor()
        c.execute('INSERT INTO users (username, created_at) VALUES (?, ?)', (username, now))
        self.conn.commit()
        return c.lastrowid

    def get_user_by_username(self, username: str) -> Optional[User]:
        c = self.conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        row = c.fetchone()
        if row:
            return User(**row)
        return None

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        c = self.conn.cursor()
        c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = c.fetchone()
        if row:
            return User(**row)
        return None

    # --- Project Methods ---

    def insert_project(self, user_id: int, name: str) -> int:
        now = datetime.utcnow().isoformat()
        c = self.conn.cursor()
        c.execute('INSERT INTO projects (user_id, name, created_at) VALUES (?, ?, ?)', (user_id, name, now))
        self.conn.commit()
        return c.lastrowid

    def get_project(self, project_id: int) -> Optional[Project]:
        c = self.conn.cursor()
        c.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
        row = c.fetchone()
        if row:
            return Project(**row)
        return None

    def get_projects_by_user(self, user_id: int) -> List[Project]:
        c = self.conn.cursor()
        c.execute('SELECT * FROM projects WHERE user_id = ?', (user_id,))
        return [Project(**row) for row in c.fetchall()]

    # --- Task Methods ---

    def insert_task(self, project_id: int, title: str, description: Optional[str], due_date: Optional[str], priority: int, task_type: str) -> int:
        now = datetime.utcnow().isoformat()
        c = self.conn.cursor()
        c.execute('''
            INSERT INTO tasks (project_id, title, description, due_date, priority, task_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (project_id, title, description, due_date, priority, task_type, now))
        self.conn.commit()
        return c.lastrowid

    def get_tasks_by_project(self, project_id: int) -> List[Task]:
        c = self.conn.cursor()
        c.execute('SELECT * FROM tasks WHERE project_id = ?', (project_id,))
        return [Task(**row) for row in c.fetchall()]

    def get_task(self, task_id: int) -> Optional[Task]:
        c = self.conn.cursor()
        c.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
        row = c.fetchone()
        if row:
            return Task(**row)
        return None

    # --- Update Methods (Examples) ---

    def update_task(self, task_id: int, **updates):
        fields = []
        values = []
        for k, v in updates.items():
            fields.append(f"{k} = ?")
            values.append(v)
        values.append(task_id)
        sql = f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?"
        c = self.conn.cursor()
        c.execute(sql, values)
        self.conn.commit()


    # --- Delete Methods (Examples) ---

    def delete_task(self, task_id: int):
        c = self.conn.cursor()
        c.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        self.conn.commit()

    def delete_project(self, project_id: int):
        c = self.conn.cursor()
        c.execute('DELETE FROM tasks WHERE project_id = ?', (project_id,))
        c.execute('DELETE FROM projects WHERE id = ?', (project_id,))
        self.conn.commit()

    def get_users_top_task(self, user_id: int) -> Optional[Task]:
        """
        Get the highest priority task for a user across all their projects.
        Returns None if the user has no tasks.
        """
        c = self.conn.cursor()
        c.execute('''
            SELECT t.* FROM tasks t
            JOIN projects p ON t.project_id = p.id
            WHERE p.user_id = ?
            ORDER BY t.priority DESC
            LIMIT 1
        ''', (user_id,))
        row = c.fetchone()
        if row:
            return Task(**row)
        return None
