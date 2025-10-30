from typing import Dict, List, Optional
from shared.database.connection import db_pool

def match_exists(match_id: str) -> bool:
    """Check if match already exists in database"""
    with db_pool.get_cursor() as cursor:
        cursor.execute("SELECT 1 FROM matches WHERE match_id = %s", (match_id,))
        return cursor.fetchone() is not None

def insert_match(match_data: Dict, match_path: str, timeline_path: Optional[str] = None):
    """Insert match and all related data"""
    info = match_data['info']
    match_id = match_data['metadata']['matchId']
    
    # Skip remakes
    if info['gameDuration'] < 300:
        return False
    
    with db_pool.get_cursor() as cursor:
        # Insert match
        cursor.execute("""
            INSERT INTO matches (
                match_id, region, game_version, game_duration,
                game_creation, patch, json_path, timeline_json_path
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (match_id) DO NOTHING
        """, (
            match_id,
            match_id.split('_')[0],
            info['gameVersion'],
            info['gameDuration'],
            info['gameCreation'],
            '.'.join(info['gameVersion'].split('.')[:2]),
            match_path,
            timeline_path
        ))
        
        # Insert participants
        for p in info['participants']:
            cursor.execute("""
                INSERT INTO match_participants (
                    match_id, puuid, participant_id, champion_id, champion_name,
                    team_id, team_position, won, kills, deaths, assists,
                    total_damage_dealt_to_champions, gold_earned, cs_score, vision_score
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (match_id, puuid) DO NOTHING
            """, (
                match_id,
                p['puuid'],
                p['participantId'],
                p['championId'],
                p['championName'],
                p['teamId'],
                p['teamPosition'],
                p['win'],
                p['kills'],
                p['deaths'],
                p['assists'],
                p['totalDamageDealtToChampions'],
                p['goldEarned'],
                p['totalMinionsKilled'] + p['neutralMinionsKilled'],
                p['visionScore']
            ))
        
        # Insert bans
        for team in info['teams']:
            for ban in team['bans']:
                cursor.execute("""
                    INSERT INTO match_bans (
                        match_id, team_id, champion_id, pick_turn
                    ) VALUES (%s, %s, %s, %s)
                    ON CONFLICT (match_id, team_id, pick_turn) DO NOTHING
                """, (
                    match_id,
                    team['teamId'],
                    ban['championId'],
                    ban['pickTurn']
                ))
        
        return True

def get_match(match_id: str) -> Optional[Dict]:
    """Get match metadata"""
    with db_pool.get_cursor() as cursor:
        cursor.execute("SELECT * FROM matches WHERE match_id = %s", (match_id,))
        return cursor.fetchone()

def get_player_matches(puuid: str, limit: int = 20) -> List[Dict]:
    """Get matches for a player"""
    with db_pool.get_cursor() as cursor:
        cursor.execute("""
            SELECT m.* FROM matches m
            JOIN match_participants mp ON m.match_id = mp.match_id
            WHERE mp.puuid = %s
            ORDER BY m.game_creation DESC
            LIMIT %s
        """, (puuid, limit))
        return cursor.fetchall()