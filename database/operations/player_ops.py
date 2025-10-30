"""
Neural Nexus v3.0 - Player Database Operations
CRUD operations for players table using Riot ID as primary identifier
"""

from typing import Optional, List
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared.database.connection import db_pool
from services.shared.models.player import Player


def insert_player(
    region: str,
    game_name: str,
    tag_line: str,
    apex_puuid: Optional[str] = None,
    nexus_puuid: Optional[str] = None,
    tier: Optional[str] = None,
    rank: Optional[str] = None,
    league_points: int = 0,
    wins: int = 0,
    losses: int = 0,
    league_id: Optional[str] = None,
    discovered_by: str = 'apex',
    is_seed_player: bool = False
) -> bool:
    """
    Insert a new player
    
    Returns:
        True if inserted, False if already exists
    """
    try:
        with db_pool.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO players (
                    region, game_name, tag_line, apex_puuid, nexus_puuid,
                    tier, rank, league_points, wins, losses, league_id,
                    discovered_by, is_seed_player
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (region, game_name, tag_line) DO NOTHING
                RETURNING region
            """, (
                region, game_name, tag_line, apex_puuid, nexus_puuid,
                tier, rank, league_points, wins, losses, league_id,
                discovered_by, is_seed_player
            ))
            
            return cursor.fetchone() is not None
    
    except Exception as e:
        print(f"❌ Failed to insert player {game_name}#{tag_line}: {e}")
        return False


def get_player(region: str, game_name: str, tag_line: str) -> Optional[Player]:
    """
    Get a player by Riot ID
    
    Returns:
        Player object or None if not found
    """
    try:
        with db_pool.get_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT * FROM players
                WHERE region = %s AND game_name = %s AND tag_line = %s
            """, (region, game_name, tag_line))
            
            row = cursor.fetchone()
            if row:
                return Player(**row)
            return None
    
    except Exception as e:
        print(f"❌ Failed to get player {game_name}#{tag_line}: {e}")
        return None

def get_player_by_puuid(region: str, puuid: str, key_type: str) -> Optional[Player]:
    """
    Get a player by PUUID for a specific API key
    
    Args:
        region: Region code
        puuid: Player PUUID (encrypted by specific key)
        key_type: 'apex' or 'nexus'
    
    Returns:
        Player object or None if not found
    """
    try:
        with db_pool.get_cursor(commit=False) as cursor:
            if key_type == 'apex':
                column = 'apex_puuid'
            elif key_type == 'nexus':
                column = 'nexus_puuid'
            else:
                raise ValueError("key_type must be 'apex' or 'nexus'")
            
            cursor.execute(f"""
                SELECT * FROM players
                WHERE region = %s AND {column} = %s
            """, (region, puuid))
            
            row = cursor.fetchone()
            if row:
                return Player(**row)
            return None
    
    except Exception as e:
        print(f"❌ Failed to get player by PUUID: {e}")
        return None

def update_apex_puuid(region: str, game_name: str, tag_line: str, apex_puuid: str) -> bool:
    """Update APEX PUUID for a player"""
    try:
        with db_pool.get_cursor() as cursor:
            cursor.execute("""
                UPDATE players
                SET apex_puuid = %s, updated_at = CURRENT_TIMESTAMP
                WHERE region = %s AND game_name = %s AND tag_line = %s
            """, (apex_puuid, region, game_name, tag_line))
            
            return cursor.rowcount > 0
    
    except Exception as e:
        print(f"❌ Failed to update apex_puuid: {e}")
        return False


def update_nexus_puuid(region: str, game_name: str, tag_line: str, nexus_puuid: str) -> bool:
    """Update NEXUS PUUID for a player"""
    try:
        with db_pool.get_cursor() as cursor:
            cursor.execute("""
                UPDATE players
                SET nexus_puuid = %s, updated_at = CURRENT_TIMESTAMP
                WHERE region = %s AND game_name = %s AND tag_line = %s
            """, (nexus_puuid, region, game_name, tag_line))
            
            return cursor.rowcount > 0
    
    except Exception as e:
        print(f"❌ Failed to update nexus_puuid: {e}")
        return False


def update_rank_data(
    region: str,
    game_name: str,
    tag_line: str,
    tier: str,
    rank: Optional[str] = None,
    league_points: int = 0,
    wins: int = 0,
    losses: int = 0,
    league_id: Optional[str] = None
) -> bool:
    """Update player rank data"""
    try:
        with db_pool.get_cursor() as cursor:
            cursor.execute("""
                UPDATE players
                SET tier = %s, rank = %s, league_points = %s,
                    wins = %s, losses = %s, league_id = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE region = %s AND game_name = %s AND tag_line = %s
            """, (tier, rank, league_points, wins, losses, league_id, region, game_name, tag_line))
            
            return cursor.rowcount > 0
    
    except Exception as e:
        print(f"❌ Failed to update rank data: {e}")
        return False


