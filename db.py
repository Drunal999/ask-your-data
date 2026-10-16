import random
import sqlite3
from datetime import date, timedelta

REGIONS = ["North", "South", "East", "West"]
SEGMENTS = ["Enterprise", "SMB", "Consumer"]
PRODUCTS = ["Analytics Suite", "Chat Assistant", "Data Connector", "Support Plan"]


def get_conn(path=":memory:", seed=7):
    """Create a small demo sales database (deterministic)."""
    rnd = random.Random(seed)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.executescript("""
        CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT, region TEXT, segment TEXT);
        CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER, product TEXT,
                             amount REAL, status TEXT, order_date TEXT);
    """)
    for i in range(1, 61):
        conn.execute("INSERT INTO customers VALUES (?,?,?,?)",
                     (i, f"Customer {i}", rnd.choice(REGIONS), rnd.choice(SEGMENTS)))
    start = date(2026, 1, 1)
    for i in range(1, 801):
        conn.execute("INSERT INTO orders VALUES (?,?,?,?,?,?)",
                     (i, rnd.randint(1, 60), rnd.choice(PRODUCTS), round(rnd.uniform(50, 2500), 2),
                      rnd.choices(["paid", "refunded", "pending"], [0.85, 0.07, 0.08])[0],
                      (start + timedelta(days=rnd.randint(0, 270))).isoformat()))
    conn.commit()
    return conn
