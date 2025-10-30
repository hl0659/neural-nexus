"""
Neural Nexus v3.0 - Database Maintenance
Automated cleanup and optimization tasks
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.database.connection import db_pool

print("="*60)
print("DATABASE MAINTENANCE")
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*60)

db_pool.initialize()

# 1. Clean expired locks
print("\n1. Cleaning Expired Match Locks:")
with db_pool.get_cursor() as cursor:
    cursor.execute("DELETE FROM match_locks WHERE expires_at < NOW()")
    deleted = cursor.rowcount
    print(f"   ✓ Deleted {deleted} expired locks")

# 2. Reset stuck processing entries
print("\n2. Resetting Stuck Queue Entries:")
with db_pool.get_cursor() as cursor:
    # Reset entries stuck in 'processing' for over 1 hour
    cursor.execute("""
        UPDATE collection_queues
        SET status = 'pending',
            next_check = CURRENT_TIMESTAMP
        WHERE status = 'processing'
          AND last_attempt < CURRENT_TIMESTAMP - INTERVAL '1 hour'
    """)
    reset = cursor.rowcount
    print(f"   ✓ Reset {reset} stuck entries")

# 3. Clean up failed entries (too many attempts)
print("\n3. Removing Failed Queue Entries:")
with db_pool.get_cursor() as cursor:
    cursor.execute("""
        DELETE FROM collection_queues
        WHERE attempts > 5
          AND last_attempt < CURRENT_TIMESTAMP - INTERVAL '24 hours'
    """)
    removed = cursor.rowcount
    print(f"   ✓ Removed {removed} failed entries (>5 attempts)")

# 4. Update queue next_check times for players not checked recently
print("\n4. Refreshing Queue Schedules:")
with db_pool.get_cursor() as cursor:
    # Reset next_check for players that haven't been checked in 48 hours
    cursor.execute("""
        UPDATE collection_queues
        SET next_check = CURRENT_TIMESTAMP
        WHERE status = 'pending'
          AND next_check > CURRENT_TIMESTAMP + INTERVAL '24 hours'
    """)
    refreshed = cursor.rowcount
    print(f"   ✓ Refreshed {refreshed} queue schedules")

# 5. Analyze tables for query optimization
print("\n5. Analyzing Tables:")
with db_pool.get_cursor() as cursor:
    tables = ['players', 'matches', 'match_participants', 'collection_queues']
    for table in tables:
        cursor.execute(f"ANALYZE {table}")
        print(f"   ✓ Analyzed {table}")

# 6. Show statistics
print("\n6. Current Statistics:")
with db_pool.get_cursor(commit=False) as cursor:
    # Queue health
    cursor.execute("""
        SELECT queue_type, status, COUNT(*) as count
        FROM collection_queues
        GROUP BY queue_type, status
        ORDER BY queue_type, status
    """)
    
    print("   Queue Status:")
    for row in cursor.fetchall():
        print(f"      {row['queue_type'].upper()} - {row['status']}: {row['count']}")
    
    # Match locks
    cursor.execute("SELECT COUNT(*) as count FROM match_locks")
    locks = cursor.fetchone()['count']
    print(f"\n   Active Locks: {locks}")
    
    # Recent errors
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM collection_queues
        WHERE last_error IS NOT NULL
          AND last_attempt > NOW() - INTERVAL '1 hour'
    """)
    recent_errors = cursor.fetchone()['count']
    print(f"   Recent Errors (last hour): {recent_errors}")

db_pool.close()

print("\n" + "="*60)
print("MAINTENANCE COMPLETE")
print("="*60)