from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterator, List, Sequence

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRouter

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "data.db"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
api_router = APIRouter(prefix="/api")


def get_connection() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def _fetch_all(conn: sqlite3.Connection, query: str, params: Sequence[Any] = ()) -> List[Dict[str, Any]]:
    cursor = conn.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]


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
            "SELECT id, title, url, description FROM items "
            f"WHERE id IN ({placeholders}) ORDER BY id"
        )
        rows = _fetch_all(conn, query, tuple(requested_ids))
        not_found = sorted(set(requested_ids) - {row["id"] for row in rows})
        if not_found:
            raise HTTPException(status_code=404, detail=f"Items not found: {not_found}")
        return rows

    return _fetch_all(conn, "SELECT id, title, url, description FROM items ORDER BY id")


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
                "items": items[:limit],
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


app.include_router(api_router)


@app.get("/")
def root() -> Dict[str, str]:
    return {"message": "Recommender API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)