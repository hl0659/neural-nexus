"""
Neural Nexus v3.0 - Database Connection Pool
Provides connection pooling and context managers for database operations
"""

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared.config.settings import settings


class DatabasePool:
    """PostgreSQL connection pool manager"""
    
    def __init__(self):
        self._pool: Optional[pool.SimpleConnectionPool] = None
    
    def initialize(self, minconn: int = 1, maxconn: int = 10):
        """Initialize the connection pool"""
        if self._pool is not None:
            print("⚠️  Database pool already initialized")
            return
        
        try:
            self._pool = psycopg2.pool.SimpleConnectionPool(
                minconn,
                maxconn,
                settings.DATABASE_URL,
                cursor_factory=RealDictCursor
            )
            print(f"✅ Database pool initialized ({minconn}-{maxconn} connections)")
        except Exception as e:
            print(f"❌ Failed to initialize database pool: {e}")
            raise
    
    def get_connection(self):
        """Get a connection from the pool"""
        if self._pool is None:
            raise RuntimeError("Database pool not initialized. Call initialize() first.")
        
        try:
            return self._pool.getconn()
        except Exception as e:
            print(f"❌ Failed to get connection from pool: {e}")
            raise
    
    def return_connection(self, conn):
        """Return a connection to the pool"""
        if self._pool is None:
            return
        
        try:
            self._pool.putconn(conn)
        except Exception as e:
            print(f"❌ Failed to return connection to pool: {e}")
    
    @contextmanager
    def get_cursor(self, commit: bool = True):
        """
        Context manager for database operations
        
        Usage:
            with db_pool.get_cursor() as cursor:
                cursor.execute("SELECT * FROM players")
                results = cursor.fetchall()
        
        Args:
            commit: Whether to commit the transaction (default: True)
        """
        conn = None
        cursor = None
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            yield cursor
            
            if commit:
                conn.commit()
        
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.return_connection(conn)
    
    def close(self):
        """Close all connections in the pool"""
        if self._pool is not None:
            self._pool.closeall()
            print("✅ Database pool closed")
            self._pool = None
    
    def test_connection(self) -> bool:
        """Test database connectivity"""
        try:
            with self.get_cursor(commit=False) as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return result is not None
        except Exception as e:
            print(f"❌ Database connection test failed: {e}")
            return False


# Global database pool instance
db_pool = DatabasePool()


if __name__ == "__main__":
    # Test database connection
    print("Testing database connection...")
    
    db_pool.initialize()
    
    if db_pool.test_connection():
        print("✅ Database connection successful!")
        
        # Test query
        with db_pool.get_cursor(commit=False) as cursor:
            cursor.execute("SELECT * FROM system_status")
            results = cursor.fetchall()
            
            print(f"\nSystem Status ({len(results)} services):")
            for row in results:
                print(f"  - {row['service_name']}: {row['current_phase']} ({'Active' if row['is_active'] else 'Inactive'})")
    else:
        print("❌ Database connection failed!")
    
    db_pool.close()