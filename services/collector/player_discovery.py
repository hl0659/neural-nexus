from datetime import datetime, timedelta
from typing import Dict, List
from shared.database.connection import db_pool

class PlayerDiscovery:
    """Discovers new players from match participants and queues them for enrichment"""
    
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
        Marks them as UNKNOWN and queues for enrichment.
        """
        participants = match_data['info']['participants']
        region = match_data['metadata']['matchId'].split('_')[0].lower()
        
        # Process each participant
        new_players = []
        enrichment_queue_entries = []
        
        for p in participants:
            puuid = p['puuid']
            
            # Skip if player already exists
            if self._player_exists(puuid):
                continue
            
            # Add as UNKNOWN tier - enrichment service will update
            next_check = datetime.now() + timedelta(days=self.RECHECK_DAYS['UNKNOWN'])
            
            new_players.append({
                'puuid': puuid,
                'summoner_name': p.get('summonerName', 'Unknown'),
                'region': region,
                'tier': 'UNKNOWN',
                'next_check_after': next_check
            })
            
            # Queue for enrichment
            enrichment_queue_entries.append({
                'puuid': puuid,
                'needs_summoner_id': True,
                'needs_rank': True,
                'needs_riot_id': True,
                'priority': 5
            })
        
        # Batch insert new players and enrichment queue entries
        if new_players:
            self._insert_players_batch(new_players)
            self._add_to_enrichment_queue(enrichment_queue_entries)
            
            print(f"✨ Discovered {len(new_players)} new players (queued for enrichment)")
    
    def _player_exists(self, puuid: str) -> bool:
        """Check if player already exists"""
        with db_pool.get_cursor() as cursor:
            cursor.execute("SELECT 1 FROM players WHERE puuid = %s", (puuid,))
            return cursor.fetchone() is not None
    
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
    
    def _add_to_enrichment_queue(self, entries: List[Dict]):
        """Add players to enrichment queue"""
        with db_pool.get_cursor() as cursor:
            for entry in entries:
                cursor.execute("""
                    INSERT INTO enrichment_queue (
                        puuid, needs_summoner_id, needs_rank, needs_riot_id, priority
                    ) VALUES (
                        %(puuid)s, %(needs_summoner_id)s, %(needs_rank)s, 
                        %(needs_riot_id)s, %(priority)s
                    )
                    ON CONFLICT (puuid) DO UPDATE SET
                        needs_summoner_id = EXCLUDED.needs_summoner_id,
                        needs_rank = EXCLUDED.needs_rank,
                        needs_riot_id = EXCLUDED.needs_riot_id,
                        status = 'pending'
                """, entry)