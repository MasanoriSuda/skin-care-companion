from __future__ import annotations

import sqlite3

from app.models import Concern, ProductRecord


class SQLiteRetriever:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def retrieve_products(
        self,
        query: str,
        concerns: list[Concern],
        budget_yen: int,
        limit: int = 8,
    ) -> list[ProductRecord]:
        terms = [concern.value for concern in concerns]
        if query:
            terms.extend(token for token in query.replace("、", " ").split() if token)

        rows: list[sqlite3.Row] = []
        if terms:
            fts_query = " OR ".join(_quote_fts(term) for term in terms)
            try:
                rows = self._conn.execute(
                    """
                    SELECT p.*
                    FROM product_fts f
                    JOIN products p ON p.product_id = f.product_id
                    WHERE product_fts MATCH ?
                    LIMIT ?
                    """,
                    (fts_query, limit),
                ).fetchall()
            except sqlite3.OperationalError:
                rows = []

        if not rows:
            rows = self._conn.execute(
                "SELECT * FROM products ORDER BY price_yen ASC LIMIT ?",
                (limit,),
            ).fetchall()

        records = [_row_to_product(row) for row in rows]
        if budget_yen > 0:
            records.sort(key=lambda product: (product.price_yen > budget_yen, product.price_yen))
        return records[:limit]

    def retrieve_memos(self, concerns: list[Concern], limit: int = 3) -> list[str]:
        labels = [concern.value for concern in concerns]
        if not labels:
            rows = self._conn.execute(
                "SELECT title, body FROM beauty_memos LIMIT ?",
                (limit,),
            ).fetchall()
        else:
            clauses = " OR ".join("concerns LIKE ?" for _ in labels)
            rows = self._conn.execute(
                f"SELECT title, body FROM beauty_memos WHERE {clauses} LIMIT ?",
                [f"%{label}%" for label in labels] + [limit],
            ).fetchall()
        return [f"{row['title']}: {row['body']}" for row in rows]


def _row_to_product(row: sqlite3.Row) -> ProductRecord:
    return ProductRecord(
        product_id=row["product_id"],
        name=row["name"],
        brand=row["brand"],
        category=row["category"],
        price_yen=row["price_yen"],
        concerns=[item for item in row["concerns"].split(",") if item],
        tags=[item for item in row["tags"].split(",") if item],
        description=row["description"],
    )


def _quote_fts(term: str) -> str:
    cleaned = term.replace('"', "").strip()
    return f'"{cleaned}"' if cleaned else '""'

