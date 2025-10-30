from datetime import datetime, timedelta
from typing import Dict, List, Optional
from shared.database.connection import db_pool
from shared.config.settings import settings
from services.collector.api.riot_client import RiotAPIClient

class PlayerDiscovery:
    """Discovers new players from match participants and fetches their real ranks"""
    
    RECHECK_DAYS = {
        'CHALLENGER': 2,
        'GRANDMASTER': 3,
        'MASTER': 4,
        'DIAMOND': 5,
        'EMERALD': 7,
        'PLATINUM': 10,
        'GOLD': 14,
        'UNKNOWN': 10
    }
    
    def __init__(self):
        # Use enrichment API key for player lookups
        self.api_client = RiotAPIClient(settings.RIOT_API_KEY_ENRICHMENT)
    
    def process_match_participants(self, match_data: Dict):
        """
        Extract and add new players from match participants.
        Queries real rank data from API.
        """
        participants = match_data['info']['participants']
        region = match_data['metadata']['matchId'].split('_')[0]
        
        # Process each participant
        new_players = []
        for p in participants:
            puuid = p['puuid']
            
            # Skip if player already exists
            if self._player_exists(puuid):
                continue
            
            # Get real rank from API
            rank_data = self._get_player_rank(puuid, region)
            
            if rank_data:
                tier = rank_data['tier']
                rank = rank_data['rank']
                lp = rank_data['league_points']
                wins = rank_data['wins']
                losses = rank_data['losses']
                summoner_id = rank_data['summoner_id']
            else:
                # Fallback if API fails
                tier = 'UNKNOWN'
                rank = None
                lp = 0
                wins = 0
                losses = 0
                summoner_id = None
            
            # Calculate next check time based on tier
            recheck_days = self.RECHECK_DAYS.get(tier, 10)
            next_check = datetime.now() + timedelta(days=recheck_days)
            
            new_players.append({
                'puuid': puuid,
                'summoner_id': summoner_id,
                'summoner_name': p.get('summonerName', 'Unknown'),
                'region': region,
                'tier': tier,
                'rank': rank,
                'league_points': lp,
                'wins': wins,
                'losses': losses,
                'next_check_after': next_check
            })
        
        # Batch insert new players
        if new_players:
            self._insert_players_batch(new_players)
            
            # Count by tier for logging
            tier_counts = {}
            for p in new_players:
                tier = p['tier']
                tier_counts[tier] = tier_counts.get(tier, 0) + 1
            
            tier_summary = ', '.join([f"{count} {tier}" for tier, count in tier_counts.items()])
            print(f"✨ Discovered {len(new_players)} new players ({tier_summary})")
    
    def _get_player_rank(self, puuid: str, region: str) -> Optional[Dict]:
        """Get player's ranked data from API using enrichment key"""
        try:
            # First get summoner ID
            summoner = self.api_client.get_summoner_by_puuid(puuid, region)
            if not summoner or 'id' not in summoner:
                return None
            
            summoner_id = summoner['id']
            
            # Get league entries
            league_entries = self.api_client.get_league_entries(summoner_id, region)
            if not league_entries:
                return None
            
            # Find ranked solo/duo entry
            for entry in league_entries:
                if entry.get('queueType') == 'RANKED_SOLO_5x5':
                    return {
                        'summoner_id': summoner_id,
                        'tier': entry.get('tier', 'UNKNOWN'),
                        'rank': entry.get('rank', 'IV'),
                        'league_points': entry.get('leaguePoints', 0),
                        'wins': entry.get('wins', 0),
                        'losses': entry.get('losses', 0)
                    }
            
            return None
            
        except Exception as e:
            print(f"  ⚠️  Failed to get rank for {puuid}: {e}")
            return None
    
    def _player_exists(self, puuid: str) -> bool:
        """Check if player already exists"""
        with db_pool.get_cursor() as cursor:
            cursor.execute("SELECT 1 FROM players WHERE puuid = %s", (puuid,))
            return cursor.fetchone() is not None
    
    def _insert_players_batch(self, players: List[Dict]):
        """Batch insert new players with full rank data"""
        with db_pool.get_cursor() as cursor:
            for player in players:
                cursor.execute("""
                    INSERT INTO players (
                        puuid, summoner_id, summoner_name, region, 
                        tier, rank, league_points, wins, losses,
                        next_check_after, last_rank_update
                    ) VALUES (
                        %(puuid)s, %(summoner_id)s, %(summoner_name)s, %(region)s,
                        %(tier)s, %(rank)s, %(league_points)s, %(wins)s, %(losses)s,
                        %(next_check_after)s, CURRENT_TIMESTAMP
                    )
                    ON CONFLICT (puuid) DO NOTHING
                """, player)