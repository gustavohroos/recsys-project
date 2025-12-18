"""Utility to export stored recommendations from SQLite to CSV.

Columns:
- target_type: user or item (derived from target_key)
- target_id: numeric id for the target
- model: recommendation model name
- generated_at: timestamp stored in the DB
- item_count: number of recommended items
- recommendations: JSON string of the items payload as stored in the table

Usage:
python export_recommendations.py --db-path ../data/data.db --output recommendations.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "data.db"


def _parse_target_key(target_key: str) -> Tuple[str, str]:
    """Split target_key like "user_id#1" into (target_type, target_id).

    Falls back to ("unknown", target_key) if the format is unexpected.
    """
    if "#" in target_key:
        prefix, suffix = target_key.split("#", 1)
        return prefix, suffix
    return "unknown", target_key


def _load_recommendations(db_path: Path) -> Iterable[Dict[str, Any]]:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT target_key, model, items, generated_at
            FROM recommendations
            ORDER BY model, target_key
            """
        ).fetchall()

    for row in rows:
        target_type, target_id = _parse_target_key(row["target_key"])
        items_raw = row["items"]
        try:
            items = json.loads(items_raw)
        except json.JSONDecodeError:
            items = []
        item_count = len(items) if isinstance(items, list) else 0
        yield {
            "target_type": target_type,
            "target_id": target_id,
            "model": row["model"],
            "generated_at": row["generated_at"],
            "item_count": item_count,
            "recommendations": items_raw,
        }


def export_to_csv(db_path: Path, output_path: Path) -> Path:
    rows = list(_load_recommendations(db_path))
    if not rows:
        raise SystemExit(f"No recommendations found in {db_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "target_type",
                "target_id",
                "model",
                "generated_at",
                "item_count",
                "recommendations",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    return output_path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export recommendations to CSV")
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"Path to SQLite DB (default: {DEFAULT_DB_PATH})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("recommendations.csv"),
        help="Output CSV path (default: recommendations.csv)",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    exported = export_to_csv(args.db_path, args.output)
    print(f"Exported recommendations to {exported}")


if __name__ == "__main__":
    main()