def update_apex_check(region: str, game_name: str, tag_line: str, match_count: int = 0) -> bool:
    """Update last APEX check timestamp and match count"""
    try:
        with db_pool.get_cursor() as cursor:
            cursor.execute("""
                UPDATE players
                SET last_apex_check = CURRENT_TIMESTAMP,
                    apex_match_count = apex_match_count + %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE region = %s AND game_name = %s AND tag_line = %s
            """, (match_count, region, game_name, tag_line))
            
            return cursor.rowcount > 0
    
    except Exception as e:
        print(f"❌ Failed to update apex check: {e}")
        return False


def update_nexus_check(region: str, game_name: str, tag_line: str, match_count: int = 0) -> bool:
    """Update last NEXUS check timestamp and match count"""
    try:
        with db_pool.get_cursor() as cursor:
            cursor.execute("""
                UPDATE players
                SET last_nexus_check = CURRENT_TIMESTAMP,
                    nexus_match_count = nexus_match_count + %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE region = %s AND game_name = %s AND tag_line = %s
            """, (match_count, region, game_name, tag_line))
            
            return cursor.rowcount > 0
    
    except Exception as e:
        print(f"❌ Failed to update nexus check: {e}")
        return False


def get_players_without_nexus_puuid(limit: int = 100) -> List[Player]:
    """
    Get players that need NEXUS PUUID resolution
    
    These are non-Challenger/GM players discovered by APEX
    """
    try:
        with db_pool.get_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT * FROM players
                WHERE apex_puuid IS NOT NULL
                  AND nexus_puuid IS NULL
                  AND tier NOT IN ('CHALLENGER', 'GRANDMASTER')
                ORDER BY 
                    CASE tier
                        WHEN 'MASTER' THEN 1
                        WHEN 'DIAMOND' THEN 2
                        WHEN 'EMERALD' THEN 3
                        WHEN 'PLATINUM' THEN 4
                        ELSE 5
                    END,
                    league_points DESC
                LIMIT %s
            """, (limit,))
            
            return [Player(**row) for row in cursor.fetchall()]
    
    except Exception as e:
        print(f"❌ Failed to get players without nexus_puuid: {e}")
        return []


def get_player_count() -> int:
    """Get total player count"""
    try:
        with db_pool.get_cursor(commit=False) as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM players")
            result = cursor.fetchone()
            return result['count'] if result else 0
    
    except Exception as e:
        print(f"❌ Failed to get player count: {e}")
        return 0


def get_players_by_tier(tier: str) -> List[Player]:
    """Get all players of a specific tier"""
    try:
        with db_pool.get_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT * FROM players
                WHERE tier = %s
                ORDER BY league_points DESC
            """, (tier,))
            
            return [Player(**row) for row in cursor.fetchall()]
    
    except Exception as e:
        print(f"❌ Failed to get players by tier: {e}")
        return []


if __name__ == "__main__":
    # Test player operations
    print("Testing Player Operations...")
    print("="*60)
    
    db_pool.initialize()
    
    # Test 1: Insert player
    print("\nTest 1: Inserting test player...")
    success = insert_player(
        region='na1',
        game_name='TestPlayer',
        tag_line='TEST',
        apex_puuid='test-apex-puuid-123',
        tier='DIAMOND',
        rank='I',
        league_points=50,
        wins=100,
        losses=80,
        discovered_by='apex'
    )
    print(f"{'✅' if success else '❌'} Insert player: {success}")
    
    # Test 2: Get player
    print("\nTest 2: Getting player...")
    player = get_player('na1', 'TestPlayer', 'TEST')
    if player:
        print(f"✅ Found player: {player}")
        print(f"   Winrate: {player.get_winrate():.1f}%")
    else:
        print("❌ Player not found")
    
    # Test 3: Update NEXUS PUUID
    print("\nTest 3: Updating NEXUS PUUID...")
    success = update_nexus_puuid('na1', 'TestPlayer', 'TEST', 'test-nexus-puuid-456')
    print(f"{'✅' if success else '❌'} Update NEXUS PUUID: {success}")
    
    # Test 4: Update rank
    print("\nTest 4: Updating rank...")
    success = update_rank_data(
        region='na1',
        game_name='TestPlayer',
        tag_line='TEST',
        tier='DIAMOND',
        rank='II',
        league_points=75,
        wins=110,
        losses=85
    )
    print(f"{'✅' if success else '❌'} Update rank: {success}")
    
    # Test 5: Get updated player
    print("\nTest 5: Getting updated player...")
    player = get_player('na1', 'TestPlayer', 'TEST')
    if player:
        print(f"✅ Player: {player}")
        print(f"   Has APEX PUUID: {player.has_apex_puuid()}")
        print(f"   Has NEXUS PUUID: {player.has_nexus_puuid()}")
        print(f"   Winrate: {player.get_winrate():.1f}%")
    
    # Test 6: Get player count
    print("\nTest 6: Getting player count...")
    count = get_player_count()
    print(f"✅ Total players: {count}")
    
    # Cleanup
    print("\nCleaning up test data...")
    with db_pool.get_cursor() as cursor:
        cursor.execute("DELETE FROM players WHERE game_name = 'TestPlayer' AND tag_line = 'TEST'")
    
    db_pool.close()
    
    print("\n✅ Player operations tests complete!")