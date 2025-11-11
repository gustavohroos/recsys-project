"""Utility to build a SQLite database from the raw CSV exports."""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path
from typing import Callable, Iterable, Tuple

DB_PATH = Path(__file__).resolve().parent / "data.db"
DATA_DIR = Path(__file__).resolve().parent


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed if trimmed else None


def _to_int(value: str | None) -> int | None:
    cleaned = _clean(value)
    return int(cleaned) if cleaned is not None else None


def _normalize_row(row: dict[str, str | None]) -> dict[str, str | None]:
    return {key.strip(): _clean(val) for key, val in row.items() if key}


def create_tables(conn: sqlite3.Connection) -> None:
    """Create the tables in the database."""

    statements = (
        """
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            url TEXT,
            description TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            gender INTEGER,
            age_range TEXT,
            married INTEGER
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            rating INTEGER,
            app INTEGER,
            data INTEGER,
            ease INTEGER,
            class TEXT,
            semester TEXT,
            lockdown TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS group_members (
            group_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            PRIMARY KEY (group_id, user_id),
            FOREIGN KEY (group_id) REFERENCES groups(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS group_sizes (
            group_id INTEGER PRIMARY KEY,
            size INTEGER NOT NULL,
            FOREIGN KEY (group_id) REFERENCES groups(id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS group_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            rating INTEGER,
            app INTEGER,
            data INTEGER,
            ease INTEGER,
            class TEXT,
            semester TEXT,
            lockdown TEXT,
            FOREIGN KEY (group_id) REFERENCES groups(id),
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
        """,
    )

    for statement in statements:
        conn.execute(statement)


def load_items(conn: sqlite3.Connection, csv_path: Path) -> None:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for raw_row in reader:
            row = _normalize_row(raw_row)
            rows.append(
                (
                    _to_int(row.get("Item")),
                    row.get("Title"),
                    row.get("URL"),
                    row.get("Descriptions"),
                )
            )
    conn.executemany(
        "INSERT OR REPLACE INTO items (id, title, url, description) VALUES (?, ?, ?, ?)",
        rows,
    )


def load_users(conn: sqlite3.Connection, csv_path: Path) -> None:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for raw_row in reader:
            row = _normalize_row(raw_row)
            rows.append(
                (
                    _to_int(row.get("UserID")),
                    _to_int(row.get("Gender")),
                    row.get("Age"),
                    _to_int(row.get("Married")),
                )
            )
    conn.executemany(
        "INSERT OR REPLACE INTO users (id, gender, age_range, married) VALUES (?, ?, ?, ?)",
        rows,
    )


def load_ratings(conn: sqlite3.Connection, csv_path: Path) -> None:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for raw_row in reader:
            row = _normalize_row(raw_row)
            rows.append(
                (
                    _to_int(row.get("UserID")),
                    _to_int(row.get("Item")),
                    _to_int(row.get("Rating")),
                    _to_int(row.get("App")),
                    _to_int(row.get("Data")),
                    _to_int(row.get("Ease")),
                    row.get("Class"),
                    row.get("Semester"),
                    row.get("Lockdown"),
                )
            )
    conn.executemany(
        """
        INSERT INTO ratings (
            user_id, item_id, rating, app, data, ease, class, semester, lockdown
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


def load_group_members(conn: sqlite3.Connection, csv_path: Path) -> None:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        member_rows = set()
        group_rows = set()
        for raw_row in reader:
            row = _normalize_row(raw_row)
            group_id = _to_int(row.get("GroupID"))
            user_id = _to_int(row.get("UserID"))
            if group_id is None or user_id is None:
                continue
            group_rows.add((group_id,))
            member_rows.add((group_id, user_id))

    if group_rows:
        conn.executemany(
            "INSERT OR IGNORE INTO groups (id) VALUES (?)",
            list(group_rows),
        )

    if member_rows:
        conn.executemany(
            "INSERT OR IGNORE INTO group_members (group_id, user_id) VALUES (?, ?)",
            list(member_rows),
        )


def load_group_sizes(conn: sqlite3.Connection, csv_path: Path) -> None:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        group_rows = set()
        size_rows = []
        for raw_row in reader:
            row = _normalize_row(raw_row)
            group_id = _to_int(row.get("GroupID"))
            size = _to_int(row.get("Size"))
            if group_id is None:
                continue
            group_rows.add((group_id,))
            if size is not None:
                size_rows.append((group_id, size))

    if group_rows:
        conn.executemany(
            "INSERT OR IGNORE INTO groups (id) VALUES (?)",
            list(group_rows),
        )

    if size_rows:
        conn.executemany(
            "INSERT OR REPLACE INTO group_sizes (group_id, size) VALUES (?, ?)",
            size_rows,
        )


def load_group_ratings(conn: sqlite3.Connection, csv_path: Path) -> None:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        group_rows = set()
        for raw_row in reader:
            row = _normalize_row(raw_row)
            group_id = _to_int(row.get("GroupID"))
            item_id = _to_int(row.get("Item"))
            if group_id is None or item_id is None:
                continue
            group_rows.add((group_id,))
            rows.append(
                (
                    group_id,
                    item_id,
                    _to_int(row.get("Rating")),
                    _to_int(row.get("App")),
                    _to_int(row.get("Data")),
                    _to_int(row.get("Ease")),
                    row.get("Class"),
                    row.get("Semester"),
                    row.get("Lockdown"),
                )
            )
    if group_rows:
        conn.executemany(
            "INSERT OR IGNORE INTO groups (id) VALUES (?)",
            list(group_rows),
        )

    if rows:
        conn.executemany(
            """
            INSERT INTO group_ratings (
                group_id, item_id, rating, app, data, ease, class, semester, lockdown
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )


def create_database(db_path: Path = DB_PATH, data_dir: Path = DATA_DIR) -> Path:
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        create_tables(conn)
        loaders: Iterable[Tuple[Callable[[sqlite3.Connection, Path], None], str]] = (
            (load_items, "items.csv"),
            (load_users, "users.csv"),
            (load_ratings, "ratings.csv"),
            (load_group_sizes, "group_size.csv"),
            (load_group_members, "group.csv"),
            (load_group_ratings, "group_ratings.csv"),
        )
        for loader, filename in loaders:
            loader(conn, data_dir / filename)
        conn.commit()

    return db_path


if __name__ == "__main__":
    created_path = create_database()
    print(f"Database created at {created_path}")
