"""
Neural Nexus v3.0 - Match Database Operations
CRUD operations for matches, participants, and bans
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared.database.connection import db_pool
from services.shared.models.match import Match, MatchParticipant


def insert_match(
    match_id: str,
    region: str,
    collected_by: str,
    game_version: str,
    game_duration: int,
    game_creation: int,
    patch: str,
    game_mode: str,
    json_path: str,
    timeline_json_path: str
) -> bool:
    """
    Insert a new match
    
    Returns:
        True if inserted, False if already exists
    """
    try:
        with db_pool.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO matches (
                    match_id, region, collected_by, game_version,
                    game_duration, game_creation, patch, game_mode,
                    json_path, timeline_json_path
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (match_id) DO NOTHING
                RETURNING match_id
            """, (
                match_id, region, collected_by, game_version,
                game_duration, game_creation, patch, game_mode,
                json_path, timeline_json_path
            ))
            
            return cursor.fetchone() is not None
    
    except Exception as e:
        print(f"❌ Failed to insert match {match_id}: {e}")
        return False


def get_match(match_id: str) -> Optional[Match]:
    """Get match by ID"""
    try:
        with db_pool.get_cursor(commit=False) as cursor:
            cursor.execute("SELECT * FROM matches WHERE match_id = %s", (match_id,))
            
            row = cursor.fetchone()
            if row:
                return Match(**row)
            return None
    
    except Exception as e:
        print(f"❌ Failed to get match {match_id}: {e}")
        return None


def match_exists(match_id: str) -> bool:
    """Check if match exists in database"""
    try:
        with db_pool.get_cursor(commit=False) as cursor:
            cursor.execute("SELECT 1 FROM matches WHERE match_id = %s", (match_id,))
            return cursor.fetchone() is not None
    
    except Exception as e:
        print(f"❌ Failed to check match existence: {e}")
        return False


def insert_participant(
    match_id: str,
    region: str,
    game_name: str,
    tag_line: str,
    participant_id: int,
    champion_id: int,
    champion_name: str,
    team_id: int,
    team_position: str,
    won: bool,
    kills: int,
    deaths: int,
    assists: int,
    total_damage_dealt_to_champions: int,
    gold_earned: int,
    cs_score: int,
    vision_score: int
) -> bool:
    """Insert a match participant"""
    try:
        with db_pool.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO match_participants (
                    match_id, region, game_name, tag_line,
                    participant_id, champion_id, champion_name,
                    team_id, team_position, won,
                    kills, deaths, assists,
                    total_damage_dealt_to_champions,
                    gold_earned, cs_score, vision_score
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (match_id, region, game_name, tag_line) DO NOTHING
                RETURNING match_id
            """, (
                match_id, region, game_name, tag_line,
                participant_id, champion_id, champion_name,
                team_id, team_position, won,
                kills, deaths, assists,
                total_damage_dealt_to_champions,
                gold_earned, cs_score, vision_score
            ))
            
            return cursor.fetchone() is not None
    
    except Exception as e:
        print(f"❌ Failed to insert participant: {e}")
        return False


def get_match_participants(match_id: str) -> List[MatchParticipant]:
    """Get all participants for a match"""
    try:
        with db_pool.get_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT * FROM match_participants
                WHERE match_id = %s
                ORDER BY team_id, participant_id
            """, (match_id,))
            
            return [MatchParticipant(**row) for row in cursor.fetchall()]
    
    except Exception as e:
        print(f"❌ Failed to get participants: {e}")
        return []


def insert_ban(match_id: str, team_id: int, champion_id: int, pick_turn: int) -> bool:
    """Insert a champion ban"""
    try:
        with db_pool.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO match_bans (match_id, team_id, champion_id, pick_turn)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (match_id, team_id, pick_turn) DO NOTHING
                RETURNING match_id
            """, (match_id, team_id, champion_id, pick_turn))
            
            return cursor.fetchone() is not None
    
    except Exception as e:
        print(f"❌ Failed to insert ban: {e}")
        return False


def get_match_count() -> int:
    """Get total match count"""
    try:
        with db_pool.get_cursor(commit=False) as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM matches")
            result = cursor.fetchone()
            return result['count'] if result else 0
    
    except Exception as e:
        print(f"❌ Failed to get match count: {e}")
        return 0


def get_matches_by_service(service: str) -> int:
    """Get match count for a specific service"""
    try:
        with db_pool.get_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT COUNT(*) as count FROM matches
                WHERE collected_by = %s
            """, (service,))
            result = cursor.fetchone()
            return result['count'] if result else 0
    
    except Exception as e:
        print(f"❌ Failed to get matches by service: {e}")
        return 0


