import sqlite3
from pathlib import Path

TASKS_SCHEMA_SQL = (
    "CREATE TABLE IF NOT EXISTS tasks ("
    "id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT NOT NULL, "
    "status TEXT NOT NULL, owner TEXT NOT NULL, priority TEXT NOT NULL, created_at TEXT NOT NULL)"
)
COUNT_TASKS_SQL = "SELECT COUNT(*) AS total FROM tasks"
INSERT_SEED_SQL = "INSERT INTO tasks(title,description,status,owner,priority,created_at) VALUES (?,?,?,?,?,datetime('now'))"

SEED_TASKS = (
    ("Refactor login", "Separar responsabilidades en frontend", "TODO", "student", "HIGH"),
    ("Review API", "Revisar seguridad de endpoints", "IN_PROGRESS", "student", "MEDIUM"),
    ("Trainer notes", "Preparar retrospectiva", "TODO", "trainer", "LOW"),
)


def open_database(db_path: str) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute(TASKS_SCHEMA_SQL)
    seed_if_empty(connection)
    return connection


def seed_if_empty(connection: sqlite3.Connection) -> None:
    if connection.execute(COUNT_TASKS_SQL).fetchone()["total"] == 0:
        connection.executemany(INSERT_SEED_SQL, SEED_TASKS)
        connection.commit()
