"""Pipeline for extracting metadata and categories from items."""

from __future__ import annotations

import csv
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "data.db"

# Predefined categories based on item analysis
CATEGORIES = {
    "finance": {
        "name": "Finanças & Economia",
        "description": "Datasets relacionados a finanças, economia, empréstimos e mercado",
        "keywords": ["credit", "loan", "bank", "finance", "economic", "income", "tax", "payroll", "insurance", "lending"],
        "icon": "💰"
    },
    "healthcare": {
        "name": "Saúde & Medicina",
        "description": "Datasets sobre saúde, medicina e diagnósticos",
        "keywords": ["health", "medical", "diabetes", "cancer", "hospital", "appointment", "disease"],
        "icon": "🏥"
    },
    "sports": {
        "name": "Esportes",
        "description": "Datasets sobre esportes e atividades físicas",
        "keywords": ["soccer", "football", "nba", "basketball", "gym", "sport", "game", "fitness"],
        "icon": "⚽"
    },
    "entertainment": {
        "name": "Entretenimento",
        "description": "Filmes, música, games e anime",
        "keywords": ["movie", "video", "music", "streaming", "anime", "game", "imdb", "entertainment"],
        "icon": "🎬"
    },
    "social": {
        "name": "Redes Sociais & Comunicação",
        "description": "Redes sociais, análise de texto e comunicação",
        "keywords": ["social", "twitter", "facebook", "network", "dating", "review", "sentiment"],
        "icon": "💬"
    },
    "government": {
        "name": "Governo & Política",
        "description": "Dados governamentais, eleições e políticas públicas",
        "keywords": ["election", "congress", "government", "census", "political", "vote", "president"],
        "icon": "🏛️"
    },
    "crime": {
        "name": "Segurança & Crime",
        "description": "Estatísticas de crime e segurança pública",
        "keywords": ["crime", "homicide", "murder", "fraud", "police", "security"],
        "icon": "🚔"
    },
    "transportation": {
        "name": "Transporte & Viagens",
        "description": "Transporte, viagens e mobilidade",
        "keywords": ["flight", "airline", "uber", "travel", "transport", "hotel", "reservation"],
        "icon": "✈️"
    },
    "environment": {
        "name": "Meio Ambiente & Clima",
        "description": "Clima, meio ambiente e recursos naturais",
        "keywords": ["climate", "weather", "environment", "temperature", "flood", "oil", "pipeline"],
        "icon": "🌍"
    },
    "business": {
        "name": "Negócios & RH",
        "description": "Recursos humanos, negócios e empresas",
        "keywords": ["hr", "employee", "business", "commerce", "inventory", "management", "attrition"],
        "icon": "💼"
    },
    "education": {
        "name": "Educação",
        "description": "Sistemas educacionais e aprendizado",
        "keywords": ["course", "education", "school", "library", "blackboard", "enrollment"],
        "icon": "📚"
    },
    "science": {
        "name": "Ciência & Pesquisa",
        "description": "Datasets científicos e de pesquisa",
        "keywords": ["iris", "mushroom", "biology", "science", "research", "experiment"],
        "icon": "🔬"
    },
    "technology": {
        "name": "Tecnologia & Dados",
        "description": "Tecnologia, IoT e sistemas de informação",
        "keywords": ["voice", "recognition", "activity", "smartphone", "file", "system", "tech"],
        "icon": "💻"
    },
    "food": {
        "name": "Alimentação",
        "description": "Comida, nutrição e restaurantes",
        "keywords": ["food", "nutrition", "restaurant", "menu", "order"],
        "icon": "🍔"
    },
    "world": {
        "name": "Dados Globais",
        "description": "Indicadores mundiais e dados globais",
        "keywords": ["world", "global", "country", "happiness", "development", "indicator"],
        "icon": "🌐"
    }
}


@dataclass
class ItemMetadata:
    """Metadata extracted from an item."""
    item_id: int
    title: str
    description: str
    categories: List[str]
    primary_category: str


def _normalize_row(row: Dict[str, str | None]) -> Dict[str, str | None]:
    """Normalize CSV row by stripping whitespace from keys and values."""
    return {
        key.strip(): (value.strip() if value else value)
        for key, value in row.items()
        if key
    }


