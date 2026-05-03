from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import TYPE_CHECKING
import pandas as pd
from functions.categories import DEFAULT_CATEGORIES

if TYPE_CHECKING:
    from models.transaction import Transaction

DB_DIR = Path(__file__).resolve().parents[1] / "database"
DB_PATH = DB_DIR / "finances.db"


def get_connection() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def initialize_database() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_date TEXT NOT NULL,
                month TEXT NOT NULL,
                partner TEXT NOT NULL,
                transaction_type TEXT NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT,
                source TEXT,
                amount REAL NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS subcategories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                subcategory TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(category, subcategory)
            )
            """
        )
        existing_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(subcategories)").fetchall()
        }
        if "created_at" not in existing_columns:
            conn.execute("ALTER TABLE subcategories ADD COLUMN created_at TEXT")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        conn.commit()


def insert_transaction(transaction: "Transaction") -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO transactions (
                entry_date, month, partner, transaction_type, category,
                subcategory, source, amount, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                transaction.entry_date.isoformat(),
                transaction.month,
                transaction.partner,
                transaction.transaction_type.value,
                transaction.category,
                transaction.subcategory,
                transaction.source,
                float(transaction.amount or 0.0),
                transaction.notes,
            ),
        )
        conn.commit()


def read_transactions() -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql_query("SELECT * FROM transactions ORDER BY entry_date DESC, id DESC", conn)


def delete_transaction(transaction_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        conn.commit()


def add_subcategory(category: str, subcategory: str) -> None:
    category_value = (category or "").strip()
    subcategory_value = (subcategory or "").strip()
    if not category_value or not subcategory_value:
        return
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO subcategories (category, subcategory) VALUES (?, ?)",
            (category_value, subcategory_value),
        )
        conn.commit()


def get_subcategories(category: str) -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT subcategory
            FROM subcategories
            WHERE category = ?
            ORDER BY subcategory
            """,
            (category,),
        ).fetchall()
    return [row[0] for row in rows]


def ensure_default_subcategories() -> None:
    default_parent_by_subcategory = {
        subcategory: category
        for category, subcategories in DEFAULT_CATEGORIES.items()
        for subcategory in subcategories
    }
    with get_connection() as conn:
        for subcategory, category in default_parent_by_subcategory.items():
            conn.execute(
                """
                DELETE FROM subcategories
                WHERE subcategory = ?
                AND category != ?
                """,
                (subcategory, category),
            )
        conn.commit()

    for category, subcategories in DEFAULT_CATEGORIES.items():
        for subcategory in subcategories:
            add_subcategory(category, subcategory)


def read_subcategories() -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql_query("SELECT category, subcategory FROM subcategories ORDER BY category, subcategory", conn)


def get_setting(key: str, default: str | None = None) -> str | None:
    with get_connection() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row[0] if row else default


def set_setting(key: str, value: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        conn.commit()


def get_partner_names() -> tuple[str, str]:
    return (get_setting("partner_a_name", "Partner A") or "Partner A", get_setting("partner_b_name", "Partner B") or "Partner B")


def save_partner_names(partner_a: str, partner_b: str) -> None:
    set_setting("partner_a_name", partner_a.strip() or "Partner A")
    set_setting("partner_b_name", partner_b.strip() or "Partner B")
