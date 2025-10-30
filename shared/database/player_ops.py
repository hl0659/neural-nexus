from datetime import datetime, timedelta
from typing import Optional, Dict, List
from shared.database.connection import db_pool

def insert_player(player_data: Dict) -> bool:
    """Insert a new player into the database"""
    with db_pool.get_cursor() as cursor:
        cursor.execute("""
            INSERT INTO players (
                puuid, summoner_id, summoner_name, tag_line,
                tier, rank, league_points, wins, losses,
                region, next_check_after
            ) VALUES (
                %(puuid)s, %(summoner_id)s, %(summoner_name)s, %(tag_line)s,
                %(tier)s, %(rank)s, %(league_points)s, %(wins)s, %(losses)s,
                %(region)s, %(next_check_after)s
            )
            ON CONFLICT (puuid) DO NOTHING
        """, player_data)
        return cursor.rowcount > 0

def get_player(puuid: str) -> Optional[Dict]:
    """Get player by PUUID"""
    with db_pool.get_cursor() as cursor:
        cursor.execute("SELECT * FROM players WHERE puuid = %s", (puuid,))
        return cursor.fetchone()

def update_player_last_match(puuid: str, match_id: str, next_check: datetime):
    """Update player's last match and next check time"""
    with db_pool.get_cursor() as cursor:
        cursor.execute("""
            UPDATE players 
            SET last_match_id = %s,
                next_check_after = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE puuid = %s
        """, (match_id, next_check, puuid))

def update_player_rank(puuid: str, tier: str, rank: str, lp: int):
    """Update player's rank information"""
    with db_pool.get_cursor() as cursor:
        cursor.execute("""
            UPDATE players
            SET tier = %s,
                rank = %s,
                league_points = %s,
                last_rank_update = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE puuid = %s
        """, (tier, rank, lp, puuid))

def get_next_player_to_check(region: str, tier: Optional[str] = None) -> Optional[Dict]:
    """Get next player that needs checking"""
    with db_pool.get_cursor() as cursor:
        if tier:
            cursor.execute("""
                SELECT * FROM players
                WHERE region = %s 
                  AND tier = %s
                  AND next_check_after < CURRENT_TIMESTAMP
                ORDER BY next_check_after ASC
                LIMIT 1
            """, (region, tier))
        else:
            cursor.execute("""
                SELECT * FROM players
                WHERE region = %s
                  AND next_check_after < CURRENT_TIMESTAMP
                ORDER BY next_check_after ASC
                LIMIT 1
            """, (region,))
        
        return cursor.fetchone()

def get_oldest_checked_player(region: str) -> Optional[Dict]:
    """Get player checked longest ago (fallback)"""
    with db_pool.get_cursor() as cursor:
        cursor.execute("""
            SELECT * FROM players
            WHERE region = %s
            ORDER BY next_check_after ASC
            LIMIT 1
        """, (region,))
        return cursor.fetchone()