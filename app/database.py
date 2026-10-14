import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

DEFAULT_DB_PATH = os.getenv("DATABASE_PATH", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "students.db"))


def get_db_path() -> str:
    path = os.getenv("DATABASE_PATH", DEFAULT_DB_PATH)
    if path != ":memory:":
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    return path


@contextmanager
def get_db():
    conn = sqlite3.connect(get_db_path(), timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                dob TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                course TEXT,
                address TEXT,
                enrollment_date TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_students_course ON students(course);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_students_dob ON students(dob);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_students_email ON students(email);")


def insert_student(data: Dict[str, Any]) -> Dict[str, Any]:
    now = datetime.utcnow().isoformat()
    record = {
        "student_id": data["student_id"],
        "name": data["name"],
        "dob": data["dob"],
        "email": data["email"],
        "phone": data["phone"],
        "course": data.get("course"),
        "address": data.get("address"),
        "enrollment_date": data.get("enrollment_date"),
        "created_at": now,
        "updated_at": now
    }
    with get_db() as conn:
        conn.execute("""
            INSERT INTO students (
                student_id, name, dob, email, phone, course, address, enrollment_date, created_at, updated_at
            ) VALUES (
                :student_id, :name, :dob, :email, :phone, :course, :address, :enrollment_date, :created_at, :updated_at
            )
        """, record)
    return record


def get_student_by_id(student_id: str) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def list_students(
    course: Optional[str] = None,
    search: Optional[str] = None,
    born_after: Optional[str] = None,
    born_before: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    query = "SELECT * FROM students WHERE 1=1"
    params: List[Any] = []

    if course:
        query += " AND LOWER(course) = LOWER(?)"
        params.append(course.strip())

    if search:
        query += " AND (LOWER(name) LIKE LOWER(?) OR LOWER(email) LIKE LOWER(?))"
        wildcard = f"%{search.strip()}%"
        params.extend([wildcard, wildcard])

    if born_after:
        query += " AND dob >= ?"
        params.append(born_after.strip())

    if born_before:
        query += " AND dob <= ?"
        params.append(born_before.strip())

    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_db() as conn:
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def update_student(student_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    clean_updates = {k: v for k, v in updates.items() if v is not None}
    if not clean_updates:
        return get_student_by_id(student_id)

    clean_updates["updated_at"] = datetime.utcnow().isoformat()
    set_clause = ", ".join(f"{key} = :{key}" for key in clean_updates)
    clean_updates["student_id"] = student_id

    with get_db() as conn:
        cursor = conn.execute(
            f"UPDATE students SET {set_clause} WHERE student_id = :student_id",
            clean_updates
        )
        if cursor.rowcount == 0:
            return None

    return get_student_by_id(student_id)


def delete_student(student_id: str) -> bool:
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
        return cursor.rowcount > 0


def get_all_records_for_context() -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT student_id, name, dob, course, enrollment_date
            FROM students
            ORDER BY student_id ASC
        """)
        return [dict(row) for row in cursor.fetchall()]
