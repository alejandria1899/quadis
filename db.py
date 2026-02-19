import os
import sqlite3
from datetime import datetime

DB_DIR = "data"
DB_PATH = os.path.join(DB_DIR, "app.db")


def get_conn():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS movement_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        created_at TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS movements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        movement_type_id INTEGER NOT NULL,
        movement_name TEXT NOT NULL,
        comment TEXT,
        ts TEXT NOT NULL,
        hhmmss TEXT NOT NULL,
        FOREIGN KEY(movement_type_id) REFERENCES movement_types(id)
    )
    """)

    conn.commit()
    conn.close()


def list_movement_types():
    conn = get_conn()
    rows = conn.execute("SELECT id, name FROM movement_types ORDER BY name ASC").fetchall()
    conn.close()
    return rows


def add_movement_type(name: str):
    name = (name or "").strip()
    if not name:
        return False, "Nombre vacío"

    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO movement_types(name, created_at) VALUES(?, ?)",
            (name, datetime.now().isoformat(timespec="seconds")),
        )
        conn.commit()
        return True, None
    except sqlite3.IntegrityError:
        return False, "Ese botón ya existe"
    finally:
        conn.close()


def delete_movement_type(movement_type_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM movement_types WHERE id = ?", (movement_type_id,))
    conn.commit()
    conn.close()


def add_movement(movement_type_id: int, movement_name: str, comment: str | None):
    now = datetime.now()
    ts = now.isoformat(timespec="seconds")
    hhmmss = now.strftime("%H:%M:%S")

    conn = get_conn()
    conn.execute(
        """
        INSERT INTO movements(movement_type_id, movement_name, comment, ts, hhmmss)
        VALUES(?, ?, ?, ?, ?)
        """,
        (movement_type_id, movement_name, (comment or "").strip(), ts, hhmmss),
    )
    conn.commit()
    conn.close()


def list_movements(limit: int = 200):
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT id, movement_name, comment, ts, hhmmss
        FROM movements
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    return rows


def list_movements_between(start_iso: str, end_iso: str):
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT id, movement_name, comment, ts, hhmmss
        FROM movements
        WHERE ts >= ? AND ts <= ?
        ORDER BY id ASC
        """,
        (start_iso, end_iso),
    ).fetchall()
    conn.close()
    return rows
