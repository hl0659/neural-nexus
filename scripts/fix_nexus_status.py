"""
Fix NEXUS System Status
Recalculates NEXUS status metrics from actual database data
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.database.connection import db_pool

print("="*60)
print("FIX NEXUS SYSTEM STATUS")
print("="*60)

db_pool.initialize()

# Get actual metrics from database
print("\n1. Calculating Actual Metrics:")
with db_pool.get_cursor(commit=False) as cursor:
    # Count matches collected by NEXUS
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM matches
        WHERE collected_by = 'nexus'
    """)
    actual_matches = cursor.fetchone()['count']
    print(f"   Actual NEXUS matches: {actual_matches}")
    
    # Count unique players processed (those with nexus_puuid)
    cursor.execute("""
        SELECT COUNT(DISTINCT (region, game_name, tag_line)) as count
        FROM collection_queues
        WHERE queue_type = 'nexus'
          AND last_attempt IS NOT NULL
    """)
    actual_players = cursor.fetchone()['count']
    print(f"   Actual players processed: {actual_players}")

# Get current status
print("\n2. Current System Status:")
with db_pool.get_cursor(commit=False) as cursor:
    cursor.execute("""
        SELECT players_processed, matches_collected, api_calls_made
        FROM system_status
        WHERE service_name = 'nexus'
    """)
    
    current = cursor.fetchone()
    if current:
        print(f"   Players processed: {current['players_processed']}")
        print(f"   Matches collected: {current['matches_collected']}")
        print(f"   API calls made: {current['api_calls_made']}")

# Update status
print("\n3. Updating Status:")
with db_pool.get_cursor() as cursor:
    cursor.execute("""
        UPDATE system_status
        SET matches_collected = %s,
            last_update = CURRENT_TIMESTAMP
        WHERE service_name = 'nexus'
    """, (actual_matches,))
    
    print(f"   ✓ Updated matches_collected to {actual_matches}")

# Verify
print("\n4. Verification:")
with db_pool.get_cursor(commit=False) as cursor:
    cursor.execute("""
        SELECT *
        FROM system_status
        WHERE service_name = 'nexus'
    """)
    
    status = cursor.fetchone()
    print(f"   Players processed: {status['players_processed']}")
    print(f"   Matches collected: {status['matches_collected']}")
    print(f"   API calls made: {status['api_calls_made']}")
    print(f"   Current phase: {status['current_phase']}")

db_pool.close()

print("\n" + "="*60)
print("STATUS FIX COMPLETE")
print("="*60)