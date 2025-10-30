from typing import List, Dict
from services.collector.api.riot_client import RiotAPIClient
from shared.database.match_ops import match_exists

class MatchScanner:
    """Scans for new matches for a player"""
    
    def __init__(self, api_client: RiotAPIClient):
        self.api_client = api_client
    
    def find_new_matches(self, player: Dict) -> List[str]:
        """
        Find new matches for a player.
        Stops at first known match for efficiency.
        """
        puuid = player['puuid']
        region = player['region']
        last_match_id = player.get('last_match_id')
        
        # Fetch recent matches (only 1 API call)
        match_history = self.api_client.get_match_list(puuid, region, count=20)
        
        if not match_history:
            return []
        
        new_matches = []
        
        for match_id in match_history:
            # CRITICAL: Stop at first known match
            if match_id == last_match_id:
                print(f"✓ Reached last known match for {player.get('summoner_name', 'player')}")
                break
            
            # Also check database in case another player brought this match
            if match_exists(match_id):
                print(f"⊙ Match {match_id} already in database")
                continue
            
            new_matches.append(match_id)
        
        return new_matches
    
    def is_very_active(self, new_match_count: int) -> bool:
        """
        Check if player is very active.
        Used to boost priority for active players.
        """
        return new_match_count >= 20