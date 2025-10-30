"""
Cleanup Stale Match Locks
Removes expired or stuck match locks
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.database.connection import db_pool

print("="*60)
print("MATCH LOCK CLEANUP")
print("="*60)

db_pool.initialize()

# Check current locks
print("\n1. Current Lock Status:")
with db_pool.get_cursor(commit=False) as cursor:
    cursor.execute("""
        SELECT locked_by, COUNT(*) as count,
               COUNT(*) FILTER (WHERE expires_at < NOW()) as expired,
               COUNT(*) FILTER (WHERE expires_at >= NOW()) as active
        FROM match_locks
        GROUP BY locked_by
    """)
    
    results = cursor.fetchall()
    
    if not results:
        print("   No locks found")
    else:
        total_expired = 0
        total_active = 0
        for row in results:
            print(f"   {row['locked_by'].upper()}:")
            print(f"      Total: {row['count']}")
            print(f"      Expired: {row['expired']}")
            print(f"      Active: {row['active']}")
            total_expired += row['expired']
            total_active += row['active']
        
        print(f"\n   TOTAL: {total_expired + total_active} locks")
        print(f"      {total_expired} expired")
        print(f"      {total_active} still active")

# Clean up expired locks
print("\n2. Cleaning Up Expired Locks:")
with db_pool.get_cursor() as cursor:
    cursor.execute("DELETE FROM match_locks WHERE expires_at < NOW()")
    deleted = cursor.rowcount
    print(f"   Deleted {deleted} expired locks")

# Option to clean ALL locks
print("\n3. Clean ALL Locks? (including active ones)")
response = input("   Type 'yes' to delete all locks: ")

if response.lower() == 'yes':
    with db_pool.get_cursor() as cursor:
        cursor.execute("DELETE FROM match_locks")
        deleted = cursor.rowcount
        print(f"   ✓ Deleted all {deleted} locks")
else:
    print("   Skipped - keeping active locks")

# Final status
print("\n4. Final Lock Status:")
with db_pool.get_cursor(commit=False) as cursor:
    cursor.execute("SELECT COUNT(*) as count FROM match_locks")
    count = cursor.fetchone()['count']
    
    if count == 0:
        print("   ✓ No locks remaining")
    else:
        print(f"   {count} locks remaining")

db_pool.close()

print("\n" + "="*60)
print("CLEANUP COMPLETE")
print("="*60)