def _categorize_item(title: str, description: str) -> List[str]:
    """Categorize an item based on its title and description."""
    text = f"{title} {description}".lower()
    matched_categories: List[str] = []

    for category_id, category_info in CATEGORIES.items():
        for keyword in category_info["keywords"]:
            if keyword.lower() in text:
                matched_categories.append(category_id)
                break

    return matched_categories if matched_categories else ["technology"]


def extract_item_metadata(data_dir: Path = DATA_DIR) -> List[ItemMetadata]:
    """Extract metadata from all items.

    Args:
        data_dir: Path to the data directory.

    Returns:
        List of ItemMetadata objects.
    """
    csv_path = data_dir / "items_with_images.csv"
    if not csv_path.exists():
        csv_path = data_dir / "items.csv"

    if not csv_path.exists():
        raise FileNotFoundError(f"Items CSV not found in {data_dir}")

    items: List[ItemMetadata] = []

    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw_row in reader:
            if raw_row is None:
                continue
            row = _normalize_row(raw_row)

            item_id_str = row.get("Item")
            if not item_id_str:
                continue

            try:
                item_id = int(item_id_str)
            except ValueError:
                continue

            title = row.get("Title") or ""
            description = row.get("Descriptions") or ""

            categories = _categorize_item(title, description)
            primary_category = categories[0] if categories else "technology"

            items.append(ItemMetadata(
                item_id=item_id,
                title=title,
                description=description,
                categories=categories,
                primary_category=primary_category,
            ))

    return items


def save_categories_to_db(db_path: Path = DB_PATH) -> None:
    """Save categories to the database."""
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                icon TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS item_categories (
                item_id INTEGER NOT NULL,
                category_id TEXT NOT NULL,
                is_primary INTEGER DEFAULT 0,
                PRIMARY KEY (item_id, category_id),
                FOREIGN KEY (item_id) REFERENCES items(id),
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)

        # Insert categories
        for category_id, category_info in CATEGORIES.items():
            conn.execute("""
                INSERT OR REPLACE INTO categories (id, name, description, icon)
                VALUES (?, ?, ?, ?)
            """, (
                category_id,
                category_info["name"],
                category_info["description"],
                category_info["icon"],
            ))

        # Extract and save item metadata
        items = extract_item_metadata(db_path.parent)

        for item in items:
            for idx, category_id in enumerate(item.categories):
                is_primary = 1 if idx == 0 else 0
                conn.execute("""
                    INSERT OR REPLACE INTO item_categories (item_id, category_id, is_primary)
                    VALUES (?, ?, ?)
                """, (item.item_id, category_id, is_primary))

        conn.commit()

    print(f"Saved {len(CATEGORIES)} categories and categorized {len(items)} items")


def get_items_by_category(category_id: str, db_path: Path = DB_PATH) -> List[int]:
    """Get all item IDs for a category.

    Args:
        category_id: The category ID to filter by.
        db_path: Path to the database.

    Returns:
        List of item IDs.
    """
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("""
            SELECT item_id FROM item_categories
            WHERE category_id = ?
        """, (category_id,))
        return [row[0] for row in cursor.fetchall()]


def get_categories_for_item(item_id: int, db_path: Path = DB_PATH) -> List[str]:
    """Get all categories for an item.

    Args:
        item_id: The item ID.
        db_path: Path to the database.

    Returns:
        List of category IDs.
    """
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("""
            SELECT category_id FROM item_categories
            WHERE item_id = ?
            ORDER BY is_primary DESC
        """, (item_id,))
        return [row[0] for row in cursor.fetchall()]


def get_all_categories(db_path: Path = DB_PATH) -> List[Dict]:
    """Get all categories with their metadata.

    Returns:
        List of category dictionaries.
    """
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT c.id, c.name, c.description, c.icon,
                   COUNT(ic.item_id) as item_count
            FROM categories c
            LEFT JOIN item_categories ic ON c.id = ic.category_id
            GROUP BY c.id
            ORDER BY item_count DESC
        """)
        return [dict(row) for row in cursor.fetchall()]


if __name__ == "__main__":
    print("Extracting item metadata and categories...")
    save_categories_to_db()

    print("\nCategories with item counts:")
    for category in get_all_categories():
        print(f"  {category['icon']} {category['name']}: {category['item_count']} items")
