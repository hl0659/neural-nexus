"""
Neural Nexus v3.0 - Match Locking System
Prevents both APEX and NEXUS from collecting the same match
"""

from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from shared.database.connection import db_pool


class MatchLockManager:
    """Database-backed match locking to coordinate APEX and NEXUS"""
    
    @staticmethod
    def try_acquire(match_id: str, service: str) -> bool:
        """
        Try to acquire lock for a match
        
        Args:
            match_id: Match ID to lock
            service: 'apex' or 'nexus'
        
        Returns:
            True if lock acquired, False if already locked
        """
        try:
            with db_pool.get_cursor() as cursor:
                # Check if already locked and not expired
                cursor.execute("""
                    SELECT locked_by, expires_at 
                    FROM match_locks 
                    WHERE match_id = %s
                """, (match_id,))
                
                result = cursor.fetchone()
                
                if result:
                    # Check if expired
                    if result['expires_at'] < datetime.now():
                        # Expired - delete and re-acquire
                        cursor.execute("DELETE FROM match_locks WHERE match_id = %s", (match_id,))
                    else:
                        # Still locked by another service
                        return False
                
                # Try to acquire lock
                cursor.execute("""
                    INSERT INTO match_locks (match_id, locked_by, expires_at)
                    VALUES (%s, %s, NOW() + INTERVAL '1 hour')
                    ON CONFLICT (match_id) DO NOTHING
                    RETURNING match_id
                """, (match_id, service))
                
                # Check if we got the lock
                acquired = cursor.fetchone() is not None
                return acquired
        
        except Exception as e:
            print(f"❌ Failed to acquire lock for {match_id}: {e}")
            return False
    
    @staticmethod
    def release(match_id: str):
        """
        Release lock after successful collection
        
        Args:
            match_id: Match ID to unlock
        """
        try:
            with db_pool.get_cursor() as cursor:
                cursor.execute("DELETE FROM match_locks WHERE match_id = %s", (match_id,))
        except Exception as e:
            print(f"❌ Failed to release lock for {match_id}: {e}")
    
    @staticmethod
    def cleanup_expired():
        """Remove expired locks (run periodically)"""
        try:
            with db_pool.get_cursor() as cursor:
                cursor.execute("DELETE FROM match_locks WHERE expires_at < NOW()")
                deleted = cursor.rowcount
                
                if deleted > 0:
                    print(f"🧹 Cleaned up {deleted} expired match locks")
                
                return deleted
        except Exception as e:
            print(f"❌ Failed to cleanup expired locks: {e}")
            return 0
    
    @staticmethod
    def get_active_locks() -> int:
        """Get count of active locks"""
        try:
            with db_pool.get_cursor(commit=False) as cursor:
                cursor.execute("SELECT COUNT(*) as count FROM match_locks WHERE expires_at > NOW()")
                result = cursor.fetchone()
                return result['count'] if result else 0
        except Exception as e:
            print(f"❌ Failed to get active locks: {e}")
            return 0
    
    @staticmethod
    def get_locks_by_service(service: str) -> int:
        """Get count of locks held by a specific service"""
        try:
            with db_pool.get_cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT COUNT(*) as count 
                    FROM match_locks 
                    WHERE locked_by = %s AND expires_at > NOW()
                """, (service,))
                result = cursor.fetchone()
                return result['count'] if result else 0
        except Exception as e:
            print(f"❌ Failed to get locks for {service}: {e}")
            return 0


# Global match lock manager
match_lock = MatchLockManager()


if __name__ == "__main__":
    # Test match locking
    print("Testing Match Lock Manager...")
    print("="*60)
    
    db_pool.initialize()
    
    test_match_id = "NA1_TEST_12345"
    
    # Test 1: Acquire lock
    print("\nTest 1: APEX tries to acquire lock...")
    if match_lock.try_acquire(test_match_id, 'apex'):
        print(f"✅ APEX acquired lock for {test_match_id}")
    else:
        print(f"❌ APEX failed to acquire lock")
    
    # Test 2: NEXUS tries to acquire same lock
    print("\nTest 2: NEXUS tries to acquire same lock...")
    if match_lock.try_acquire(test_match_id, 'nexus'):
        print(f"❌ NEXUS should NOT have acquired lock (APEX has it)")
    else:
        print(f"✅ NEXUS correctly blocked (APEX has lock)")
    
    # Test 3: Check active locks
    print("\nTest 3: Check active locks...")
    active = match_lock.get_active_locks()
    apex_locks = match_lock.get_locks_by_service('apex')
    nexus_locks = match_lock.get_locks_by_service('nexus')
    print(f"  Total active locks: {active}")
    print(f"  APEX locks: {apex_locks}")
    print(f"  NEXUS locks: {nexus_locks}")
    
    # Test 4: Release lock
    print("\nTest 4: APEX releases lock...")
    match_lock.release(test_match_id)
    print(f"✅ Lock released")
    
    # Test 5: NEXUS tries again
    print("\nTest 5: NEXUS tries to acquire after release...")
    if match_lock.try_acquire(test_match_id, 'nexus'):
        print(f"✅ NEXUS acquired lock for {test_match_id}")
    else:
        print(f"❌ NEXUS failed to acquire lock")
    
    # Cleanup test lock
    match_lock.release(test_match_id)
    
    db_pool.close()
    
    print("\n✅ Match lock tests complete!")