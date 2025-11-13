"""Run recommender models and persist their outputs to SQLite."""

from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List

from item_similarity import generate_item_similarity_recommendations
from random_model import DATA_DIR as DEFAULT_DATA_DIR
from random_model import generate_random_recommendations

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "data.db"

ModelFunction = Callable[[int, int | None, Path], Dict[str, List[Dict[str, float]]]]

RECOMMENDATIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_key TEXT NOT NULL,
    model TEXT NOT NULL,
    items TEXT NOT NULL,
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(target_key, model)
)
"""


@dataclass(frozen=True)
class ModelSpec:
    name: str
    runner: ModelFunction


MODEL_REGISTRY: Dict[str, ModelSpec] = {
    "random": ModelSpec(
        name="random",
        runner=lambda top_n, seed, data_dir: generate_random_recommendations(
            top_n=top_n,
            seed=seed,
            data_dir=data_dir,
        ),
    ),
    "item_similarity": ModelSpec(
        name="item_similarity",
        runner=lambda top_n, seed, data_dir: generate_item_similarity_recommendations(
            top_n=top_n,
            data_dir=data_dir,
            seed=seed,
        ),
    ),
}


def _ensure_database(db_path: Path) -> None:
    if not db_path.exists():
        raise FileNotFoundError(
            "Database not found. Run data/create_db.py to build it before generating recommendations: "
            f"{db_path}"
        )


def _serialize_items(items: Iterable[Dict[str, float]]) -> str:
    return json.dumps(list(items))


def _persist_recommendations(
    conn: sqlite3.Connection,
    model_name: str,
    recommendations: Dict[str, List[Dict[str, float]]],
) -> int:
    rows = [
        (target_key, model_name, _serialize_items(items))
        for target_key, items in recommendations.items()
    ]
    if not rows:
        return 0

    conn.executemany(
        """
        INSERT INTO recommendations (target_key, model, items)
        VALUES (?, ?, ?)
        ON CONFLICT(target_key, model)
        DO UPDATE SET
            items = excluded.items,
            generated_at = CURRENT_TIMESTAMP
        """,
        rows,
    )
    return len(rows)


def run_models(
    models: Iterable[str],
    *,
    top_n: int = 10,
    seed: int | None = None,
    data_dir: Path = DEFAULT_DATA_DIR,
    db_path: Path = DEFAULT_DB_PATH,
) -> Dict[str, int]:
    _ensure_database(db_path)

    resolved_data_dir = data_dir
    if not resolved_data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {resolved_data_dir}")

    results: Dict[str, int] = {}

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(RECOMMENDATIONS_TABLE_SQL)
        for model_name in models:
            spec = MODEL_REGISTRY.get(model_name)
            if spec is None:
                raise ValueError(f"Unknown model '{model_name}'. Available: {sorted(MODEL_REGISTRY)}")
            recommendations = spec.runner(top_n, seed, resolved_data_dir)
            count = _persist_recommendations(conn, model_name, recommendations)
            results[model_name] = count
        conn.commit()

    return results


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate and store recommendations")
    parser.add_argument(
        "--models",
        nargs="+",
        default=["random"],
        choices=sorted(MODEL_REGISTRY.keys()),
        help="One or more model names to run",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="Number of items to recommend per target (default: 10)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional random seed for deterministic output",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="Path to the data directory (default: recsys/data)",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DEFAULT_DB_PATH,
        help="Path to the SQLite database (default: api/data.db)",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    results = run_models(
        args.models,
        top_n=args.top_n,
        seed=args.seed,
        data_dir=args.data_dir,
        db_path=args.db_path,
    )
    for model_name, count in results.items():
        print(f"Stored {count} recommendation rows for model '{model_name}'")


if __name__ == "__main__":
    main()
