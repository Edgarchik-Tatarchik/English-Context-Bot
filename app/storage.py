from __future__ import annotations
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).resolve().parent.parent / "data.db"

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    with get_conn() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS saved_terms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            term TEXT NOT NULL,
            explanation TEXT NOT NULL,
            examples_json TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, term)
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS quiz_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            term TEXT NOT NULL,
            chosen INTEGER NOT NULL,
            correct INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

def save_term(user_id: int, term: str, explanation: str, examples: list[str]) -> bool:
    examples_json = json.dumps(examples, ensure_ascii=False)
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO saved_terms(user_id, term, explanation, examples_json) VALUES (?, ?, ?, ?)",
                (user_id, term, explanation, examples_json),
            )
        return True
    except sqlite3.IntegrityError:
        return False

def list_saved(user_id: int, limit: int = 20) -> list[str]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT term FROM saved_terms WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [r["term"] for r in rows]

@dataclass
class SavedItem:
    term: str
    explanation: str
    examples: list[str]

def get_saved_item(user_id: int, term: str) -> Optional[SavedItem]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT term, explanation, examples_json FROM saved_terms WHERE user_id=? AND term=?",
            (user_id, term),
        ).fetchone()
    if not row:
        return None
    return SavedItem(
        term=row["term"],
        explanation=row["explanation"],
        examples=json.loads(row["examples_json"]),
    )

def get_random_saved_term(user_id: int) -> Optional[str]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT term FROM saved_terms WHERE user_id=? ORDER BY RANDOM() LIMIT 1",
            (user_id,),
        ).fetchone()
    return row["term"] if row else None

def add_quiz_attempt(user_id: int, term: str, chosen: int, correct: int) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO quiz_attempts(user_id, term, chosen, correct) VALUES (?, ?, ?, ?)",
            (user_id, term, chosen, correct),
        )
