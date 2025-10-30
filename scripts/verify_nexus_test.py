"""
NEXUS Test Verification
Verifies the NEXUS service test worked correctly
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.database.connection import db_pool

print("="*60)
print("NEXUS TEST VERIFICATION")
print("="*60)

db_pool.initialize()

# Test 1: Check NEXUS matches collected
print("\n1. NEXUS Matches Collected:")
with db_pool.get_cursor(commit=False) as cursor:
    cursor.execute("""
        SELECT region, COUNT(*) as count
        FROM matches
        WHERE collected_by = 'nexus'
        GROUP BY region
    """)
    
    total = 0
    for row in cursor.fetchall():
        print(f"   {row['region'].upper()}: {row['count']} matches")
        total += row['count']
    
    print(f"   TOTAL: {total} matches")
    
    if total == 0:
        print("   ❌ No NEXUS matches collected!")
    else:
        print(f"   ✓ NEXUS collection working")

# Test 2: Check PUUID resolution
print("\n2. PUUID Resolution (apex_puuid → nexus_puuid):")
with db_pool.get_cursor(commit=False) as cursor:
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM players
        WHERE nexus_puuid IS NOT NULL
    """)
    
    count = cursor.fetchone()['count']
    print(f"   Players with nexus_puuid: {count}")
    
    if count == 0:
        print("   ❌ PUUID resolution not working!")
    else:
        print(f"   ✓ PUUID resolution working")

# Test 3: Check for duplicate matches
print("\n3. Duplicate Match Check:")
with db_pool.get_cursor(commit=False) as cursor:
    cursor.execute("""
        SELECT match_id, COUNT(*) as times
        FROM matches
        GROUP BY match_id
        HAVING COUNT(*) > 1
    """)
    
    duplicates = cursor.fetchall()
    
    if duplicates:
        print(f"   ❌ Found {len(duplicates)} duplicate matches!")
        for dup in duplicates[:5]:
            print(f"      {dup['match_id']} collected {dup['times']} times")
    else:
        print("   ✓ No duplicate matches (match locks working)")

# Test 4: Check participant processing
print("\n4. Participant Processing:")
with db_pool.get_cursor(commit=False) as cursor:
    # Get sample NEXUS match
    cursor.execute("""
        SELECT match_id 
        FROM matches 
        WHERE collected_by = 'nexus' 
        LIMIT 1
    """)
    
    match = cursor.fetchone()
    
    if match:
        match_id = match['match_id']
        
        # Count participants
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM match_participants
            WHERE match_id = %s
        """, (match_id,))
        
        participant_count = cursor.fetchone()['count']
        print(f"   Sample match {match_id}:")
        print(f"   Participants extracted: {participant_count}/10")
        
        if participant_count == 10:
            print("   ✓ Participant extraction working")
        else:
            print(f"   ⚠️  Expected 10 participants, found {participant_count}")
    else:
        print("   ⚠️  No NEXUS matches to check")

# Test 5: Check queue routing (Challenger/GM → APEX, others → NEXUS)
print("\n5. Queue Routing by Tier:")
with db_pool.get_cursor(commit=False) as cursor:
    cursor.execute("""
        SELECT 
            cq.queue_type,
            COUNT(*) FILTER (WHERE p.tier IN ('CHALLENGER', 'GRANDMASTER')) as high_elo,
            COUNT(*) FILTER (WHERE p.tier NOT IN ('CHALLENGER', 'GRANDMASTER', 'UNRANKED')) as low_elo,
            COUNT(*) FILTER (WHERE p.tier = 'UNRANKED') as unranked
        FROM collection_queues cq
        JOIN players p ON (
            cq.region = p.region AND 
            cq.game_name = p.game_name AND 
            cq.tag_line = p.tag_line
        )
        GROUP BY cq.queue_type
    """)
    
    routing_correct = True
    for row in cursor.fetchall():
        queue = row['queue_type'].upper()
        print(f"   {queue} Queue:")
        print(f"      Challenger/GM: {row['high_elo']}")
        print(f"      Other ranks: {row['low_elo']}")
        print(f"      Unranked: {row['unranked']}")
        
        # APEX should only have high elo
        if queue == 'APEX' and row['low_elo'] > 0:
            print(f"      ❌ APEX has {row['low_elo']} non-high-elo players!")
            routing_correct = False
        
        # NEXUS should primarily have low elo
        if queue == 'NEXUS' and row['low_elo'] == 0 and row['unranked'] == 0:
            print(f"      ❌ NEXUS has no low-elo players!")
            routing_correct = False
    
    if routing_correct:
        print("   ✓ Queue routing working correctly")

# Test 6: Check match locks
print("\n6. Match Lock Status:")
with db_pool.get_cursor(commit=False) as cursor:
    cursor.execute("""
        SELECT locked_by, COUNT(*) as count
        FROM match_locks
        GROUP BY locked_by
    """)
    
    locks = cursor.fetchall()
    
    if locks:
        print("   Active locks:")
        for lock in locks:
            print(f"      {lock['locked_by'].upper()}: {lock['count']}")
        print("   ⚠️  Locks still active (may be stale)")
    else:
        print("   ✓ No active locks (all released properly)")

# Test 7: System status
print("\n7. NEXUS System Status:")
with db_pool.get_cursor(commit=False) as cursor:
    cursor.execute("""
        SELECT *
        FROM system_status
        WHERE service_name = 'nexus'
    """)
    
    status = cursor.fetchone()
    
    if status:
        print(f"   Current phase: {status['current_phase']}")
        print(f"   Players processed: {status['players_processed']}")
        print(f"   Matches collected: {status['matches_collected']}")
        print(f"   API calls made: {status['api_calls_made']}")
        print(f"   Errors: {status['errors_encountered']}")
        
        if status['matches_collected'] > 0:
            print("   ✓ Status tracking working")
        else:
            print("   ⚠️  Status shows 0 matches collected")

db_pool.close()

print("\n" + "="*60)
print("VERIFICATION COMPLETE")
print("="*60)