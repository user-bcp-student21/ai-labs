import sqlite3
from pathlib import Path

SELECT_TASKS_SQL = "SELECT id,title,description,status,owner,priority,created_at FROM tasks"
SELECT_BY_OWNER_SQL = SELECT_TASKS_SQL + " WHERE owner = ? ORDER BY id"
SELECT_BY_ID_SQL = SELECT_TASKS_SQL + " WHERE id = ?"
SELECT_STATUS_PRIORITY_SQL = "SELECT status,priority FROM tasks WHERE owner = ?"
INSERT_TASK_SQL = "INSERT INTO tasks(title,description,status,owner,priority,created_at) VALUES (?,?,?,?,?,datetime('now'))"


def find_by_owner(connection: sqlite3.Connection, owner: str) -> list[sqlite3.Row]:
    return connection.execute(SELECT_BY_OWNER_SQL, (owner,)).fetchall()


def find_by_id(connection: sqlite3.Connection, task_id: int) -> sqlite3.Row:
    return connection.execute(SELECT_BY_ID_SQL, (task_id,)).fetchone()


def status_priority_by_owner(connection: sqlite3.Connection, owner: str) -> list[sqlite3.Row]:
    return connection.execute(SELECT_STATUS_PRIORITY_SQL, (owner,)).fetchall()


def insert(connection: sqlite3.Connection, values: tuple[str, str, str, str, str]) -> int:
    cursor = connection.execute(INSERT_TASK_SQL, values)
    connection.commit()
    return int(cursor.lastrowid)