def get_matches_by_region(region: str) -> int:
    """Get match count for a specific region"""
    try:
        with db_pool.get_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT COUNT(*) as count FROM matches
                WHERE region = %s
            """, (region,))
            result = cursor.fetchone()
            return result['count'] if result else 0
    
    except Exception as e:
        print(f"❌ Failed to get matches by region: {e}")
        return 0


def get_match_stats() -> Dict[str, Any]:
    """Get comprehensive match statistics"""
    try:
        with db_pool.get_cursor(commit=False) as cursor:
            # Total matches
            cursor.execute("SELECT COUNT(*) as count FROM matches")
            total = cursor.fetchone()['count']
            
            # By service
            cursor.execute("""
                SELECT collected_by, COUNT(*) as count
                FROM matches
                GROUP BY collected_by
            """)
            by_service = {row['collected_by']: row['count'] for row in cursor.fetchall()}
            
            # By region
            cursor.execute("""
                SELECT region, COUNT(*) as count
                FROM matches
                GROUP BY region
            """)
            by_region = {row['region']: row['count'] for row in cursor.fetchall()}
            
            return {
                'total_matches': total,
                'by_service': by_service,
                'by_region': by_region
            }
    
    except Exception as e:
        print(f"❌ Failed to get match stats: {e}")
        return {'total_matches': 0, 'by_service': {}, 'by_region': {}}


if __name__ == "__main__":
    # Test match operations
    print("Testing Match Operations...")
    print("="*60)
    
    db_pool.initialize()
    
    # First, create a test player (needed for foreign key)
    from database.operations.player_ops import insert_player
    
    insert_player(
        region='na1',
        game_name='TestPlayer',
        tag_line='TEST',
        apex_puuid='test-puuid'
    )
    
    # Test 1: Insert match
    print("\nTest 1: Inserting test match...")
    success = insert_match(
        match_id='NA1_TEST_999',
        region='na1',
        collected_by='apex',
        game_version='13.24.1.1234',
        game_duration=1856,
        game_creation=1234567890,
        patch='13.24',
        game_mode='CLASSIC',
        json_path='/test/path/match.json.gz',
        timeline_json_path='/test/path/timeline.json.gz'
    )
    print(f"{'✅' if success else '❌'} Insert match: {success}")
    
    # Test 2: Check if match exists
    print("\nTest 2: Checking if match exists...")
    exists = match_exists('NA1_TEST_999')
    print(f"{'✅' if exists else '❌'} Match exists: {exists}")
    
    # Test 3: Get match
    print("\nTest 3: Getting match...")
    match = get_match('NA1_TEST_999')
    if match:
        print(f"✅ Found match: {match}")
        print(f"   Duration: {match.get_duration_minutes():.1f} minutes")
    else:
        print("❌ Match not found")
    
    # Test 4: Insert participant
    print("\nTest 4: Inserting participant...")
    success = insert_participant(
        match_id='NA1_TEST_999',
        region='na1',
        game_name='TestPlayer',
        tag_line='TEST',
        participant_id=1,
        champion_id=103,
        champion_name='Ahri',
        team_id=100,
        team_position='MIDDLE',
        won=True,
        kills=12,
        deaths=3,
        assists=8,
        total_damage_dealt_to_champions=25000,
        gold_earned=15000,
        cs_score=220,
        vision_score=45
    )
    print(f"{'✅' if success else '❌'} Insert participant: {success}")
    
    # Test 5: Get participants
    print("\nTest 5: Getting participants...")
    participants = get_match_participants('NA1_TEST_999')
    print(f"✅ Found {len(participants)} participant(s)")
    for p in participants:
        print(f"   {p}")
    
    # Test 6: Insert ban
    print("\nTest 6: Inserting ban...")
    success = insert_ban('NA1_TEST_999', 100, 157, 1)
    print(f"{'✅' if success else '❌'} Insert ban: {success}")
    
    # Test 7: Get match stats
    print("\nTest 7: Getting match stats...")
    stats = get_match_stats()
    print(f"✅ Total matches: {stats['total_matches']}")
    print(f"   By service: {stats['by_service']}")
    print(f"   By region: {stats['by_region']}")
    
    # Cleanup
    print("\nCleaning up test data...")
    with db_pool.get_cursor() as cursor:
        cursor.execute("DELETE FROM match_bans WHERE match_id = 'NA1_TEST_999'")
        cursor.execute("DELETE FROM match_participants WHERE match_id = 'NA1_TEST_999'")
        cursor.execute("DELETE FROM matches WHERE match_id = 'NA1_TEST_999'")
        cursor.execute("DELETE FROM players WHERE game_name = 'TestPlayer' AND tag_line = 'TEST'")
    
    db_pool.close()
    
    print("\n✅ Match operations tests complete!")