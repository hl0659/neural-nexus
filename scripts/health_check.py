"""
Neural Nexus v3.0 - Health Check
Quick system health check - can run while collection is active
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.database.connection import db_pool
from shared.config.settings import settings

print("="*60)
print("NEURAL NEXUS HEALTH CHECK")
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*60)

db_pool.initialize()

# 1. Database Connection
print("\n1. Database Connection:")
try:
    if db_pool.test_connection():
        print("   ✓ Connected")
    else:
        print("   ❌ Failed")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 2. API Keys
print("\n2. API Keys:")
print(f"   APEX: {'✓ Configured' if settings.RIOT_API_KEY_APEX else '❌ Missing'}")
print(f"   NEXUS: {'✓ Configured' if settings.RIOT_API_KEY_NEXUS else '❌ Missing'}")

# 3. Service Status
print("\n3. Service Status:")
with db_pool.get_cursor(commit=False) as cursor:
    cursor.execute("SELECT * FROM system_status")
    
    for row in cursor.fetchall():
        status_icon = "🟢" if row['is_active'] else "⚪"
        print(f"   {status_icon} {row['service_name'].upper()}: {row['current_phase']}")
        if row['is_active']:
            print(f"      Players: {row['players_processed']}")
            print(f"      Matches: {row['matches_collected']}")
            if row['last_update']:
                time_since = datetime.now() - row['last_update']
                print(f"      Last update: {int(time_since.total_seconds())}s ago")

# 4. Queue Depths
print("\n4. Queue Depths:")
with db_pool.get_cursor(commit=False) as cursor:
    cursor.execute("""
        SELECT queue_type, status, COUNT(*) as count
        FROM collection_queues
        GROUP BY queue_type, status
        ORDER BY queue_type, status
    """)
    
    current_queue = None
    for row in cursor.fetchall():
        if row['queue_type'] != current_queue:
            current_queue = row['queue_type']
            print(f"   {current_queue.upper()}:")
        print(f"      {row['status']}: {row['count']}")

# 5. Recent Activity (last 5 minutes)
print("\n5. Recent Activity (last 5 minutes):")
with db_pool.get_cursor(commit=False) as cursor:
    five_min_ago = datetime.now() - timedelta(minutes=5)
    
    cursor.execute("""
        SELECT collected_by, COUNT(*) as count
        FROM matches
        WHERE collected_at > %s
        GROUP BY collected_by
    """, (five_min_ago,))
    
    results = cursor.fetchall()
    if results:
        for row in results:
            print(f"   {row['collected_by'].upper()}: {row['count']} matches")
    else:
        print("   No recent activity")

# 6. Match Locks
print("\n6. Match Locks:")
with db_pool.get_cursor(commit=False) as cursor:
    cursor.execute("""
        SELECT locked_by, 
               COUNT(*) as total,
               COUNT(*) FILTER (WHERE expires_at < NOW()) as expired
        FROM match_locks
        GROUP BY locked_by
    """)
    
    results = cursor.fetchall()
    if results:
        for row in results:
            print(f"   {row['locked_by'].upper()}: {row['total']} ({row['expired']} expired)")
    else:
        print("   No active locks")

# 7. Storage
print("\n7. Storage:")
try:
    data_path = settings.DATA_PATH
    if data_path.exists():
        print(f"   ✓ Data directory exists: {data_path}")
        
        # Count files
        match_count = len(list((data_path / 'matches').rglob('*.json.gz')))
        timeline_count = len(list((data_path / 'timelines').rglob('*.json.gz')))
        
        print(f"   Match files: {match_count}")
        print(f"   Timeline files: {timeline_count}")
    else:
        print(f"   ❌ Data directory not found: {data_path}")
except Exception as e:
    print(f"   ⚠️  Could not check storage: {e}")

# 8. Database Stats
print("\n8. Database Stats:")
with db_pool.get_cursor(commit=False) as cursor:
    cursor.execute("SELECT COUNT(*) as count FROM players")
    player_count = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM matches")
    match_count = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM match_participants")
    participant_count = cursor.fetchone()['count']
    
    print(f"   Players: {player_count:,}")
    print(f"   Matches: {match_count:,}")
    print(f"   Participants: {participant_count:,}")

db_pool.close()

print("\n" + "="*60)
print("HEALTH CHECK COMPLETE")
print("="*60)