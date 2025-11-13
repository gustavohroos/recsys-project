"""Item-similarity recommender based on sentence embeddings."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence

import numpy as np
from sentence_transformers import SentenceTransformer

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_BATCH_SIZE = 32


@dataclass(frozen=True)
class ItemRecord:
    item_id: int
    text: str


def _normalize_row(row: Dict[str, str | None]) -> Dict[str, str | None]:
    return {
        key.strip(): (value.strip() if value else value)
        for key, value in row.items()
        if key
    }


def _load_items(data_dir: Path) -> List[ItemRecord]:
    csv_path = data_dir / "items.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"items.csv not found in {data_dir}")

    records: List[ItemRecord] = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw_row in reader:
            if raw_row is None:
                continue
            row = _normalize_row(raw_row)
            raw_id = row.get("Item")
            if not raw_id:
                continue
            try:
                item_id = int(raw_id)
            except ValueError:
                continue
            title = row.get("Title") or ""
            description = row.get("Descriptions") or ""
            text = f"{title.strip()} {description.strip()}".strip()
            if not text:
                text = title.strip() or f"Item {item_id}"
            records.append(ItemRecord(item_id=item_id, text=text))

    if not records:
        raise ValueError(f"No items loaded from {csv_path}")

    return records


def _compute_embeddings(
    records: Sequence[ItemRecord],
    *,
    model_name: str = DEFAULT_MODEL_NAME,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> np.ndarray:
    model = SentenceTransformer(model_name)
    texts = [record.text for record in records]
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return embeddings.astype(np.float32, copy=False)


def _build_similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    if embeddings.ndim != 2:
        raise ValueError("Embeddings array must be 2D")
    return embeddings @ embeddings.T


def _top_n_similar(
    similarity_matrix: np.ndarray,
    item_ids: Sequence[int],
    top_n: int,
) -> Dict[str, List[int]]:
    num_items = len(item_ids)
    if similarity_matrix.shape != (num_items, num_items):
        raise ValueError("Similarity matrix shape mismatch")

    recommendations: Dict[str, List[int]] = {}
    for idx, item_id in enumerate(item_ids):
        scores = similarity_matrix[idx]
        if num_items <= 1:
            recommendations[f"item_id#{item_id}"] = []
            continue

        # Retrieve top_n + 1 to account for the item itself, then drop self-reference.
        candidate_count = min(top_n + 1, num_items)
        candidate_indices = np.argpartition(scores, -candidate_count)[-candidate_count:]
        sorted_candidate_indices = candidate_indices[np.argsort(scores[candidate_indices])[::-1]]

        similar_items: List[int] = []
        for candidate_idx in sorted_candidate_indices:
            candidate_id = item_ids[candidate_idx]
            if candidate_id == item_id:
                continue
            similar_items.append(candidate_id)
            if len(similar_items) >= top_n:
                break

        recommendations[f"item_id#{item_id}"] = similar_items

    return recommendations


def generate_item_similarity_recommendations(
    top_n: int = 10,
    *,
    data_dir: Path = DATA_DIR,
    model_name: str = DEFAULT_MODEL_NAME,
    batch_size: int = DEFAULT_BATCH_SIZE,
    seed: int | None = None,
) -> Dict[str, List[int]]:
    del seed  # Unused, but kept for a compatible signature.
    if top_n < 1:
        raise ValueError("top_n must be at least 1")

    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    records = _load_items(data_dir)
    embeddings = _compute_embeddings(records, model_name=model_name, batch_size=batch_size)
    similarity = _build_similarity_matrix(embeddings)
    item_ids = [record.item_id for record in records]
    return _top_n_similar(similarity, item_ids, top_n)


if __name__ == "__main__":  # pragma: no cover - manual usage helper
    recommendations = generate_item_similarity_recommendations()
    for key, items in list(recommendations.items())[:5]:
        print(key, "->", items)
