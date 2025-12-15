from __future__ import annotations

import asyncio
import json
import sqlite3
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, List, Sequence

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRouter
from pydantic import BaseModel

# Add recsys to path for imports
RECSYS_PATH = Path(__file__).resolve().parent.parent / "recsys"
sys.path.insert(0, str(RECSYS_PATH))

from preference_recommender import compute_preference_based_recommendations
from feedback_recommender import (
    save_feedback,
    get_user_feedback,
    get_feedback_adjusted_recommendations,
    get_all_feedback_stats,
    ensure_feedback_table,
)

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "data.db"

# Background task configuration
RECOMMENDATION_REGENERATION_INTERVAL_SECONDS = 300  # 5 minutes
_background_task_running = False


async def regenerate_recommendations_periodically():
    """Background task to regenerate recommendations periodically."""
    global _background_task_running

    while _background_task_running:
        try:
            print("[Background] Starting recommendation regeneration...")
            # Import here to avoid circular imports
            from generate_recommendations import main as generate_main
            generate_main()
            print("[Background] Recommendation regeneration complete.")
        except Exception as e:
            print(f"[Background] Error regenerating recommendations: {e}")

        await asyncio.sleep(RECOMMENDATION_REGENERATION_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app lifespan - start and stop background tasks."""
    global _background_task_running

    # Ensure feedback table exists
    ensure_feedback_table(DB_PATH)

    # Start background task
    _background_task_running = True
    task = asyncio.create_task(regenerate_recommendations_periodically())

    yield

    # Stop background task
    _background_task_running = False
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
api_router = APIRouter(prefix="/api")
def get_connection() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def _fetch_all(conn: sqlite3.Connection, query: str, params: Sequence[Any] = ()) -> List[Dict[str, Any]]:
    cursor = conn.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]


def _normalize_scored_items(raw_items: Any, limit: int) -> List[Dict[str, Any]]:
    if not isinstance(raw_items, list):
        raise HTTPException(status_code=500, detail="Stored recommendations have invalid format")

    normalized: List[Dict[str, Any]] = []
    for entry in raw_items:
        if isinstance(entry, dict):
            item_id = entry.get("item_id")
            if item_id is None:
                continue
            score = entry.get("score")
            normalized.append(
                {
                    "item_id": int(item_id),
                    "score": float(score) if score is not None else None,
                }
            )
        elif isinstance(entry, (int, float)):
            normalized.append({"item_id": int(entry), "score": None})
        else:
            continue

        if len(normalized) >= limit:
            break

    return normalized


@api_router.get("/items")
def list_items(
    ids: str | None = Query(default=None, description="Comma-separated list of item ids"),
    conn: sqlite3.Connection = Depends(get_connection),
) -> List[Dict[str, Any]]:
    if ids:
        try:
            requested_ids = [int(value.strip()) for value in ids.split(",") if value.strip()]
        except ValueError:
            raise HTTPException(status_code=400, detail="ids must be integers separated by commas")
        if not requested_ids:
            raise HTTPException(status_code=400, detail="No valid ids provided")

        placeholders = ",".join("?" for _ in requested_ids)
        query = (
            "SELECT id, title, url, description, image_url FROM items "
            f"WHERE id IN ({placeholders}) ORDER BY id"
        )
        rows = _fetch_all(conn, query, tuple(requested_ids))
        not_found = sorted(set(requested_ids) - {row["id"] for row in rows})
        if not_found:
            raise HTTPException(status_code=404, detail=f"Items not found: {not_found}")
        return rows

    return _fetch_all(conn, "SELECT id, title, url, description, image_url FROM items ORDER BY id")


@api_router.get("/users")
def list_users(conn: sqlite3.Connection = Depends(get_connection)) -> List[Dict[str, Any]]:
    return _fetch_all(conn, "SELECT id, gender, age_range, married FROM users ORDER BY id")


@api_router.get("/users/{user_id}")
def get_user(user_id: int, conn: sqlite3.Connection = Depends(get_connection)) -> Dict[str, Any]:
    row = conn.execute(
        "SELECT id, gender, age_range, married FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(row)


@api_router.get("/ratings")
def list_ratings(
    user_id: int | None = Query(default=None, description="Filter ratings by user id"),
    item_id: int | None = Query(default=None, description="Filter ratings by item id"),
    conn: sqlite3.Connection = Depends(get_connection),
) -> List[Dict[str, Any]]:
    filters: List[str] = []
    params: List[Any] = []
    if user_id is not None:
        filters.append("user_id = ?")
        params.append(user_id)
    if item_id is not None:
        filters.append("item_id = ?")
        params.append(item_id)

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    query = (
        "SELECT user_id, item_id, rating, app, data, ease, class, semester, lockdown "
        f"FROM ratings {where_clause} ORDER BY user_id, item_id"
    )
    return _fetch_all(conn, query, tuple(params))


@api_router.get("/groups")
def list_groups(conn: sqlite3.Connection = Depends(get_connection)) -> List[Dict[str, Any]]:
    groups = _fetch_all(conn, "SELECT id FROM groups ORDER BY id")
    memberships = _fetch_all(
        conn,
        "SELECT group_id, user_id FROM group_members ORDER BY group_id, user_id",
    )

    members_by_group: Dict[int, List[int]] = {group["id"]: [] for group in groups}
    for membership in memberships:
        members_by_group.setdefault(membership["group_id"], []).append(membership["user_id"])

    return [
        {"id": group_id, "members": members_by_group.get(group_id, [])}
        for group_id in members_by_group
    ]


@api_router.get("/group-sizes")
def list_group_sizes(conn: sqlite3.Connection = Depends(get_connection)) -> List[Dict[str, Any]]:
    return _fetch_all(conn, "SELECT group_id, size FROM group_sizes ORDER BY group_id")


@api_router.get("/group-ratings")
def list_group_ratings(
    group_id: int | None = Query(default=None, description="Filter ratings by group id"),
    conn: sqlite3.Connection = Depends(get_connection),
) -> List[Dict[str, Any]]:
    params: List[Any] = []
    where_clause = ""
    if group_id is not None:
        where_clause = "WHERE group_id = ?"
        params.append(group_id)

    query = (
        "SELECT group_id, item_id, rating, app, data, ease, class, semester, lockdown "
        f"FROM group_ratings {where_clause} ORDER BY group_id, item_id"
    )
    return _fetch_all(conn, query, tuple(params))


def _ensure_exists(conn: sqlite3.Connection, table: str, entity_id: int) -> None:
    row = conn.execute(f"SELECT 1 FROM {table} WHERE id = ?", (entity_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"{table.rstrip('s').capitalize()} not found")


@api_router.get("/recommendations")
def list_recommendations(
    user_id: int | None = Query(default=None, description="User id to fetch recommendations for"),
    item_id: int | None = Query(default=None, description="Item id to fetch recommendations for"),
    model: str | None = Query(default=None, description="Optional model name filter"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of items per model"),
    conn: sqlite3.Connection = Depends(get_connection),
) -> Dict[str, Any]:
    if user_id is None and item_id is None:
        raise HTTPException(status_code=400, detail="Provide either user_id or item_id")

    if user_id is not None:
        _ensure_exists(conn, "users", user_id)
        target_key = f"user_id#{user_id}"
        target_type = "user"
        target_id = user_id
    elif item_id is not None:
        _ensure_exists(conn, "items", item_id)
        target_key = f"item_id#{item_id}"
        target_type = "item"
        target_id = item_id
    else:
        raise HTTPException(status_code=400, detail="Unable to resolve recommendation target")

    filters = ["target_key = ?"]
    params: List[Any] = [target_key]
    if model is not None:
        filters.append("model = ?")
        params.append(model)

    where_clause = f"WHERE {' AND '.join(filters)}"
    query = (
        "SELECT model, items, generated_at FROM recommendations "
        f"{where_clause} ORDER BY model"
    )
    rows = _fetch_all(conn, query, tuple(params))

    if not rows:
        raise HTTPException(status_code=404, detail="No recommendations found for the requested target")

    recommendations = []
    for row in rows:
        try:
            items = json.loads(row["items"])
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=500, detail="Stored recommendations are corrupted") from exc
        recommendations.append(
            {
                "model": row["model"],
                "items": _normalize_scored_items(items, limit),
                "generated_at": row["generated_at"],
            }
        )

    return {
        "target_type": target_type,
        "target_id": target_id,
        "target_key": target_key,
        "model": model,
        "limit": limit,
        "recommendations": recommendations,
    }





# Categories endpoints
@api_router.get("/categories")
def list_categories(
    conn: sqlite3.Connection = Depends(get_connection),
) -> List[Dict[str, Any]]:
    """Get all available categories with item counts."""
    try:
        rows = _fetch_all(
            conn,
            """
            SELECT c.id, c.name, c.description, c.icon,
                   COUNT(ic.item_id) as item_count
            FROM categories c
            LEFT JOIN item_categories ic ON c.id = ic.category_id
            GROUP BY c.id
            ORDER BY item_count DESC
            """
        )
        return rows
    except sqlite3.OperationalError:
        # Categories table doesn't exist yet
        return []


@api_router.get("/items/{item_id}/categories")
def get_item_categories(
    item_id: int,
    conn: sqlite3.Connection = Depends(get_connection),
) -> List[Dict[str, Any]]:
    """Get categories for a specific item."""
    _ensure_exists(conn, "items", item_id)
    try:
        rows = _fetch_all(
            conn,
            """
            SELECT c.id, c.name, c.description, c.icon, ic.is_primary
            FROM categories c
            JOIN item_categories ic ON c.id = ic.category_id
            WHERE ic.item_id = ?
            ORDER BY ic.is_primary DESC
            """,
            (item_id,)
        )
        return rows
    except sqlite3.OperationalError:
        return []


@api_router.get("/categories/{category_id}/items")
def get_category_items(
    category_id: str,
    limit: int = Query(20, ge=1, le=100),
    conn: sqlite3.Connection = Depends(get_connection),
) -> List[Dict[str, Any]]:
    """Get items in a specific category."""
    try:
        rows = _fetch_all(
            conn,
            """
            SELECT i.id, i.title, i.url, i.description, i.image_url, ic.is_primary
            FROM items i
            JOIN item_categories ic ON i.id = ic.item_id
            WHERE ic.category_id = ?
            ORDER BY ic.is_primary DESC, i.id
            LIMIT ?
            """,
            (category_id, limit)
        )
        return rows
    except sqlite3.OperationalError:
        return []


class PreferenceRequest(BaseModel):
    categories: List[str]
    limit: int = 10


@api_router.post("/recommendations/by-preferences")
def get_recommendations_by_preferences(
    request: PreferenceRequest,
    conn: sqlite3.Connection = Depends(get_connection),
) -> Dict[str, Any]:
    """Get recommendations based on category preferences."""
    if not request.categories:
        raise HTTPException(status_code=400, detail="At least one category must be provided")

    # Validate categories exist
    try:
        existing = _fetch_all(
            conn,
            "SELECT id FROM categories WHERE id IN ({})".format(
                ",".join("?" for _ in request.categories)
            ),
            tuple(request.categories)
        )
        existing_ids = {row["id"] for row in existing}
        invalid = [c for c in request.categories if c not in existing_ids]
        if invalid:
            raise HTTPException(status_code=400, detail=f"Invalid categories: {invalid}")
    except sqlite3.OperationalError:
        raise HTTPException(status_code=500, detail="Categories not initialized. Run extract_metadata.py first.")

    # Get recommendations
    recommendations = compute_preference_based_recommendations(
        preferred_categories=request.categories,
        top_n=request.limit,
        db_path=DB_PATH,
    )

    return {
        "categories": request.categories,
        "limit": request.limit,
        "items": recommendations,
    }


# Feedback endpoints
class FeedbackRequest(BaseModel):
    user_id: int = 1  # Default user for demo purposes
    itemId: int
    feedback: str | None  # "like", "dislike", or null


@api_router.post("/feedback")
def submit_feedback(
    request: FeedbackRequest,
) -> Dict[str, Any]:
    """Submit user feedback (like/dislike) for an item."""
    if request.feedback not in ("like", "dislike", None):
        raise HTTPException(
            status_code=400,
            detail="feedback must be 'like', 'dislike', or null"
        )

    result = save_feedback(
        user_id=request.user_id,
        item_id=request.itemId,
        feedback_type=request.feedback,
        db_path=DB_PATH,
    )

    return result


@api_router.get("/feedback/{user_id}")
def get_feedback(
    user_id: int,
) -> Dict[str, Any]:
    """Get all feedback for a specific user."""
    feedback = get_user_feedback(user_id, db_path=DB_PATH)
    return {
        "user_id": user_id,
        **feedback,
    }


@api_router.get("/feedback/stats")
def get_feedback_stats() -> Dict[str, Any]:
    """Get global feedback statistics."""
    return get_all_feedback_stats(db_path=DB_PATH)


@api_router.get("/recommendations/with-feedback")
def get_recommendations_with_feedback(
    user_id: int = Query(..., description="User id to fetch recommendations for"),
    model: str | None = Query(default=None, description="Optional model name filter"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of items per model"),
    conn: sqlite3.Connection = Depends(get_connection),
) -> Dict[str, Any]:
    """
    Get recommendations for a user with feedback adjustments applied.

    - Removes disliked items
    - Boosts liked items and similar items
    """
    _ensure_exists(conn, "users", user_id)

    result = get_feedback_adjusted_recommendations(
        user_id=user_id,
        model=model,
        limit=limit,
        db_path=DB_PATH,
    )

    if not result["recommendations"]:
        raise HTTPException(
            status_code=404,
            detail="No recommendations found for the requested user"
        )

    return {
        "target_type": "user",
        "target_id": user_id,
        "target_key": f"user_id#{user_id}",
        "model": model,
        "limit": limit,
        **result,
    }


@api_router.delete("/feedback/reset")
def reset_all_feedback(
    conn: sqlite3.Connection = Depends(get_connection),
) -> Dict[str, Any]:
    """Reset all user feedback (likes and dislikes) for all users."""
    try:
        cursor = conn.execute("DELETE FROM user_feedback")
        deleted_count = cursor.rowcount
        conn.commit()
        return {
            "status": "success",
            "message": "All feedback has been reset",
            "deleted_count": deleted_count,
        }
    except sqlite3.OperationalError as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset feedback: {e}")


@app.get("/")
def root() -> Dict[str, str]:
    return {"message": "Recommender API"}

app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)