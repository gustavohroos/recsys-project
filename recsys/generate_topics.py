import sqlite3
import pandas as pd
from bertopic import BERTopic
from umap import UMAP
from hdbscan import HDBSCAN
from sentence_transformers import SentenceTransformer
from pathlib import Path
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction import text
from bertopic.representation import KeyBERTInspired
import numpy as np
import random
import torch

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)


TABLE_NAME = "items"
COLUMN_TEXT = "description"
DB_PATH = Path(__file__).resolve().parent.parent / "data/data.db"
NEW_TABLE_NAME = f"{TABLE_NAME}_topics"


def load_data(db_path: Path, table: str, column: str) -> pd.DataFrame:
    with sqlite3.connect(db_path) as conn:
        query = f"SELECT * FROM {table} WHERE {column} IS NOT NULL"
        df = pd.read_sql_query(query, conn)
    return df


def preprocess_text(s: str) -> str:
    s = s.lower()
    s = s.strip()
    s = " ".join(s.split())
    return s


def build_topic_model() -> BERTopic:
    stop_words = list(text.ENGLISH_STOP_WORDS)
    stop_words.extend(["dataset", "datasets", "data", "database", "project", "features", "contains", "kaggle", "provided"])

    vectorizer_model = CountVectorizer(
        stop_words=stop_words,
        ngram_range=(1, 3),     # ↑ melhora qualidade das frases
        min_df=2                # remove palavras raras sem sentido
    )
    
    representation_model = KeyBERTInspired()
    # embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    # embedding_model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
    embedding_model = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")


    umap_model = UMAP(
        n_neighbors=8,
        n_components=5,
        min_dist=0.1,
        metric="cosine",
        random_state=SEED
    )

    hdbscan_model = HDBSCAN(
        min_cluster_size=3,
        min_samples=1,
        metric="euclidean",
        # cluster_selection_method="eom",
        cluster_selection_method="leaf",
        prediction_data=True
    )

    topic_model = BERTopic(
        embedding_model=embedding_model,
        umap_model=umap_model,
        hdbscan_model=hdbscan_model,
        vectorizer_model=vectorizer_model,
        representation_model=representation_model,
        language="english",
        verbose=False 
    )

    return topic_model


def save_results(df: pd.DataFrame, db_path: Path, table: str) -> None:
    with sqlite3.connect(db_path) as conn:
        df.to_sql(table, conn, if_exists="replace", index=False)


def main() -> None:
    df = load_data(DB_PATH, TABLE_NAME, COLUMN_TEXT)

    df["clean_text"] = df[COLUMN_TEXT].apply(preprocess_text)

    topic_model = build_topic_model()

    topics, probs = topic_model.fit_transform(df["clean_text"].tolist())

    df["topic"] = topics

    info = topic_model.get_topic_info()
    mapping = dict(zip(info["Topic"], info["Name"]))
    df["topic_name"] = df["topic"].map(mapping)

    save_results(df, DB_PATH, NEW_TABLE_NAME)

    # topic_model.save("bertopic_model")


if __name__ == "__main__":
    main()