
import sqlite3

DATABASE_NAME = "production_control.db"

STATUSES = {"On Track", "At Risk", "Delayed", "Completed"}

def validate_project(name, manager, status, progress):
    if not isinstance(name, str) or not name.strip() or not isinstance(manager, str) or not manager.strip():
        raise ValueError("Project name and manager are required.")
    if not isinstance(status, str) or status not in STATUSES:
        raise ValueError("Select a supported project status.")
    if type(progress) is not int or not 0 <= progress <= 100:
        raise ValueError("Progress must be an integer between 0 and 100.")




# Connect to SQLite database
def get_connection():
    return sqlite3.connect(DATABASE_NAME)


# Initialize database and create projects table
def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                manager TEXT NOT NULL,
                status TEXT NOT NULL,
                progress INTEGER NOT NULL DEFAULT 0
                    CHECK(progress BETWEEN 0 AND 100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


# Create a new project
def add_project(name, manager, status, progress):
    validate_project(name, manager, status, progress)

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO projects (
                name,
                manager,
                status,
                progress
            )
            VALUES (?, ?, ?, ?)
            """,
            (name, manager, status, progress)
        )
        return cursor.lastrowid


# Retrieve all saved projects
def get_projects():
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT
                id,
                name,
                manager,
                status,
                progress
            FROM projects
            ORDER BY id DESC
        """)
        return cursor.fetchall()


# Update an existing project
def update_project(
    project_id,
    name,
    manager,
    status,
    progress
):
    validate_project(name, manager, status, progress)

    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE projects
            SET
                name = ?,
                manager = ?,
                status = ?,
                progress = ?
            WHERE id = ?
            """,
            (
                name,
                manager,
                status,
                progress,
                project_id
            )
        )
        return cursor.rowcount > 0


# Delete an existing project
def delete_project(project_id):
    with get_connection() as conn:
        cursor = conn.execute(
            """
            DELETE FROM projects
            WHERE id = ?
            """,
            (project_id,)
        )
        return cursor.rowcount > 0

