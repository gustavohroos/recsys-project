"""Collaborative Filtering recommender using user-item ratings matrix."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import svds
from sklearn.metrics.pairwise import cosine_similarity

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Minimum number of common ratings required for similarity calculation
MIN_COMMON_RATINGS = 2
# Number of similar users/items to consider for prediction
K_NEIGHBORS = 20
# SVD components for matrix factorization
N_COMPONENTS = 50


def _normalize_row(row: Dict[str, str | None]) -> Dict[str, str | None]:
    """Normalize CSV row by stripping whitespace from keys and values."""
    return {
        key.strip(): (value.strip() if value else value)
        for key, value in row.items()
        if key
    }


def _load_ratings(data_dir: Path) -> List[Tuple[int, int, float]]:
    """Load ratings from CSV file.

    Returns:
        List of (user_id, item_id, rating) tuples.
    """
    csv_path = data_dir / "ratings.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"ratings.csv not found in {data_dir}")

    ratings: List[Tuple[int, int, float]] = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw_row in reader:
            if raw_row is None:
                continue
            row = _normalize_row(raw_row)

            user_id_str = row.get("UserID")
            item_id_str = row.get("Item")
            rating_str = row.get("Rating")

            if not user_id_str or not item_id_str or not rating_str:
                continue

            try:
                user_id = int(user_id_str)
                item_id = int(item_id_str)
                rating = float(rating_str)
                ratings.append((user_id, item_id, rating))
            except ValueError:
                continue

    if not ratings:
        raise ValueError(f"No ratings loaded from {csv_path}")

    return ratings


def _load_identifiers(csv_path: Path, id_column: str) -> List[int]:
    """Load identifiers from a CSV file."""
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


@dataclass
class RatingsMatrix:
    """Sparse user-item ratings matrix with index mappings."""

    matrix: csr_matrix
    user_to_idx: Dict[int, int]
    idx_to_user: Dict[int, int]
    item_to_idx: Dict[int, int]
    idx_to_item: Dict[int, int]
    user_means: np.ndarray
    item_means: np.ndarray
    global_mean: float

    @classmethod
    def from_ratings(
        cls,
        ratings: List[Tuple[int, int, float]],
        all_user_ids: List[int],
        all_item_ids: List[int],
    ) -> "RatingsMatrix":
        """Build a sparse ratings matrix from rating tuples.

        Args:
            ratings: List of (user_id, item_id, rating) tuples.
            all_user_ids: List of all user IDs in the system.
            all_item_ids: List of all item IDs in the system.

        Returns:
            RatingsMatrix with sparse matrix and index mappings.
        """
        # Create mappings for all users and items
        user_to_idx = {uid: idx for idx, uid in enumerate(sorted(set(all_user_ids)))}
        idx_to_user = {idx: uid for uid, idx in user_to_idx.items()}
        item_to_idx = {iid: idx for idx, iid in enumerate(sorted(set(all_item_ids)))}
        idx_to_item = {idx: iid for iid, idx in item_to_idx.items()}

        n_users = len(user_to_idx)
        n_items = len(item_to_idx)

        # Build sparse matrix
        rows, cols, data = [], [], []
        for user_id, item_id, rating in ratings:
            if user_id in user_to_idx and item_id in item_to_idx:
                rows.append(user_to_idx[user_id])
                cols.append(item_to_idx[item_id])
                data.append(rating)

        matrix = csr_matrix(
            (data, (rows, cols)),
            shape=(n_users, n_items),
            dtype=np.float32,
        )

        # Calculate means for normalization
        # User means (only for rated items)
        user_means = np.zeros(n_users, dtype=np.float32)
        for i in range(n_users):
            row = matrix.getrow(i)
            if row.nnz > 0:
                user_means[i] = row.data.mean()

        # Item means (only for rated items)
        item_means = np.zeros(n_items, dtype=np.float32)
        matrix_csc = matrix.tocsc()
        for j in range(n_items):
            col = matrix_csc.getcol(j)
            if col.nnz > 0:
                item_means[j] = col.data.mean()

        # Global mean
        global_mean = float(np.mean(data)) if data else 0.0

        return cls(
            matrix=matrix,
            user_to_idx=user_to_idx,
            idx_to_user=idx_to_user,
            item_to_idx=item_to_idx,
            idx_to_item=idx_to_item,
            user_means=user_means,
            item_means=item_means,
            global_mean=global_mean,
        )


@dataclass
class UserBasedCF:
    """User-based collaborative filtering recommender.

    Uses cosine similarity between users based on their rating patterns
    to predict ratings for items a user hasn't seen.
    """

    ratings_matrix: RatingsMatrix
    user_similarity: np.ndarray = field(init=False)
    k_neighbors: int = K_NEIGHBORS

    def __post_init__(self) -> None:
        """Compute user-user similarity matrix."""
        # Mean-center the ratings for better similarity calculation
        centered_matrix = self._mean_center_matrix()

        # Compute cosine similarity between users
        self.user_similarity = cosine_similarity(centered_matrix, dense_output=True)

        # Set self-similarity to 0 to exclude self from neighbors
        np.fill_diagonal(self.user_similarity, 0)

    def _mean_center_matrix(self) -> np.ndarray:
        """Mean-center the ratings matrix by user."""
        dense = self.ratings_matrix.matrix.toarray()
        mask = dense != 0

        # Subtract user mean only from rated items
        centered = dense.copy()
        for i in range(dense.shape[0]):
            user_mean = self.ratings_matrix.user_means[i]
            if user_mean > 0:
                centered[i, mask[i]] -= user_mean

        return centered

    def predict_rating(self, user_idx: int, item_idx: int) -> float:
        """Predict rating for a user-item pair using k-nearest neighbors.

        Args:
            user_idx: Index of the user in the matrix.
            item_idx: Index of the item in the matrix.

        Returns:
            Predicted rating.
        """
        # Get similarity scores with all other users
        similarities = self.user_similarity[user_idx]

        # Get users who have rated this item
        item_ratings = self.ratings_matrix.matrix.getcol(item_idx).toarray().flatten()
        rated_mask = item_ratings != 0

        # Filter to users who rated the item
        valid_users = np.where(rated_mask)[0]
        if len(valid_users) == 0:
            return self.ratings_matrix.global_mean

        # Get top-k similar users who rated this item
        valid_similarities = similarities[valid_users]
        top_k_indices = np.argsort(valid_similarities)[-self.k_neighbors:]
        top_k_users = valid_users[top_k_indices]
        top_k_sims = valid_similarities[top_k_indices]

        # Filter out negative similarities
        positive_mask = top_k_sims > 0
        if not np.any(positive_mask):
            return self.ratings_matrix.user_means[user_idx] or self.ratings_matrix.global_mean

        top_k_users = top_k_users[positive_mask]
        top_k_sims = top_k_sims[positive_mask]

        # Weighted average of ratings
        numerator = 0.0
        denominator = 0.0
        user_mean = self.ratings_matrix.user_means[user_idx]

        for neighbor_idx, sim in zip(top_k_users, top_k_sims):
            neighbor_mean = self.ratings_matrix.user_means[neighbor_idx]
            neighbor_rating = item_ratings[neighbor_idx]
            # Use deviation from neighbor's mean
            numerator += sim * (neighbor_rating - neighbor_mean)
            denominator += abs(sim)

        if denominator == 0:
            return user_mean or self.ratings_matrix.global_mean

        predicted = user_mean + (numerator / denominator)
        # Clip to valid rating range
        return float(np.clip(predicted, 1.0, 5.0))

    def recommend_for_user(
        self,
        user_id: int,
        top_n: int = 10,
    ) -> List[Dict[str, float]]:
        """Generate top-N recommendations for a user.

        Args:
            user_id: The user ID to generate recommendations for.
            top_n: Number of recommendations to return.

        Returns:
            List of dicts with item_id and predicted score.
        """
        if user_id not in self.ratings_matrix.user_to_idx:
            return []

        user_idx = self.ratings_matrix.user_to_idx[user_id]

        # Get items the user has already rated
        user_ratings = self.ratings_matrix.matrix.getrow(user_idx).toarray().flatten()
        rated_items = set(np.where(user_ratings != 0)[0])

        # Predict ratings for unrated items
        predictions: List[Tuple[int, float]] = []
        for item_idx in range(self.ratings_matrix.matrix.shape[1]):
            if item_idx in rated_items:
                continue
            pred = self.predict_rating(user_idx, item_idx)
            item_id = self.ratings_matrix.idx_to_item[item_idx]
            predictions.append((item_id, pred))

        # Sort by predicted rating and return top-N
        predictions.sort(key=lambda x: x[1], reverse=True)

        return [
            {"item_id": item_id, "score": round(float(score), 6)}
            for item_id, score in predictions[:top_n]
        ]


@dataclass
class ItemBasedCF:
    """Item-based collaborative filtering recommender.

    Uses cosine similarity between items based on user rating patterns
    to predict ratings and find similar items.
    """

    ratings_matrix: RatingsMatrix
    item_similarity: np.ndarray = field(init=False)
    k_neighbors: int = K_NEIGHBORS

    def __post_init__(self) -> None:
        """Compute item-item similarity matrix."""
        # Transpose to get item vectors (each row is an item)
        item_vectors = self.ratings_matrix.matrix.T.toarray()

        # Mean-center by item
        mask = item_vectors != 0
        centered = item_vectors.copy()
        for i in range(item_vectors.shape[0]):
            item_mean = self.ratings_matrix.item_means[i]
            if item_mean > 0:
                centered[i, mask[i]] -= item_mean

        # Compute cosine similarity between items
        self.item_similarity = cosine_similarity(centered, dense_output=True)

        # Set self-similarity to 0
        np.fill_diagonal(self.item_similarity, 0)

    def predict_rating(self, user_idx: int, item_idx: int) -> float:
        """Predict rating for a user-item pair.

        Args:
            user_idx: Index of the user in the matrix.
            item_idx: Index of the item in the matrix.

        Returns:
            Predicted rating.
        """
        # Get user's ratings
        user_ratings = self.ratings_matrix.matrix.getrow(user_idx).toarray().flatten()
        rated_mask = user_ratings != 0

        # Get items the user has rated
        rated_items = np.where(rated_mask)[0]
        if len(rated_items) == 0:
            return self.ratings_matrix.global_mean

        # Get similarity of target item to rated items
        similarities = self.item_similarity[item_idx, rated_items]

        # Get top-k most similar items
        top_k_indices = np.argsort(similarities)[-self.k_neighbors:]
        top_k_items = rated_items[top_k_indices]
        top_k_sims = similarities[top_k_indices]

        # Filter out negative similarities
        positive_mask = top_k_sims > 0
        if not np.any(positive_mask):
            return self.ratings_matrix.item_means[item_idx] or self.ratings_matrix.global_mean

        top_k_items = top_k_items[positive_mask]
        top_k_sims = top_k_sims[positive_mask]

        # Weighted average
        numerator = np.sum(top_k_sims * user_ratings[top_k_items])
        denominator = np.sum(np.abs(top_k_sims))

        if denominator == 0:
            return self.ratings_matrix.item_means[item_idx] or self.ratings_matrix.global_mean

        predicted = numerator / denominator
        return float(np.clip(predicted, 1.0, 5.0))

    def recommend_for_user(
        self,
        user_id: int,
        top_n: int = 10,
    ) -> List[Dict[str, float]]:
        """Generate top-N recommendations for a user.

        Args:
            user_id: The user ID to generate recommendations for.
            top_n: Number of recommendations to return.

        Returns:
            List of dicts with item_id and predicted score.
        """
        if user_id not in self.ratings_matrix.user_to_idx:
            return []

        user_idx = self.ratings_matrix.user_to_idx[user_id]

        # Get items the user has already rated
        user_ratings = self.ratings_matrix.matrix.getrow(user_idx).toarray().flatten()
        rated_items = set(np.where(user_ratings != 0)[0])

        # Predict ratings for unrated items
        predictions: List[Tuple[int, float]] = []
        for item_idx in range(self.ratings_matrix.matrix.shape[1]):
            if item_idx in rated_items:
                continue
            pred = self.predict_rating(user_idx, item_idx)
            item_id = self.ratings_matrix.idx_to_item[item_idx]
            predictions.append((item_id, pred))

        # Sort by predicted rating and return top-N
        predictions.sort(key=lambda x: x[1], reverse=True)

        return [
            {"item_id": item_id, "score": round(float(score), 6)}
            for item_id, score in predictions[:top_n]
        ]

    def similar_items(
        self,
        item_id: int,
        top_n: int = 10,
    ) -> List[Dict[str, float]]:
        """Find items most similar to a given item.

        Args:
            item_id: The item ID to find similar items for.
            top_n: Number of similar items to return.

        Returns:
            List of dicts with item_id and similarity score.
        """
        if item_id not in self.ratings_matrix.item_to_idx:
            return []

        item_idx = self.ratings_matrix.item_to_idx[item_id]
        similarities = self.item_similarity[item_idx]

        # Get top-N most similar items (excluding self)
        top_indices = np.argsort(similarities)[::-1][:top_n]

        results = []
        for idx in top_indices:
            sim = similarities[idx]
            if sim <= 0:
                continue
            similar_item_id = self.ratings_matrix.idx_to_item[idx]
            results.append({
                "item_id": similar_item_id,
                "score": round(float(sim), 6),
            })

        return results


@dataclass
class MatrixFactorizationCF:
    """Matrix Factorization collaborative filtering using SVD.

    Decomposes the user-item matrix into latent factors for users and items,
    enabling predictions for any user-item pair.
    """

    ratings_matrix: RatingsMatrix
    n_components: int = N_COMPONENTS
    user_factors: np.ndarray = field(init=False)
    item_factors: np.ndarray = field(init=False)
    sigma: np.ndarray = field(init=False)

    def __post_init__(self) -> None:
        """Compute SVD decomposition of the ratings matrix."""
        # Fill zeros with global mean for SVD
        dense = self.ratings_matrix.matrix.toarray().astype(np.float64)
        mask = dense == 0
        dense[mask] = self.ratings_matrix.global_mean

        # Mean-center the matrix
        row_means = dense.mean(axis=1, keepdims=True)
        centered = dense - row_means

        # Limit components to matrix dimensions
        n_components = min(
            self.n_components,
            centered.shape[0] - 1,
            centered.shape[1] - 1,
        )

        if n_components < 1:
            n_components = 1

        # SVD decomposition
        U, sigma, Vt = svds(csr_matrix(centered), k=n_components)

        # Sort by singular values (svds returns in ascending order)
        idx = np.argsort(sigma)[::-1]
        self.user_factors = U[:, idx]
        self.sigma = sigma[idx]
        self.item_factors = Vt[idx, :].T

        # Store row means for prediction
        self._row_means = row_means.flatten()

    def predict_rating(self, user_idx: int, item_idx: int) -> float:
        """Predict rating using latent factors.

        Args:
            user_idx: Index of the user in the matrix.
            item_idx: Index of the item in the matrix.

        Returns:
            Predicted rating.
        """
        # Reconstruct prediction: U @ diag(sigma) @ V^T + row_mean
        user_vec = self.user_factors[user_idx] * self.sigma
        item_vec = self.item_factors[item_idx]
        pred = np.dot(user_vec, item_vec) + self._row_means[user_idx]
        return float(np.clip(pred, 1.0, 5.0))

    def recommend_for_user(
        self,
        user_id: int,
        top_n: int = 10,
    ) -> List[Dict[str, float]]:
        """Generate top-N recommendations for a user.

        Args:
            user_id: The user ID to generate recommendations for.
            top_n: Number of recommendations to return.

        Returns:
            List of dicts with item_id and predicted score.
        """
        if user_id not in self.ratings_matrix.user_to_idx:
            return []

        user_idx = self.ratings_matrix.user_to_idx[user_id]

        # Get items the user has already rated
        user_ratings = self.ratings_matrix.matrix.getrow(user_idx).toarray().flatten()
        rated_items = set(np.where(user_ratings != 0)[0])

        # Compute all predictions for this user
        user_vec = self.user_factors[user_idx] * self.sigma
        all_predictions = np.dot(user_vec, self.item_factors.T) + self._row_means[user_idx]
        all_predictions = np.clip(all_predictions, 1.0, 5.0)

        # Filter out rated items and get top-N
        predictions: List[Tuple[int, float]] = []
        for item_idx, pred in enumerate(all_predictions):
            if item_idx in rated_items:
                continue
            item_id = self.ratings_matrix.idx_to_item[item_idx]
            predictions.append((item_id, float(pred)))

        predictions.sort(key=lambda x: x[1], reverse=True)

        return [
            {"item_id": item_id, "score": round(score, 6)}
            for item_id, score in predictions[:top_n]
        ]

    def similar_items(
        self,
        item_id: int,
        top_n: int = 10,
    ) -> List[Dict[str, float]]:
        """Find items most similar based on latent factors.

        Args:
            item_id: The item ID to find similar items for.
            top_n: Number of similar items to return.

        Returns:
            List of dicts with item_id and similarity score.
        """
        if item_id not in self.ratings_matrix.item_to_idx:
            return []

        item_idx = self.ratings_matrix.item_to_idx[item_id]

        # Compute cosine similarity in latent space
        target_vec = self.item_factors[item_idx]
        similarities = cosine_similarity(
            target_vec.reshape(1, -1),
            self.item_factors,
        ).flatten()

        # Set self-similarity to 0
        similarities[item_idx] = 0

        # Get top-N
        top_indices = np.argsort(similarities)[::-1][:top_n]

        results = []
        for idx in top_indices:
            sim = similarities[idx]
            if sim <= 0:
                continue
            similar_item_id = self.ratings_matrix.idx_to_item[idx]
            results.append({
                "item_id": similar_item_id,
                "score": round(float(sim), 6),
            })

        return results


def generate_collaborative_filtering_recommendations(
    top_n: int = 10,
    *,
    data_dir: Path = DATA_DIR,
    method: str = "item_based",
    seed: int | None = None,
) -> Dict[str, List[Dict[str, float]]]:
    """Generate recommendations using collaborative filtering.

    Args:
        top_n: Number of recommendations per target.
        data_dir: Path to the data directory.
        method: One of "user_based", "item_based", or "matrix_factorization".
        seed: Random seed (unused, for API compatibility).

    Returns:
        Dictionary mapping target keys to recommendation lists.
    """
    del seed  # Unused but kept for API compatibility

    if top_n < 1:
        raise ValueError("top_n must be at least 1")

    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    # Load data
    ratings = _load_ratings(data_dir)
    user_ids = _load_identifiers(data_dir / "users.csv", "UserID")
    item_ids = _load_identifiers(data_dir / "items.csv", "Item")

    # Build ratings matrix
    ratings_matrix = RatingsMatrix.from_ratings(ratings, user_ids, item_ids)

    # Initialize the appropriate model
    if method == "user_based":
        model: UserBasedCF | ItemBasedCF | MatrixFactorizationCF = UserBasedCF(
            ratings_matrix=ratings_matrix
        )
    elif method == "item_based":
        model = ItemBasedCF(ratings_matrix=ratings_matrix)
    elif method == "matrix_factorization":
        model = MatrixFactorizationCF(ratings_matrix=ratings_matrix)
    else:
        raise ValueError(f"Unknown method: {method}. Use 'user_based', 'item_based', or 'matrix_factorization'")

    recommendations: Dict[str, List[Dict[str, float]]] = {}

    # Generate user recommendations
    for user_id in user_ids:
        recs = model.recommend_for_user(user_id, top_n=top_n)
        recommendations[f"user_id#{user_id}"] = recs

    # Generate item-to-item recommendations (similar items)
    if hasattr(model, "similar_items"):
        for item_id in item_ids:
            similar = model.similar_items(item_id, top_n=top_n)
            recommendations[f"item_id#{item_id}"] = similar

    return recommendations


# Wrapper functions for different CF methods to match the model registry interface
def generate_user_based_cf_recommendations(
    top_n: int = 10,
    seed: int | None = None,
    data_dir: Path = DATA_DIR,
) -> Dict[str, List[Dict[str, float]]]:
    """Generate recommendations using User-Based Collaborative Filtering."""
    return generate_collaborative_filtering_recommendations(
        top_n=top_n,
        data_dir=data_dir,
        method="user_based",
        seed=seed,
    )


def generate_item_based_cf_recommendations(
    top_n: int = 10,
    seed: int | None = None,
    data_dir: Path = DATA_DIR,
) -> Dict[str, List[Dict[str, float]]]:
    """Generate recommendations using Item-Based Collaborative Filtering."""
    return generate_collaborative_filtering_recommendations(
        top_n=top_n,
        data_dir=data_dir,
        method="item_based",
        seed=seed,
    )


def generate_matrix_factorization_recommendations(
    top_n: int = 10,
    seed: int | None = None,
    data_dir: Path = DATA_DIR,
) -> Dict[str, List[Dict[str, float]]]:
    """Generate recommendations using Matrix Factorization (SVD)."""
    return generate_collaborative_filtering_recommendations(
        top_n=top_n,
        data_dir=data_dir,
        method="matrix_factorization",
        seed=seed,
    )


if __name__ == "__main__":
    print("Testing Collaborative Filtering Recommenders...")
    print("=" * 60)

    # Test User-Based CF
    print("\n1. User-Based Collaborative Filtering:")
    user_based_recs = generate_user_based_cf_recommendations(top_n=5)
    sample_user_keys = [k for k in user_based_recs.keys() if k.startswith("user_id")][:3]
    for key in sample_user_keys:
        print(f"  {key} -> {user_based_recs[key]}")

    # Test Item-Based CF
    print("\n2. Item-Based Collaborative Filtering:")
    item_based_recs = generate_item_based_cf_recommendations(top_n=5)
    sample_item_keys = [k for k in item_based_recs.keys() if k.startswith("item_id")][:3]
    for key in sample_item_keys:
        print(f"  {key} -> {item_based_recs[key]}")

    # Test Matrix Factorization
    print("\n3. Matrix Factorization (SVD):")
    mf_recs = generate_matrix_factorization_recommendations(top_n=5)
    sample_user_keys = [k for k in mf_recs.keys() if k.startswith("user_id")][:3]
    for key in sample_user_keys:
        print(f"  {key} -> {mf_recs[key]}")

    print("\n" + "=" * 60)
    print("Testing complete!")
