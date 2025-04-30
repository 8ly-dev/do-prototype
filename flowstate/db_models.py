"""
Database models and utilities for the Flowstate application.

This module provides dataclasses for representing database entities,
a database access layer for interacting with the SQLite database,
and utility functions for getting a database instance.
"""

import sqlite3
from dataclasses import dataclass
from datetime import datetime, UTC
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
    """
    Represents a user in the system.

    Attributes:
        id: The unique identifier for the user
        username: The username of the user
        created_at: The timestamp when the user was created
    """
    id: Optional[int]
    username: str
    created_at: str

@dataclass
class Project:
    """
    Represents a project in the system.

    Attributes:
        id: The unique identifier for the project
        user_id: The ID of the user who owns the project
        name: The name of the project
        created_at: The timestamp when the project was created
    """
    id: Optional[int]
    user_id: int
    name: str
    created_at: str

@dataclass
class Task:
    """
    Represents a task in the system.

    Attributes:
        id: The unique identifier for the task
        project_id: The ID of the project that the task belongs to
        title: The title of the task
        description: Optional description of the task
        due_date: Optional due date for the task
        priority: The priority of the task (higher values indicate higher priority)
        task_type: The type of the task (todo, email, calendar, create_task)
        created_at: The timestamp when the task was created
    """
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
    """
    Database access layer for the Flowstate application.

    This class provides methods for interacting with the SQLite database,
    including creating, reading, updating, and deleting users, projects, and tasks.
    """
    def __init__(self, db_path="flowstate.db"):
        """
        Initialize the database connection and create tables if they don't exist.

        Args:
            db_path: The path to the SQLite database file
        """
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        """
        Create the database tables if they don't exist.

        This method creates the users, projects, and tasks tables
        with the appropriate schema and constraints.
        """
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
        """
        Insert a new user into the database.

        Args:
            username: The username of the new user

        Returns:
            The ID of the newly created user
        """
        now = datetime.utcnow().isoformat()
        c = self.conn.cursor()
        c.execute('INSERT INTO users (username, created_at) VALUES (?, ?)', (username, now))
        self.conn.commit()
        return c.lastrowid

    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get a user by their username.

        Args:
            username: The username to look up

        Returns:
            The User object if found, or None if not found
        """
        c = self.conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        row = c.fetchone()
        if row:
            return User(**row)
        return None

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get a user by their ID.

        Args:
            user_id: The ID of the user to look up

        Returns:
            The User object if found, or None if not found
        """
        c = self.conn.cursor()
        c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = c.fetchone()
        if row:
            return User(**row)
        return None

    # --- Project Methods ---

    def insert_project(self, user_id: int, name: str) -> int:
        """
        Insert a new project into the database.

        Args:
            user_id: The ID of the user who owns the project
            name: The name of the project

        Returns:
            The ID of the newly created project
        """
        now = datetime.now(UTC).isoformat()
        c = self.conn.cursor()
        c.execute('INSERT INTO projects (user_id, name, created_at) VALUES (?, ?, ?)', (user_id, name, now))
        self.conn.commit()
        return c.lastrowid

    def get_project(self, project_id: int) -> Optional[Project]:
        """
        Get a project by its ID.

        Args:
            project_id: The ID of the project to look up

        Returns:
            The Project object if found, or None if not found
        """
        c = self.conn.cursor()
        c.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
        row = c.fetchone()
        if row:
            return Project(**row)
        return None

    def get_projects_by_user(self, user_id: int) -> List[Project]:
        """
        Get all projects owned by a user.

        Args:
            user_id: The ID of the user

        Returns:
            A list of Project objects owned by the user
        """
        c = self.conn.cursor()
        c.execute('SELECT * FROM projects WHERE user_id = ?', (user_id,))
        return [Project(**row) for row in c.fetchall()]

    # --- Task Methods ---

    def insert_task(self, project_id: int, title: str, description: Optional[str], due_date: Optional[str], priority: int, task_type: str) -> int:
        """
        Insert a new task into the database.

        Args:
            project_id: The ID of the project that the task belongs to
            title: The title of the task
            description: Optional description of the task
            due_date: Optional due date for the task
            priority: The priority of the task (higher values indicate higher priority)
            task_type: The type of the task (todo, email, calendar, create_task)

        Returns:
            The ID of the newly created task
        """
        now = datetime.now(UTC).isoformat()
        due_date = datetime.fromisoformat(due_date).astimezone(UTC).isoformat() if due_date else None
        c = self.conn.cursor()
        c.execute('''
            INSERT INTO tasks (project_id, title, description, due_date, priority, task_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (project_id, title, description, due_date, priority, task_type, now))
        self.conn.commit()
        return c.lastrowid

    def get_tasks_by_project(self, project_id: int) -> List[Task]:
        """
        Get all tasks belonging to a project.

        Args:
            project_id: The ID of the project

        Returns:
            A list of Task objects belonging to the project
        """
        c = self.conn.cursor()
        c.execute('SELECT * FROM tasks WHERE project_id = ?', (project_id,))
        return [Task(**row) for row in c.fetchall()]

    def get_task(self, task_id: int) -> Optional[Task]:
        """
        Get a task by its ID.

        Args:
            task_id: The ID of the task to look up

        Returns:
            The Task object if found, or None if not found
        """
        c = self.conn.cursor()
        c.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
        row = c.fetchone()
        if row:
            return Task(**row)
        return None

    # --- Update Methods (Examples) ---

    def update_task(self, task_id: int, **updates):
        """
        Update a task with the specified fields.

        Args:
            task_id: The ID of the task to update
            **updates: Keyword arguments representing the fields to update and their new values
        """
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
        """
        Delete a task from the database.

        Args:
            task_id: The ID of the task to delete
        """
        c = self.conn.cursor()
        c.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        self.conn.commit()

    def delete_project(self, project_id: int):
        """
        Delete a project and all its tasks from the database.

        Args:
            project_id: The ID of the project to delete
        """
        c = self.conn.cursor()
        c.execute('DELETE FROM tasks WHERE project_id = ?', (project_id,))
        c.execute('DELETE FROM projects WHERE id = ?', (project_id,))
        self.conn.commit()

    def get_users_top_task(self, user_id: int) -> Optional[Task]:
        """
        Get the highest priority task for a user across all their projects.

        This method finds the task with the highest priority value across all
        projects owned by the specified user.

        Args:
            user_id: The ID of the user

        Returns:
            The highest priority Task object, or None if the user has no tasks
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
