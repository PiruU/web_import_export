import sqlite3, pathlib, typing

from .purchase import Purchase

def create_purchase_scheme(connexion: sqlite3.Connection) -> None:
    connexion.executescript("""
    CREATE TABLE IF NOT EXISTS purchases (
        id          TEXT    PRIMARY KEY,
        customer_id INTEGER NOT NULL,
        product_id  INTEGER NOT NULL,
        quantity    INT     NOT NULL CHECK (quantity > 0),
        price       REAL    NOT NULL CHECK (price >= 0),
        currency    TEXT    NOT NULL,
        date        TEXT    NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS ix_purchases_customer ON purchases(customer_id);
    CREATE INDEX IF NOT EXISTS ix_purchases_date     ON purchases(date);
    """)
    connexion.commit()

def _upsert_purchase(cursor: sqlite3.Cursor, purchase: Purchase) -> None:
    sql = """
    INSERT INTO purchases (id, customer_id, product_id, quantity, price, currency, date)
    VALUES(?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
        customer_id = excluded.customer_id,
        product_id  = excluded.product_id,
        quantity    = excluded.quantity,
        price       = excluded.price,
        currency    = excluded.currency,
        date        = excluded.date
    """
    cursor.execute(sql, (
        purchase.purchase_id,
        purchase.customer_id,
        purchase.product_id,
        purchase.quantity,
        purchase.price,
        purchase.currency,
        purchase.date
    ))

def upsert_purchases(connexion: sqlite3.Connection, purchases: typing.List[Purchase]) -> int:
    cursor, count = connexion.cursor(), 0
    for purchase in purchases:
        _upsert_purchase(cursor, purchase)
        count += 1
    connexion.commit()
    return count