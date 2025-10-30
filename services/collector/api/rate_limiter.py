import time
from threading import Lock
from typing import Dict
from shared.config.settings import settings

class RegionalRateLimiter:
    """Per-region rate limiter for Riot API (100 requests per 2 minutes per region)"""
    
    def __init__(self):
        self.regions: Dict[str, Dict] = {}
        
        # Initialize each region
        for region in settings.REGIONS:
            self.regions[region] = {
                'tokens': settings.RATE_LIMIT_REQUESTS,
                'window_start': time.time(),
                'lock': Lock()
            }
    
    def acquire(self, region: str) -> bool:
        """
        Acquire a token for the given region.
        Blocks until a token is available.
        """
        if region not in self.regions:
            raise ValueError(f"Unknown region: {region}")
        
        bucket = self.regions[region]
        
        with bucket['lock']:
            now = time.time()
            elapsed = now - bucket['window_start']
            
            # Reset window if enough time has passed
            if elapsed >= settings.RATE_LIMIT_WINDOW_SECONDS:
                bucket['tokens'] = settings.RATE_LIMIT_REQUESTS
                bucket['window_start'] = now
                elapsed = 0
            
            # If we have tokens, use one
            if bucket['tokens'] > 0:
                bucket['tokens'] -= 1
                return True
            
            # Need to wait for reset
            sleep_time = settings.RATE_LIMIT_WINDOW_SECONDS - elapsed
        
        # Sleep outside the lock so other regions aren't blocked
        print(f"⏸️  Rate limit hit for {region}, sleeping {sleep_time:.1f}s")
        time.sleep(sleep_time)
        
        # Recursive call after sleeping
        return self.acquire(region)
    
    def get_remaining(self, region: str) -> int:
        """Get remaining tokens for a region"""
        if region not in self.regions:
            return 0
        
        bucket = self.regions[region]
        with bucket['lock']:
            return bucket['tokens']
    
    def get_reset_time(self, region: str) -> float:
        """Get seconds until rate limit resets"""
        if region not in self.regions:
            return 0.0
        
        bucket = self.regions[region]
        with bucket['lock']:
            elapsed = time.time() - bucket['window_start']
            return max(0, settings.RATE_LIMIT_WINDOW_SECONDS - elapsed)