"""Random baseline recommender for quick sanity checks."""

from __future__ import annotations

import csv
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load_identifiers(csv_path: Path, id_column: str) -> List[int]:
	identifiers: List[int] = []
	with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
		reader = csv.DictReader(handle)
		for raw_row in reader:
			if raw_row is None:
				continue
			normalized = {
				key.strip(): (value.strip() if value else value)
				for key, value in raw_row.items()
				if key
			}
			value = normalized.get(id_column)
			if value in (None, ""):
				continue
			identifiers.append(int(value))

	if not identifiers:
		raise ValueError(f"No identifiers found in {csv_path}")
	return identifiers


@dataclass(slots=True)
class RandomRecommender:
    user_ids: List[int]
    item_ids: List[int]
    rng: random.Random

    @classmethod
    def from_data(
        cls,
        data_dir: Path = DATA_DIR,
        seed: int | None = None,
    ) -> "RandomRecommender":
        if not data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {data_dir}")

        user_ids = _load_identifiers(data_dir / "users.csv", "UserID")
        item_ids = _load_identifiers(data_dir / "items.csv", "Item")
        rng = random.Random(seed)
        return cls(user_ids=user_ids, item_ids=item_ids, rng=rng)

    def recommend(self, top_n: int = 10) -> Dict[str, List[int]]:
        if top_n < 1:
            raise ValueError("top_n must be at least 1")

        recs: Dict[str, List[int]] = {}

        item_pool: Sequence[int] = tuple(self.item_ids)
        n_items = len(item_pool)
        limit = min(top_n, n_items)

        for user_id in self.user_ids:
            selected = self.rng.sample(item_pool, k=limit)
            recs[f"user_id#{user_id}"] = list(selected)

        for item_id in self.item_ids:
            if n_items == 1:
                recs[f"item_id#{item_id}"] = []
                continue
            candidates = [candidate for candidate in item_pool if candidate != item_id]
            size = min(top_n, len(candidates))
            selected = self.rng.sample(candidates, k=size) if size else []
            recs[f"item_id#{item_id}"] = list(selected)

        return recs


def generate_random_recommendations(
    top_n: int = 10,
    seed: int | None = None,
    data_dir: Path = DATA_DIR,
) -> Dict[str, List[int]]:
    recommender = RandomRecommender.from_data(data_dir=data_dir, seed=seed)
    return recommender.recommend(top_n=top_n)


def _dump_recommendations(recommendations: Dict[str, Iterable[int]]) -> str:
    return json.dumps(recommendations, indent=2, sort_keys=True)


if __name__ == "__main__":
    output = generate_random_recommendations()
    print(_dump_recommendations(output))
