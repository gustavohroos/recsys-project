from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterator, List, Sequence

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.routing import APIRouter

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "data.db"

app = FastAPI()
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
def list_items(conn: sqlite3.Connection = Depends(get_connection)) -> List[Dict[str, Any]]:
    return _fetch_all(conn, "SELECT id, title, url, description FROM items ORDER BY id")


@api_router.get("/items/{item_id}")
def get_item(item_id: int, conn: sqlite3.Connection = Depends(get_connection)) -> Dict[str, Any]:
    row = conn.execute(
        "SELECT id, title, url, description FROM items WHERE id = ?",
        (item_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return dict(row)


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


@api_router.get("/recommendations")
def list_recommendations(
    user_id: int = Query(..., description="User id to generate recommendations for"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of items to return"),
) -> Dict[str, Any]:
    detail = "Recommendations service not implemented yet"
    return {"user_id": user_id, "limit": limit, "detail": detail, "recommendations": []}


app.include_router(api_router)


@app.get("/")
def root() -> Dict[str, str]:
    return {"message": "Recommender API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)