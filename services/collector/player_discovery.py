from datetime import datetime, timedelta
from typing import Dict, List
from shared.database.connection import db_pool

class PlayerDiscovery:
    """Discovers new players from match participants"""
    
    TIER_VALUES = {
        'CHALLENGER': 9,
        'GRANDMASTER': 8,
        'MASTER': 7,
        'DIAMOND': 6,
        'EMERALD': 5,
        'PLATINUM': 4,
        'GOLD': 3,
        'SILVER': 2,
        'BRONZE': 1,
        'IRON': 0
    }
    
    RECHECK_DAYS = {
        'CHALLENGER': 2,
        'GRANDMASTER': 3,
        'MASTER': 4,
        'DIAMOND': 5,
        'EMERALD': 7,
        'PLATINUM': 10,
        'UNKNOWN': 10
    }
    
    def process_match_participants(self, match_data: Dict):
        """
        Extract and add new players from match participants.
        Infers tier from known players in the lobby.
        """
        participants = match_data['info']['participants']
        region = match_data['metadata']['matchId'].split('_')[0]
        
        # Get tiers of known players
        known_tiers = []
        for p in participants:
            existing_player = self._get_player(p['puuid'])
            if existing_player and existing_player.get('tier'):
                known_tiers.append(existing_player['tier'])
        
        # Infer tier for unknown players
        inferred_tier = self._infer_tier(known_tiers)
        
        # Process each participant
        new_players = []
        for p in participants:
            if not self._player_exists(p['puuid']):
                recheck_days = self.RECHECK_DAYS.get(inferred_tier, 10)
                next_check = datetime.now() + timedelta(days=recheck_days)
                
                new_players.append({
                    'puuid': p['puuid'],
                    'summoner_name': p.get('summonerName', 'Unknown'),
                    'region': region,
                    'tier': inferred_tier,
                    'next_check_after': next_check
                })
        
        # Batch insert new players
        if new_players:
            self._insert_players_batch(new_players)
            print(f"✨ Discovered {len(new_players)} new players (tier: {inferred_tier})")
    
    def _infer_tier(self, known_tiers: List[str]) -> str:
        """Infer tier from known players in lobby"""
        if not known_tiers:
            return 'UNKNOWN'
        
        # Calculate average tier value
        tier_values = [self.TIER_VALUES.get(t, 3) for t in known_tiers]
        avg_value = sum(tier_values) / len(tier_values)
        
        # Return tier one below average (matchmaking usually works this way)
        if avg_value >= 8.5:
            return 'GRANDMASTER'
        elif avg_value >= 7.5:
            return 'MASTER'
        elif avg_value >= 6.5:
            return 'DIAMOND'
        elif avg_value >= 5.5:
            return 'EMERALD'
        elif avg_value >= 4.5:
            return 'PLATINUM'
        elif avg_value >= 3.5:
            return 'GOLD'
        else:
            return 'UNKNOWN'
    
    def _player_exists(self, puuid: str) -> bool:
        """Check if player already exists"""
        with db_pool.get_cursor() as cursor:
            cursor.execute("SELECT 1 FROM players WHERE puuid = %s", (puuid,))
            return cursor.fetchone() is not None
    
    def _get_player(self, puuid: str) -> Dict:
        """Get player data"""
        with db_pool.get_cursor() as cursor:
            cursor.execute("SELECT * FROM players WHERE puuid = %s", (puuid,))
            return cursor.fetchone()
    
    def _insert_players_batch(self, players: List[Dict]):
        """Batch insert new players"""
        with db_pool.get_cursor() as cursor:
            for player in players:
                cursor.execute("""
                    INSERT INTO players (
                        puuid, summoner_name, region, tier, next_check_after
                    ) VALUES (
                        %(puuid)s, %(summoner_name)s, %(region)s, 
                        %(tier)s, %(next_check_after)s
                    )
                    ON CONFLICT (puuid) DO NOTHING
                """, player)