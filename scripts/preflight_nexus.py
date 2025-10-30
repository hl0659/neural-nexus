"""
NEXUS Pre-Flight Check
Verifies system is ready for NEXUS test
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.database.connection import db_pool
from shared.config.settings import settings

print("="*60)
print("NEXUS SERVICE - PRE-FLIGHT CHECK")
print("="*60)

# Check 1: Environment
print("\n1. Environment Configuration:")
print(f"   ✓ NEXUS API Key: {settings.RIOT_API_KEY_NEXUS[-8:] if settings.RIOT_API_KEY_NEXUS else '❌ NOT SET'}")
print(f"   ✓ Regions: {', '.join(settings.REGIONS)}")
print(f"   ✓ Match Depth: {settings.MATCH_HISTORY_DEPTH}")
print(f"   ✓ Data Path: {settings.DATA_PATH}")

# Check 2: Database
print("\n2. Database Connection:")
db_pool.initialize()
if db_pool.test_connection():
    print("   ✓ Connection successful")
else:
    print("   ❌ Connection failed")
    db_pool.close()
    sys.exit(1)

# Check 3: NEXUS Queue
print("\n3. NEXUS Queue Status:")
with db_pool.get_cursor(commit=False) as cursor:
    cursor.execute("""
        SELECT 
            region,
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE status = 'pending') as pending
        FROM collection_queues
        WHERE queue_type = 'nexus'
        GROUP BY region
    """)
    
    total_pending = 0
    for row in cursor.fetchall():
        print(f"   {row['region'].upper()}: {row['pending']} pending (of {row['total']} total)")
        total_pending += row['pending']
    
    if total_pending == 0:
        print("\n   ❌ No pending players in NEXUS queue!")
        db_pool.close()
        sys.exit(1)
    else:
        print(f"\n   ✓ Total pending: {total_pending} players")

# Check 4: Sample Players
print("\n4. Sample Players (showing 3):")
with db_pool.get_cursor(commit=False) as cursor:
    cursor.execute("""
        SELECT p.region, p.game_name, p.tag_line, p.tier, p.league_points,
               p.apex_puuid IS NOT NULL as has_apex,
               p.nexus_puuid IS NOT NULL as has_nexus
        FROM collection_queues cq
        JOIN players p ON (
            cq.region = p.region AND 
            cq.game_name = p.game_name AND 
            cq.tag_line = p.tag_line
        )
        WHERE cq.queue_type = 'nexus'
          AND cq.status = 'pending'
        ORDER BY 
            CASE p.tier
                WHEN 'MASTER' THEN 1
                WHEN 'DIAMOND' THEN 2
                WHEN 'EMERALD' THEN 3
                ELSE 4
            END,
            p.league_points DESC
        LIMIT 3
    """)
    
    for row in cursor.fetchall():
        puuid_status = "✓ APEX" if row['has_apex'] else ""
        puuid_status += ", ✓ NEXUS" if row['has_nexus'] else ", ⚠ needs NEXUS"
        print(f"   {row['game_name']}#{row['tag_line']}")
        print(f"      {row['region'].upper()} | {row['tier']} {row['league_points']}LP | {puuid_status}")

# Check 5: Current Stats
print("\n5. Current System Stats:")
with db_pool.get_cursor(commit=False) as cursor:
    cursor.execute("SELECT COUNT(*) as count FROM matches")
    total_matches = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM matches WHERE collected_by = 'nexus'")
    nexus_matches = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM players WHERE nexus_puuid IS NOT NULL")
    with_nexus_puuid = cursor.fetchone()['count']
    
    print(f"   Total matches: {total_matches}")
    print(f"   NEXUS matches: {nexus_matches}")
    print(f"   Players with nexus_puuid: {with_nexus_puuid}")

db_pool.close()

print("\n" + "="*60)
print("PRE-FLIGHT CHECK COMPLETE ✓")
print("="*60)
print("\nSystem is ready for NEXUS test!")
print("\nRecommended test command:")
print("  python -m services.nexus.run_collection_parallel --hours 0.1")
print("\nThis will test on ~10 players for ~6 minutes")
print("="*60)