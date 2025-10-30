import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from contextlib import contextmanager
from shared.config.settings import settings

class DatabasePool:
    """PostgreSQL connection pool manager"""
    
    def __init__(self):
        self.pool = None
    
    def initialize(self):
        """Initialize the connection pool"""
        self.pool = ConnectionPool(
            conninfo=settings.DATABASE_URL,
            min_size=5,
            max_size=20,
            kwargs={"row_factory": dict_row}
        )
        print("✅ Database pool initialized")
    
    def close(self):
        """Close the connection pool"""
        if self.pool:
            self.pool.close()
            print("✅ Database pool closed")
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool"""
        conn = self.pool.getconn()
        try:
            yield conn
        finally:
            self.pool.putconn(conn)
    
    @contextmanager
    def get_cursor(self):
        """Get a cursor with automatic commit/rollback"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                cursor.close()

# Global database pool instance
db_pool = DatabasePool()