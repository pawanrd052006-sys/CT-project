"""
database.py - SQLite Database Layer
=====================================
Handles persistent storage of products and blockchain state.
Products are stored in SQLite so data survives server restarts.
The blockchain is rebuilt from the database on each startup.
"""

import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "dataset", "products.db")


def get_connection():
    """Return a SQLite connection with row factory for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist yet."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_connection()
    cur = conn.cursor()

    # Products table — stores all product metadata
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id  TEXT UNIQUE NOT NULL,
            name        TEXT NOT NULL,
            manufacturer TEXT NOT NULL,
            category    TEXT NOT NULL,
            date_added  TEXT NOT NULL,
            block_index INTEGER NOT NULL,
            block_hash  TEXT NOT NULL,
            prev_hash   TEXT NOT NULL,
            timestamp   TEXT NOT NULL,
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Activity log — recent actions for the dashboard
    cur.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            action      TEXT NOT NULL,
            details     TEXT NOT NULL,
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def save_product(product_data, block):
    """
    Save a product and its associated blockchain block info to the database.
    Called immediately after a block is added to the blockchain.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO products 
                (product_id, name, manufacturer, category, date_added, 
                 block_index, block_hash, prev_hash, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            product_data["product_id"],
            product_data["name"],
            product_data["manufacturer"],
            product_data["category"],
            product_data["date_added"],
            block.index,
            block.hash,
            block.previous_hash,
            block.timestamp
        ))

        # Log the activity
        cur.execute("""
            INSERT INTO activity_log (action, details)
            VALUES (?, ?)
        """, ("ADD_PRODUCT", f"Added product '{product_data['name']}' (ID: {product_data['product_id']})"))

        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False   # Duplicate product_id
    finally:
        conn.close()


def get_all_products():
    """Return all products ordered by most recently added."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_product_by_id(product_id):
    """Fetch a single product by its product_id."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE product_id = ?", (product_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def delete_product(product_id):
    """Remove a product from the database."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
    cur.execute("""
        INSERT INTO activity_log (action, details)
        VALUES (?, ?)
    """, ("DELETE_PRODUCT", f"Deleted product ID: {product_id}"))
    conn.commit()
    affected = cur.rowcount
    conn.close()
    return affected > 0


def get_stats():
    """Return summary statistics for the dashboard."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as total FROM products")
    total = cur.fetchone()["total"]
    cur.execute("SELECT COUNT(DISTINCT category) as cats FROM products")
    cats = cur.fetchone()["cats"]
    cur.execute("SELECT COUNT(DISTINCT manufacturer) as mfrs FROM products")
    mfrs = cur.fetchone()["mfrs"]
    conn.close()
    return {"total_products": total, "categories": cats, "manufacturers": mfrs}


def get_recent_activity(limit=10):
    """Return the most recent activity log entries."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM activity_log ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def log_verification(product_id, result):
    """Log a verification attempt."""
    conn = get_connection()
    cur = conn.cursor()
    status = "GENUINE" if result else "FAKE/NOT FOUND"
    cur.execute("""
        INSERT INTO activity_log (action, details)
        VALUES (?, ?)
    """, ("VERIFY", f"Verified product ID: {product_id} — Result: {status}"))
    conn.commit()
    conn.close()


def search_products(query):
    """Search products by name, product_id, manufacturer, or category."""
    conn = get_connection()
    cur = conn.cursor()
    like = f"%{query}%"
    cur.execute("""
        SELECT * FROM products
        WHERE name LIKE ? OR product_id LIKE ? OR manufacturer LIKE ? OR category LIKE ?
        ORDER BY id DESC
    """, (like, like, like, like))
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def rebuild_blockchain_data():
    """
    Load all products from DB ordered by block_index.
    Used to re-populate the blockchain object on server restart.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products ORDER BY block_index ASC")
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]
