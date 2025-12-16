"""Feedback-based recommendation adjustments.

This module provides functions to:
1. Store user feedback (likes/dislikes)
2. Adjust recommendation scores based on feedback
3. Filter out disliked items
4. Boost liked items and similar items
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "data.db"

# Score boost factor for liked items
LIKE_BOOST_FACTOR = 1.3
# Score boost factor for items similar to liked items
SIMILAR_ITEM_BOOST_FACTOR = 1.15
# Number of similar items to boost
SIMILAR_ITEMS_TO_BOOST = 5


def _get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Get a database connection with row factory."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_feedback_table(db_path: Path = DB_PATH) -> None:
    """Ensure the user_feedback table exists."""
    conn = _get_connection(db_path)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                feedback_type TEXT NOT NULL CHECK(feedback_type IN ('like', 'dislike')),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (item_id) REFERENCES items(id),
                UNIQUE(user_id, item_id)
            )
        """)
        conn.commit()
    finally:
        conn.close()


def save_feedback(
    user_id: int,
    item_id: int,
    feedback_type: Optional[str],
    db_path: Path = DB_PATH,
) -> Dict[str, Any]:
    """
    Save or update user feedback for an item.

    Args:
        user_id: The user's ID
        item_id: The item's ID
        feedback_type: "like", "dislike", or None (to remove feedback)
        db_path: Path to the database

    Returns:
        Dict with status and feedback info
    """
    ensure_feedback_table(db_path)
    conn = _get_connection(db_path)

    try:
        if feedback_type is None:
            # Remove feedback
            conn.execute(
                "DELETE FROM user_feedback WHERE user_id = ? AND item_id = ?",
                (user_id, item_id)
            )
            conn.commit()
            return {
                "status": "removed",
                "user_id": user_id,
                "item_id": item_id,
                "feedback_type": None,
            }

        # Insert or update feedback
        now = datetime.now().isoformat()
        conn.execute(
            """
            INSERT INTO user_feedback (user_id, item_id, feedback_type, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, item_id) DO UPDATE SET
                feedback_type = excluded.feedback_type,
                updated_at = excluded.updated_at
            """,
            (user_id, item_id, feedback_type, now, now)
        )
        conn.commit()

        return {
            "status": "saved",
            "user_id": user_id,
            "item_id": item_id,
            "feedback_type": feedback_type,
        }
    finally:
        conn.close()


def get_user_feedback(
    user_id: int,
    db_path: Path = DB_PATH,
) -> Dict[str, List[int]]:
    """
    Get all feedback for a user.

    Returns:
        Dict with 'likes' and 'dislikes' lists of item IDs
    """
    ensure_feedback_table(db_path)
    conn = _get_connection(db_path)

    try:
        rows = conn.execute(
            "SELECT item_id, feedback_type FROM user_feedback WHERE user_id = ?",
            (user_id,)
        ).fetchall()

        likes = [row["item_id"] for row in rows if row["feedback_type"] == "like"]
        dislikes = [row["item_id"] for row in rows if row["feedback_type"] == "dislike"]

        return {"likes": likes, "dislikes": dislikes}
    finally:
        conn.close()


def get_similar_items(
    item_id: int,
    top_n: int = SIMILAR_ITEMS_TO_BOOST,
    db_path: Path = DB_PATH,
) -> List[int]:
    """
    Get similar items from stored recommendations.

    Args:
        item_id: The item to find similar items for
        top_n: Number of similar items to return
        db_path: Path to the database

    Returns:
        List of similar item IDs
    """
    conn = _get_connection(db_path)

    try:
        # Look for item_similarity model recommendations for this item
        target_key = f"item_id#{item_id}"
        row = conn.execute(
            """
            SELECT items FROM recommendations
            WHERE target_key = ? AND model = 'item_similarity'
            """,
            (target_key,)
        ).fetchone()

        if row is None:
            return []

        try:
            items = json.loads(row["items"])
            return [item["item_id"] for item in items[:top_n]]
        except (json.JSONDecodeError, KeyError):
            return []
    finally:
        conn.close()


