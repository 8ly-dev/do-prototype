import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

# --- Dataclasses ---

@dataclass
class User:
    id: Optional[int]
    email: str
    created_at: str

@dataclass
class Project:
    id: Optional[int]
    user_id: int
    name: str
    created_at: str

@dataclass
class Milestone:
    id: Optional[int]
    project_id: int
    name: str
    due_date: Optional[str]
    created_at: str

@dataclass
class Task:
    id: Optional[int]
    milestone_id: int
    title: str
    description: Optional[str]
    due_date: Optional[str]
    priority: int
    task_type: str
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
                email TEXT UNIQUE NOT NULL,
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
            CREATE TABLE IF NOT EXISTS milestones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                due_date TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                milestone_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                due_date TEXT,
                priority INTEGER NOT NULL,
                task_type TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(milestone_id) REFERENCES milestones(id)
            )
        ''')
        self.conn.commit()

    # --- User Methods ---

    def insert_user(self, email: str) -> int:
        now = datetime.utcnow().isoformat()
        c = self.conn.cursor()
        c.execute('INSERT INTO users (email, created_at) VALUES (?, ?)', (email, now))
        self.conn.commit()
        return c.lastrowid

    def get_user_by_email(self, email: str) -> Optional[User]:
        c = self.conn.cursor()
        c.execute('SELECT * FROM users WHERE email = ?', (email,))
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

    def get_projects_by_user(self, user_id: int) -> List[Project]:
        c = self.conn.cursor()
        c.execute('SELECT * FROM projects WHERE user_id = ?', (user_id,))
        return [Project(**row) for row in c.fetchall()]

    # --- Milestone Methods ---

    def insert_milestone(self, project_id: int, name: str, due_date: Optional[str]) -> int:
        now = datetime.utcnow().isoformat()
        c = self.conn.cursor()
        c.execute('INSERT INTO milestones (project_id, name, due_date, created_at) VALUES (?, ?, ?, ?)',
                  (project_id, name, due_date, now))
        self.conn.commit()
        return c.lastrowid

    def get_milestones_by_project(self, project_id: int) -> List[Milestone]:
        c = self.conn.cursor()
        c.execute('SELECT * FROM milestones WHERE project_id = ?', (project_id,))
        return [Milestone(**row) for row in c.fetchall()]

    # --- Task Methods ---

    def insert_task(self, milestone_id: int, title: str, description: Optional[str], due_date: Optional[str], priority: int, task_type: str) -> int:
        now = datetime.utcnow().isoformat()
        c = self.conn.cursor()
        c.execute('''
            INSERT INTO tasks (milestone_id, title, description, due_date, priority, task_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (milestone_id, title, description, due_date, priority, task_type, now))
        self.conn.commit()
        return c.lastrowid

    def get_tasks_by_milestone(self, milestone_id: int) -> List[Task]:
        c = self.conn.cursor()
        c.execute('SELECT * FROM tasks WHERE milestone_id = ?', (milestone_id,))
        return [Task(**row) for row in c.fetchall()]

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

    def update_milestone(self, milestone_id: int, **updates):
        fields = []
        values = []
        for k, v in updates.items():
            fields.append(f"{k} = ?")
            values.append(v)
        values.append(milestone_id)
        sql = f"UPDATE milestones SET {', '.join(fields)} WHERE id = ?"
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
        c.execute('DELETE FROM projects WHERE id = ?', (project_id,))
        self.conn.commit()

    def get_users_top_task(self, user_id: int) -> Optional[Task]:
        """
        Get the highest priority task for a user across all their projects and milestones.
        Returns None if the user has no tasks.
        """
        c = self.conn.cursor()
        c.execute('''
            SELECT t.* FROM tasks t
            JOIN milestones m ON t.milestone_id = m.id
            JOIN projects p ON m.project_id = p.id
            WHERE p.user_id = ?
            ORDER BY t.priority DESC
            LIMIT 1
        ''', (user_id,))
        row = c.fetchone()
        if row:
            return Task(**row)
        return None
