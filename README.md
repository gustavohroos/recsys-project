# Recsys Project

This repository contains a minimal recommender-system stack used for experimentation. It provides a FastAPI backend backed by a SQLite database, plus simple scripts for loading CSV datasets and generating baseline recommendations.

## Features

- SQLite database creation from the raw CSV exports using `data/create_db.py`.
- FastAPI service (`api/main.py`) exposing REST endpoints for users, items, groups, ratings, and stored recommendations.
- Multiple recommendation algorithms:
  - **Random baseline** (`recsys/random_model.py`) - Random recommendations for sanity checks.
  - **Item similarity** (`recsys/item_similarity.py`) - Content-based recommendations using sentence embeddings.
  - **Collaborative filtering** (`recsys/collaborative_filtering.py`) - Three approaches:
    - **User-Based CF**: Finds similar users based on rating patterns and recommends items liked by similar users.
    - **Item-Based CF**: Finds similar items based on user rating patterns and recommends items similar to those the user liked.
    - **Matrix Factorization (SVD)**: Decomposes the user-item matrix into latent factors for predictions.
- CORS-enabled API so it can be consumed directly from web clients during demos.

## Project Structure

```
api/           # FastAPI application
data/          # Raw CSVs and generated SQLite database
recsys/        # Notebooks and experimentation scripts
recsys-front/  # Vite + React frontend
```

## Prerequisites

- Python 3.13 (a virtual environment is recommended)
- `pip` for dependency installation

## Setup Instructions

1. **Clone the repository and enter the project directory.**

   ```bash
   git clone https://github.com/gustavohroos/recsys-project.git
   cd recsys-project
   ```

2. **Create and activate a virtual environment (optional but recommended).**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   .venv\Scripts\activate # Windows
   ```

3. **Install backend dependencies.**

   ```bash
   pip install -r recsys/requirements.txt
   pip install -r api/requirements.txt
   ```

4. **Create the SQLite database.**

   ```bash
   python data/create_db.py
   ```

5. **Generate recommendations (optional but useful for testing).**

   ```bash
   # Generate random and item similarity recommendations
   python recsys/generate_recommendations.py --models random item_similarity --top-n 10 --seed 42

   # Generate collaborative filtering recommendations
   python recsys/generate_recommendations.py --models user_based_cf item_based_cf matrix_factorization --top-n 10 --seed 42

   # Generate all available models at once
   python recsys/generate_recommendations.py --models random item_similarity user_based_cf item_based_cf matrix_factorization --top-n 10 --seed 42
   ```

6. **Run the FastAPI server.**

   ```bash
   uvicorn api.main:app --reload
   ```

   The API will be available at `http://127.0.0.1:8000`. Interactive documentation is accessible at `http://127.0.0.1:8000/docs`.

7. **Install and run the frontend.**

   ```bash
   cd recsys-front
   npm install
   npm run dev
   ```

   By default the frontend runs at `http://127.0.0.1:5173` and proxies API requests to the FastAPI backend.

> Tip: you can also use the Makefile helpers, for example `make setup`, `make create-db`, `make run-api`, and `make run-front`.

## API Highlights

- `GET /api/items?ids=1,2,3` – fetch metadata for specific items (or all items if `ids` is omitted).
- `GET /api/users/{user_id}` – retrieve a single user profile.
- `GET /api/recommendations?user_id=1000&model=random` – fetch stored recommendations for a user (supports `item_id` and result limiting via `limit`).
- Frontend served locally at `http://127.0.0.1:5173`, consuming the same API.

## Development Notes

- All SQLite interactions happen via the `data/data.db` file. Delete it and rerun `data/create_db.py` if you need a reset.
- The `recsys` folder is intended for experimentation (notebooks, prototype models). Keep production adapters inside the API directory.
- When adding new models, register them in `recsys/generate_recommendations.py` so they can populate the database through the shared script.
- The `recsys-front` app is scaffolded with Vite + React. Use `npm run dev` for local development and `npm run build` to produce optimized bundles.
