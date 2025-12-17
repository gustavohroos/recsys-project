import argparse
import sqlite3
from pathlib import Path

DB_PATH = Path("data") / "data.db"

def generate_top_rated(conn, min_ratings: int, limit: int):
    conn.execute("DELETE FROM top_rated_items;")

    rows = conn.execute(
        """
        SELECT
          i.id AS item_id,
          i.title,
          i.description,
          i.image_url,
          AVG(r.rating) AS avg_rating,
          COUNT(*) AS rating_count
        FROM ratings r
        JOIN items i ON i.id = r.item_id
        WHERE r.rating IS NOT NULL
        GROUP BY i.id
        HAVING COUNT(*) >= ?
        ORDER BY avg_rating DESC, rating_count DESC, i.id ASC
        LIMIT ?;
        """,
        (min_ratings, limit),
    ).fetchall()

    for rank, (item_id, title, description, image_url, avg_rating, rating_count) in enumerate(rows, start=1):
        conn.execute(
            """
            INSERT INTO top_rated_items
            (rank, item_id, title, description, image_url, avg_rating, rating_count)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (rank, item_id, title, description, image_url, float(avg_rating), int(rating_count)),
        )

    conn.commit()
    return len(rows)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-ratings", type=int, default=3)
    parser.add_argument("--limit", type=int, default=500)
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    try:
        n = generate_top_rated(conn, args.min_ratings, args.limit)
        print(f"Stored {n} top-rated items")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