def adjust_recommendations_with_feedback(
    user_id: int,
    recommendations: List[Dict[str, Any]],
    db_path: Path = DB_PATH,
) -> List[Dict[str, Any]]:
    """
    Adjust recommendation scores based on user feedback.

    - Remove disliked items
    - Boost liked items by LIKE_BOOST_FACTOR
    - Boost items similar to liked items by SIMILAR_ITEM_BOOST_FACTOR

    Args:
        user_id: The user's ID
        recommendations: List of recommendation dicts with 'item_id' and 'score'
        db_path: Path to the database

    Returns:
        Adjusted and filtered recommendations
    """
    feedback = get_user_feedback(user_id, db_path)
    liked_items = set(feedback["likes"])
    disliked_items = set(feedback["dislikes"])

    # Get items similar to liked items
    similar_to_liked: set[int] = set()
    for liked_item in liked_items:
        similar = get_similar_items(liked_item, db_path=db_path)
        similar_to_liked.update(similar)

    # Remove the liked items from similar set to avoid double boost
    similar_to_liked -= liked_items

    adjusted_recommendations = []
    for rec in recommendations:
        item_id = rec.get("item_id")
        if item_id is None:
            continue

        # Skip disliked items
        if item_id in disliked_items:
            continue

        score = rec.get("score", 0.5)

        # Boost liked items
        if item_id in liked_items:
            score = min(score * LIKE_BOOST_FACTOR, 1.0)
        # Boost items similar to liked items
        elif item_id in similar_to_liked:
            score = min(score * SIMILAR_ITEM_BOOST_FACTOR, 1.0)

        adjusted_rec = {**rec, "score": float(score)}
        adjusted_recommendations.append(adjusted_rec)

    # Re-sort by adjusted score
    adjusted_recommendations.sort(key=lambda x: x.get("score", 0), reverse=True)

    return adjusted_recommendations


def get_feedback_adjusted_recommendations(
    user_id: int,
    model: Optional[str] = None,
    limit: int = 10,
    db_path: Path = DB_PATH,
) -> Dict[str, Any]:
    """
    Get recommendations for a user with feedback adjustments applied.

    Args:
        user_id: The user's ID
        model: Optional model name filter
        limit: Maximum number of recommendations per model
        db_path: Path to the database

    Returns:
        Dict with recommendations adjusted for user feedback
    """
    ensure_feedback_table(db_path)
    conn = _get_connection(db_path)

    try:
        # Get base recommendations
        target_key = f"user_id#{user_id}"

        filters = ["target_key = ?"]
        params: List[Any] = [target_key]
        if model is not None:
            filters.append("model = ?")
            params.append(model)

        where_clause = f"WHERE {' AND '.join(filters)}"
        query = f"""
            SELECT model, items, generated_at FROM recommendations
            {where_clause} ORDER BY model
        """
        rows = conn.execute(query, tuple(params)).fetchall()

        if not rows:
            return {
                "user_id": user_id,
                "recommendations": [],
                "feedback_applied": True,
            }

        recommendations = []
        for row in rows:
            try:
                items = json.loads(row["items"])
            except json.JSONDecodeError:
                continue

            # Apply feedback adjustments
            adjusted_items = adjust_recommendations_with_feedback(
                user_id, items, db_path
            )

            # Limit results
            limited_items = adjusted_items[:limit]

            recommendations.append({
                "model": row["model"],
                "items": limited_items,
                "generated_at": row["generated_at"],
            })

        return {
            "user_id": user_id,
            "recommendations": recommendations,
            "feedback_applied": True,
        }
    finally:
        conn.close()


def get_all_feedback_stats(db_path: Path = DB_PATH) -> Dict[str, Any]:
    """
    Get statistics about user feedback.

    Returns:
        Dict with feedback statistics
    """
    ensure_feedback_table(db_path)
    conn = _get_connection(db_path)

    try:
        total = conn.execute("SELECT COUNT(*) as count FROM user_feedback").fetchone()["count"]
        likes = conn.execute(
            "SELECT COUNT(*) as count FROM user_feedback WHERE feedback_type = 'like'"
        ).fetchone()["count"]
        dislikes = conn.execute(
            "SELECT COUNT(*) as count FROM user_feedback WHERE feedback_type = 'dislike'"
        ).fetchone()["count"]
        users_with_feedback = conn.execute(
            "SELECT COUNT(DISTINCT user_id) as count FROM user_feedback"
        ).fetchone()["count"]

        return {
            "total_feedback": total,
            "likes": likes,
            "dislikes": dislikes,
            "users_with_feedback": users_with_feedback,
        }
    finally:
        conn.close()


if __name__ == "__main__":
    # Test the feedback system
    ensure_feedback_table()

    # Save some test feedback
    print("Saving test feedback...")
    print(save_feedback(1, 10, "like"))
    print(save_feedback(1, 20, "dislike"))
    print(save_feedback(1, 30, "like"))

    # Get user feedback
    print("\nUser 1 feedback:")
    print(get_user_feedback(1))

    # Get feedback stats
    print("\nFeedback stats:")
    print(get_all_feedback_stats())

    # Test recommendation adjustment
    print("\nTesting recommendation adjustment...")
    test_recs = [
        {"item_id": 10, "score": 0.8},  # liked - should be boosted
        {"item_id": 20, "score": 0.9},  # disliked - should be removed
        {"item_id": 30, "score": 0.7},  # liked - should be boosted
        {"item_id": 40, "score": 0.6},  # neutral
    ]
    adjusted = adjust_recommendations_with_feedback(1, test_recs)
    print("Adjusted recommendations:", adjusted)
