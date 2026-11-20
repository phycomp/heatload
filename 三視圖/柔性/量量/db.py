from streamlit import cache_resource, secrets
from psycopg import rows
import streamlit as st
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row


@cache_resource
def get_pool():
    連接=secrets["量量"]["conninfo"]  #postgresql
    print(['連接', 連接])
    return ConnectionPool(
        conninfo=連接, #secrets["postgresql"]["conninfo"],
        min_size=2,
        max_size=10,
        kwargs={"row_factory": dict_row},
        check=ConnectionPool.check_connection,
        open=True,
    )


def query(sql, params=None):
    with get_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()


def execute(sql, params=None):
    with get_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.rowcount


def execute_returning(sql, params=None):
    with get_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()


def write_audit(table_name, row_id, column_name, old_value, new_value, changed_by):
    execute(
        "INSERT INTO audit_log (table_name, row_id, column_name, old_value, new_value, changed_by) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (table_name, row_id, column_name, str(old_value), str(new_value), changed_by),
    )
