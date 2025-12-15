"""Content-based recommender using category preferences."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict, List

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "data.db"


def _get_item_category_scores(db_path: Path = DB_PATH) -> Dict[int, Dict[str, float]]:
    """Get category scores for each item.

    Returns:
        Dictionary mapping item_id to category scores.
    """
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("""
            SELECT item_id, category_id, is_primary
            FROM item_categories
        """)

        item_categories: Dict[int, Dict[str, float]] = {}
        for item_id, category_id, is_primary in cursor.fetchall():
            if item_id not in item_categories:
                item_categories[item_id] = {}
            # Primary category gets higher weight
            score = 1.0 if is_primary else 0.5
            item_categories[item_id][category_id] = score

        return item_categories


def _get_all_categories(db_path: Path = DB_PATH) -> List[str]:
    """Get all category IDs."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("SELECT id FROM categories ORDER BY id")
        return [row[0] for row in cursor.fetchall()]


def _get_all_item_ids(db_path: Path = DB_PATH) -> List[int]:
    """Get all item IDs."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("SELECT id FROM items ORDER BY id")
        return [row[0] for row in cursor.fetchall()]


def compute_preference_based_recommendations(
    preferred_categories: List[str],
    top_n: int = 10,
    db_path: Path = DB_PATH,
) -> List[Dict[str, float]]:
    """Compute recommendations based on category preferences.

    Args:
        preferred_categories: List of category IDs the user prefers.
        top_n: Number of recommendations to return.
        db_path: Path to the database.

    Returns:
        List of item recommendations with scores.
    """
    if not preferred_categories:
        return []

    # Get item category scores
    item_categories = _get_item_category_scores(db_path)
    all_items = _get_all_item_ids(db_path)

    # Convert preferences to weights
    preference_weights = {cat: 1.0 for cat in preferred_categories}

    # Score each item
    item_scores: List[tuple] = []

    for item_id in all_items:
        if item_id not in item_categories:
            continue

        # Calculate score based on overlap with preferred categories
        score = 0.0
        item_cats = item_categories[item_id]

        for category_id, cat_weight in item_cats.items():
            if category_id in preference_weights:
                score += cat_weight * preference_weights[category_id]

        if score > 0:
            item_scores.append((item_id, score))

    # Normalize scores
    if item_scores:
        max_score = max(s[1] for s in item_scores)
        if max_score > 0:
            item_scores = [(item_id, score / max_score) for item_id, score in item_scores]

    # Sort by score descending
    item_scores.sort(key=lambda x: x[1], reverse=True)

    return [
        {"item_id": item_id, "score": round(float(score), 6)}
        for item_id, score in item_scores[:top_n]
    ]


def generate_preference_recommendations(
    top_n: int = 10,
    seed: int | None = None,
    data_dir: Path = DATA_DIR,
    preferred_categories: List[str] | None = None,
) -> Dict[str, List[Dict[str, float]]]:
    """Generate recommendations based on preferences for all users.

    This is a wrapper for compatibility with the model registry.
    For real use, call compute_preference_based_recommendations directly.

    Args:
        top_n: Number of recommendations per target.
        seed: Random seed (unused).
        data_dir: Path to data directory.
        preferred_categories: Categories to use for recommendations.

    Returns:
        Dictionary with preference-based recommendations.
    """
    del seed  # Unused
    db_path = data_dir / "data.db"

    # If no preferences provided, return empty
    if not preferred_categories:
        return {}

    # Generate recommendations for the given preferences
    recs = compute_preference_based_recommendations(
        preferred_categories=preferred_categories,
        top_n=top_n,
        db_path=db_path,
    )

    # Return with a special key for preference-based recommendations
    pref_key = "preferences#" + ",".join(sorted(preferred_categories))
    return {pref_key: recs}


if __name__ == "__main__":
    # Test with some preferences
    test_preferences = ["entertainment", "sports"]
    print(f"Testing recommendations for preferences: {test_preferences}")

    recs = compute_preference_based_recommendations(test_preferences, top_n=10)
    print("\nTop 10 recommendations:")
    for rec in recs:
        print(f"  Item {rec['item_id']}: {rec['score']:.4f}")
