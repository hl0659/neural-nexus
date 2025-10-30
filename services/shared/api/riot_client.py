"""
Neural Nexus v3.0 - Riot API Client
Dual-key API client supporting both APEX and NEXUS keys
"""

import requests
import time
from typing import Optional, Dict, Any
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from shared.config.settings import settings


class RiotAPIClient:
    """
    Riot API client with support for multiple API keys
    
    Usage:
        apex_client = RiotAPIClient('apex')
        nexus_client = RiotAPIClient('nexus')
    """
    
    def __init__(self, key_type: str):
        """
        Initialize API client
        
        Args:
            key_type: Either 'apex' or 'nexus'
        """
        if key_type not in ['apex', 'nexus']:
            raise ValueError("key_type must be 'apex' or 'nexus'")
        
        self.key_type = key_type
        self.api_key = (settings.RIOT_API_KEY_APEX if key_type == 'apex' 
                       else settings.RIOT_API_KEY_NEXUS)
        
        if not self.api_key:
            raise ValueError(f"{key_type.upper()} API key not configured")
        
        self.headers = {'X-Riot-Token': self.api_key}
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def _make_request(self, url: str, params: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request with error handling
        
        Args:
            url: Full URL to request
            params: Optional query parameters
        
        Returns:
            Response JSON or None if error
        """
        try:
            response = self.session.get(url, params=params, timeout=10)
            
            # Rate limit headers
            rate_limit = response.headers.get('X-App-Rate-Limit-Count', 'N/A')
            
            if response.status_code == 200:
                return response.json()
            
            elif response.status_code == 429:
                # Rate limited
                retry_after = int(response.headers.get('Retry-After', 60))
                print(f"⚠️  [{self.key_type.upper()}] Rate limited. Retry after {retry_after}s")
                time.sleep(retry_after)
                return None
            
            elif response.status_code == 404:
                # Not found (normal for some queries)
                return None
            
            else:
                print(f"❌ [{self.key_type.upper()}] API Error {response.status_code}: {response.text}")
                return None
        
        except requests.exceptions.Timeout:
            print(f"❌ [{self.key_type.upper()}] Request timeout: {url}")
            return None
        
        except Exception as e:
            print(f"❌ [{self.key_type.upper()}] Request failed: {e}")
            return None
    
    # ========================================================================
    # LEAGUE-V4 Endpoints
    # ========================================================================
    
    def get_challenger_league(self, region: str) -> Optional[Dict]:
        """Get Challenger league for a region"""
        url = f"https://{region}.api.riotgames.com/lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5"
        return self._make_request(url)
    
    def get_grandmaster_league(self, region: str) -> Optional[Dict]:
        """Get Grandmaster league for a region"""
        url = f"https://{region}.api.riotgames.com/lol/league/v4/grandmasterleagues/by-queue/RANKED_SOLO_5x5"
        return self._make_request(url)
    
    def get_league_by_puuid(self, puuid: str, region: str) -> Optional[list]:
        """
        Get league entries for a player by PUUID
        
        CRITICAL: PUUID must be from the same API key!
        """
        url = f"https://{region}.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}"
        return self._make_request(url)
    
    # ========================================================================
    # ACCOUNT-V1 Endpoints (Regional Routing)
    # ========================================================================
    
    def get_account_by_puuid(self, puuid: str, platform: str) -> Optional[Dict]:
        """
        Get account info (Riot ID) by PUUID
        
        Args:
            puuid: Player PUUID
            platform: Platform code (e.g., 'na1', 'euw1')
        
        Returns:
            Dict with 'gameName' and 'tagLine' or None
        """
        routing = settings.get_regional_routing(platform)
        url = f"https://{routing}.api.riotgames.com/riot/account/v1/accounts/by-puuid/{puuid}"
        return self._make_request(url)
    
    def get_account_by_riot_id(self, game_name: str, tag_line: str, platform: str) -> Optional[Dict]:
        """
        Get account info by Riot ID (gameName#tagLine)
        
        Args:
            game_name: In-game name
            tag_line: Tag line (without #)
            platform: Platform code (e.g., 'na1')
        
        Returns:
            Dict with 'puuid' or None
        """
        routing = settings.get_regional_routing(platform)
        url = f"https://{routing}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        return self._make_request(url)
    
    # ========================================================================
    # MATCH-V5 Endpoints (Regional Routing)
    # ========================================================================
    
    def get_match_history(self, puuid: str, platform: str, 
                         count: int = 200, start: int = 0) -> Optional[list]:
        """
        Get match history for a player
        
        Args:
            puuid: Player PUUID (must match this client's key)
            platform: Platform code
            count: Number of matches (max 200)
            start: Starting index
        
        Returns:
            List of match IDs or None
        """
        routing = settings.get_regional_routing(platform)
        url = f"https://{routing}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"
        params = {
            'start': start,
            'count': min(count, 200)  # API max is 200
        }
        return self._make_request(url, params)
    
    def get_match(self, match_id: str, platform: str) -> Optional[Dict]:
        """
        Get match details
        
        Args:
            match_id: Match ID (e.g., 'NA1_1234567890')
            platform: Platform code
        
        Returns:
            Match data dict or None
        """
        routing = settings.get_regional_routing(platform)
        url = f"https://{routing}.api.riotgames.com/lol/match/v5/matches/{match_id}"
        return self._make_request(url)
    
    def get_timeline(self, match_id: str, platform: str) -> Optional[Dict]:
        """
        Get match timeline
        
        Args:
            match_id: Match ID
            platform: Platform code
        
        Returns:
            Timeline data dict or None
        """
        routing = settings.get_regional_routing(platform)
        url = f"https://{routing}.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline"
        return self._make_request(url)
    
    def close(self):
        """Close the session"""
        self.session.close()


if __name__ == "__main__":
    # Test both API clients
    print("Testing APEX API Client...")
    apex_client = RiotAPIClient('apex')
    
    print("\nTesting Challenger league fetch...")
    challenger = apex_client.get_challenger_league('na1')
    if challenger:
        print(f"✅ Found {len(challenger.get('entries', []))} Challenger players")
    else:
        print("❌ Failed to fetch Challenger league")
    
    print("\n" + "="*60)
    print("Testing NEXUS API Client...")
    nexus_client = RiotAPIClient('nexus')
    
    print("\nTesting Grandmaster league fetch...")
    grandmaster = nexus_client.get_grandmaster_league('na1')
    if grandmaster:
        print(f"✅ Found {len(grandmaster.get('entries', []))} Grandmaster players")
    else:
        print("❌ Failed to fetch Grandmaster league")
    
    # Clean up
    apex_client.close()
    nexus_client.close()
    
    print("\n✅ API client tests complete!")