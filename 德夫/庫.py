# 2. Database Connection Module

"""
Database Connection Module for KPI Ticket Tracking System
Supports PostgreSQL with connection pooling
"""
import os
from psycopg import connect as pgCnnct
#from psycopg.extras import RealDictCursor
from contextlib import contextmanager
import streamlit as st

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'dbname': os.getenv('DB_NAME', 'delft'), #kpi_tracker
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'password')
}

@contextmanager
def get_db_connection():
    """Get database connection with context manager"""
    conn = None
    try:
        conn = pgCnnct(**DB_CONFIG)  #psycopg.connect
        yield conn
    except Exception as e:
        st.error(f"Database connection error: {e}")
        raise
    finally:
        if conn:
            conn.close()

@contextmanager
def get_db_cursor(dict_cursor=False):
    """Get database cursor with context manager"""
    with get_db_connection() as conn:
        #cursor_factory = RealDictCursor if dict_cursor else None
        cur = conn.cursor()#cursor_factory=cursor_factory)
        try:
            yield cur
            conn.commit()
        except Exception as e:
            conn.rollback()
            st.error(f"Database query error: {e}")
            raise
        finally:
            cur.close()

def init_database():
    """Initialize database with schema"""
    schema_path = os.path.join(os.path.dirname(__file__), 'sql', 'schema.sql')
    if os.path.exists(schema_path):
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(schema_sql)
            conn.commit()
        return True
    return False
