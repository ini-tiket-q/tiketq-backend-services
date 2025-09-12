# flights-service/payment_db_reader.py
import os
from typing import Optional
import psycopg2
from psycopg2 import pool

# Prefer PAYMENT_DB_URL; fall back to POSTGRES_* envs if needed
PAYMENT_DB_URL = os.getenv("PAYMENT_DB_URL")
if not PAYMENT_DB_URL:
    user = os.getenv("POSTGRES_USER", "postgres")
    pwd = os.getenv("POSTGRES_PASSWORD", "postgres")
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")
    db   = os.getenv("POSTGRES_DB", "tiketq_db")
    PAYMENT_DB_URL = f"postgresql://{user}:{pwd}@{host}:{port}/{db}"

_conn_pool: Optional[pool.SimpleConnectionPool] = None

def _pool() -> pool.SimpleConnectionPool:
    global _conn_pool
    if _conn_pool is None:
        _conn_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=5,
            dsn=PAYMENT_DB_URL,
        )
    return _conn_pool

def get_payment_status_by_order_id(order_id: str) -> Optional[str]:
    """
    Returns the latest payment status for an order_id (e.g., 'SUCCESS', 'PENDING', etc),
    or None if not found.
    """
    conn = _pool().getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT status
                FROM payments
                WHERE order_id = %s
                ORDER BY created_at DESC
                LIMIT 1;
                """,
                (order_id,),
            )
            row = cur.fetchone()
            if row:
                return row[0]  # status as string
            return None
    finally:
        _pool().putconn(conn)
