import httpx # pyright: ignore[reportMissingImports]
import time
from typing import Dict, List, Optional
from services.collector.api.rate_limiter import RegionalRateLimiter

class RiotAPIClient:
    """Riot Games API client with regional rate limiting"""
    
    # Regional routing values
    REGION_ROUTES = {
        'na1': 'americas',
        'euw1': 'europe',
        'kr': 'asia'
    }
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.rate_limiter = RegionalRateLimiter()
        self.client = httpx.Client(timeout=30.0)
    
    def _make_request(self, url: str, region: str, retries: int = 3) -> Optional[Dict]:
        """Make API request with rate limiting and retries"""
        for attempt in range(retries):
            try:
                # Acquire rate limit token
                self.rate_limiter.acquire(region)
                
                # Make request
                response = self.client.get(
                    url,
                    headers={'X-Riot-Token': self.api_key}
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    # Rate limited - wait and retry
                    retry_after = int(response.headers.get('Retry-After', 10))
                    print(f"⚠️  429 Rate Limited, waiting {retry_after}s")
                    time.sleep(retry_after)
                    continue
                elif response.status_code == 404:
                    # Not found
                    return None
                else:
                    print(f"❌ API Error {response.status_code}: {url}")
                    return None
                    
            except Exception as e:
                print(f"❌ Request failed (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def get_match_list(self, puuid: str, region: str, count: int = 20) -> List[str]:
        """Get recent match IDs for a player"""
        routing = self.REGION_ROUTES.get(region, 'americas')
        url = f"https://{routing}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?count={count}"
        
        result = self._make_request(url, region)
        return result if result else []
    
    def get_match(self, match_id: str, region: str) -> Optional[Dict]:
        """Get match details"""
        routing = self.REGION_ROUTES.get(region, 'americas')
        url = f"https://{routing}.api.riotgames.com/lol/match/v5/matches/{match_id}"
        
        return self._make_request(url, region)
    
    def get_timeline(self, match_id: str, region: str) -> Optional[Dict]:
        """Get match timeline"""
        routing = self.REGION_ROUTES.get(region, 'americas')
        url = f"https://{routing}.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline"
        
        return self._make_request(url, region)
    
    def get_summoner_by_puuid(self, puuid: str, region: str) -> Optional[Dict]:
        """Get summoner info by PUUID"""
        url = f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
        
        return self._make_request(url, region)
    
    def get_summoner_by_id(self, summoner_id: str, region: str) -> Optional[Dict]:
        """Get summoner info by summoner ID"""
        url = f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/{summoner_id}"
        
        return self._make_request(url, region)

    def get_league_entries(self, summoner_id: str, region: str) -> List[Dict]:
        """Get ranked info for summoner"""
        url = f"https://{region}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}"
        
        result = self._make_request(url, region)
        return result if result else []
    
    def get_challenger_league(self, region: str) -> Optional[Dict]:
        """Get Challenger league"""
        url = f"https://{region}.api.riotgames.com/lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5"
        
        return self._make_request(url, region)
    
    def get_grandmaster_league(self, region: str) -> Optional[Dict]:
        """Get Grandmaster league"""
        url = f"https://{region}.api.riotgames.com/lol/league/v4/grandmasterleagues/by-queue/RANKED_SOLO_5x5"
        
        return self._make_request(url, region)
    
    def get_master_league(self, region: str) -> Optional[Dict]:
        """Get Master league"""
        url = f"https://{region}.api.riotgames.com/lol/league/v4/masterleagues/by-queue/RANKED_SOLO_5x5"
        
        return self._make_request(url, region)
    
    def close(self):
        """Close the HTTP client"""
        self.client.close()