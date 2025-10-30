"""
Neural Nexus v3.0 - Rate Limiter
Per-key, per-region rate limiting for Riot API
"""

import time
from collections import defaultdict
from threading import Lock
from typing import Dict, Tuple, Optional
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from shared.config.settings import settings


class RateLimiter:
    """
    Rate limiter with per-key, per-region tracking
    
    Riot API limits: 100 requests per 120 seconds per region per key
    """
    
    def __init__(self):
        # Track requests: {(key_type, region): [(timestamp1, timestamp2, ...)]}
        self._requests: Dict[Tuple[str, str], list] = defaultdict(list)
        self._lock = Lock()
        
        # Configuration
        self.window_seconds = settings.RATE_LIMIT_WINDOW_SECONDS  # 120
        self.max_requests = settings.RATE_LIMIT_REQUESTS  # 100
    
    def _cleanup_old_requests(self, key: Tuple[str, str]):
        """Remove requests older than the time window"""
        current_time = time.time()
        cutoff_time = current_time - self.window_seconds
        
        self._requests[key] = [
            ts for ts in self._requests[key] 
            if ts > cutoff_time
        ]
    
    def can_make_request(self, key_type: str, region: str) -> bool:
        """
        Check if we can make a request without exceeding rate limit
        
        Args:
            key_type: 'apex' or 'nexus'
            region: Region code (e.g., 'na1', 'euw1', 'kr')
        
        Returns:
            True if request can be made, False if rate limited
        """
        with self._lock:
            key = (key_type, region)
            self._cleanup_old_requests(key)
            
            return len(self._requests[key]) < self.max_requests
    
    def record_request(self, key_type: str, region: str):
        """
        Record that a request was made
        
        Args:
            key_type: 'apex' or 'nexus'
            region: Region code
        """
        with self._lock:
            key = (key_type, region)
            self._requests[key].append(time.time())
    
    def wait_if_needed(self, key_type: str, region: str) -> float:
        """
        Block until we can make a request (if rate limited)
        
        Args:
            key_type: 'apex' or 'nexus'
            region: Region code
        
        Returns:
            Wait time in seconds (0 if no wait needed)
        """
        with self._lock:
            key = (key_type, region)
            self._cleanup_old_requests(key)
            
            if len(self._requests[key]) < self.max_requests:
                return 0
            
            # Calculate wait time until oldest request expires
            oldest_request = min(self._requests[key])
            wait_until = oldest_request + self.window_seconds
            wait_time = max(0, wait_until - time.time())
            
            if wait_time > 0:
                print(f"⏳ [{key_type.upper()}:{region.upper()}] Rate limited. Waiting {wait_time:.1f}s...")
            
            return wait_time
    
    def get_status(self, key_type: str, region: str) -> Dict:
        """
        Get current rate limit status
        
        Returns:
            Dict with usage stats
        """
        with self._lock:
            key = (key_type, region)
            self._cleanup_old_requests(key)
            
            used = len(self._requests[key])
            remaining = self.max_requests - used
            percentage = (used / self.max_requests) * 100
            
            return {
                'key_type': key_type,
                'region': region,
                'used': used,
                'remaining': remaining,
                'max': self.max_requests,
                'window_seconds': self.window_seconds,
                'percentage': percentage
            }
    
    def get_all_status(self) -> list:
        """Get status for all tracked key-region combinations"""
        statuses = []
        # Create a copy of keys to avoid modification during iteration
        keys_copy = list(self._requests.keys())
        
        for key in keys_copy:
            key_type, region = key
            statuses.append(self.get_status(key_type, region))
        
        return statuses
    
    def reset(self, key_type: Optional[str] = None, region: Optional[str] = None):
        """
        Reset rate limit tracking
        
        Args:
            key_type: Optional - reset only this key type
            region: Optional - reset only this region
        """
        with self._lock:
            if key_type and region:
                key = (key_type, region)
                if key in self._requests:
                    del self._requests[key]
            elif key_type:
                keys_to_remove = [k for k in self._requests.keys() if k[0] == key_type]
                for k in keys_to_remove:
                    del self._requests[k]
            elif region:
                keys_to_remove = [k for k in self._requests.keys() if k[1] == region]
                for k in keys_to_remove:
                    del self._requests[k]
            else:
                self._requests.clear()


# Global rate limiter instance
rate_limiter = RateLimiter()


if __name__ == "__main__":
    # Test rate limiter
    print("Testing Rate Limiter...")
    print("="*60)
    
    # Simulate requests
    print("\nSimulating 5 requests for APEX:NA1...")
    for i in range(5):
        if rate_limiter.can_make_request('apex', 'na1'):
            rate_limiter.record_request('apex', 'na1')
            print(f"  ✅ Request {i+1} recorded")
        else:
            print(f"  ❌ Request {i+1} blocked (rate limited)")
    
    print("\nSimulating 3 requests for NEXUS:EUW1...")
    for i in range(3):
        if rate_limiter.can_make_request('nexus', 'euw1'):
            rate_limiter.record_request('nexus', 'euw1')
            print(f"  ✅ Request {i+1} recorded")
        else:
            print(f"  ❌ Request {i+1} blocked (rate limited)")
    
    print("\nSimulating 2 requests for APEX:KR...")
    for i in range(2):
        if rate_limiter.can_make_request('apex', 'kr'):
            rate_limiter.record_request('apex', 'kr')
            print(f"  ✅ Request {i+1} recorded")
        else:
            print(f"  ❌ Request {i+1} blocked (rate limited)")
    
    # Show status
    print("\n" + "="*60)
    print("Rate Limit Status:")
    print("="*60)
    
    for status in rate_limiter.get_all_status():
        print(f"\n{status['key_type'].upper()}:{status['region'].upper()}")
        print(f"  Used: {status['used']}/{status['max']} ({status['percentage']:.1f}%)")
        print(f"  Remaining: {status['remaining']}")
    
    # Test wait functionality
    print("\n" + "="*60)
    print("Testing wait functionality...")
    print("="*60)
    
    # Fill up the limit
    print("\nFilling APEX:NA1 to limit (100 requests)...")
    for i in range(95):  # Already have 5
        rate_limiter.record_request('apex', 'na1')
    
    status = rate_limiter.get_status('apex', 'na1')
    print(f"Current: {status['used']}/{status['max']}")
    
    # Try one more (should hit limit)
    if rate_limiter.can_make_request('apex', 'na1'):
        print("✅ Can make request")
    else:
        print("❌ Rate limited!")
        wait_time = rate_limiter.wait_if_needed('apex', 'na1')
        print(f"Need to wait: {wait_time:.1f}s")
    
    print("\n✅ Rate limiter tests complete!")