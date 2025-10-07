import sqlite3, pathlib, typing

from .customer import Customer

def create_customer_scheme(connexion: sqlite3.Connection) -> None:
    connexion.executescript("""
    CREATE TABLE IF NOT EXISTS customers (
        id          INTEGER PRIMARY KEY,
        title       INTEGER,
        lastname    TEXT,
        firstname   TEXT,
        zipcode     TEXT,
        city        TEXT,
        email       TEXT
    );
    """)
    connexion.commit()

def _none_if_empty(v: str) -> str | None:
    return None if isinstance(v, str) and v == "" else v

def _upsert_customer(cursor: sqlite3.Cursor, customer: Customer) -> None:
    sql = """
    INSERT INTO customers (id, title, lastname, firstname, zipcode, city, email)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
        title     = excluded.title,
        lastname  = excluded.lastname,
        firstname = excluded.firstname,
        zipcode   = excluded.zipcode,
        city      = excluded.city,
        email     = excluded.email
    """
    cursor.execute(sql, (
        customer.customer_id,
        _none_if_empty(customer.title),
        _none_if_empty(customer.lastname),
        _none_if_empty(customer.firstname),
        _none_if_empty(customer.postal_code),
        _none_if_empty(customer.city),
        _none_if_empty(customer.email)
    ))

def upsert_customers(connexion: sqlite3.Connection, customers: typing.List[Customer]) -> int:
    cursor, count = connexion.cursor(), 0
    for customer in customers:
        _upsert_customer(cursor, customer)
        count += 1
    connexion.commit()
    return count