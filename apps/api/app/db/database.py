from pathlib import Path
import sqlite3


DB_DIR = Path(__file__).resolve().parent


def connect(database_path: Path) -> sqlite3.Connection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(database_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(database_path: Path) -> None:
    with connect(database_path) as conn:
        conn.executescript((DB_DIR / "schema.sql").read_text(encoding="utf-8"))
        conn.executescript((DB_DIR / "seed.sql").read_text(encoding="utf-8"))
        refresh_product_fts(conn)
        conn.commit()


def refresh_product_fts(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM product_fts")
    conn.execute(
        """
        INSERT INTO product_fts(product_id, name, brand, category, concerns, tags, description)
        SELECT product_id, name, brand, category, concerns, tags, description
        FROM products
        """
    )

