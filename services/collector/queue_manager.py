from datetime import datetime, timedelta
from typing import Optional, Dict
from shared.database.connection import db_pool

class QueueManager:
    """Manages player collection queue with tier-based priorities"""
    
    # Recheck intervals by tier (in days)
    TIER_INTERVALS = {
        'CHALLENGER': 2,
        'GRANDMASTER': 3,
        'MASTER': 4,
        'DIAMOND': 5,
        'EMERALD': 7,
        'PLATINUM': 10,
        'GOLD': 14,
        'SILVER': 14,
        'BRONZE': 14,
        'IRON': 14
    }
    
    # Tier priority order (highest to lowest)
    TIER_ORDER = [
        'CHALLENGER',
        'GRANDMASTER', 
        'MASTER',
        'DIAMOND',
        'EMERALD',
        'PLATINUM',
        'GOLD',
        'SILVER',
        'BRONZE',
        'IRON'
    ]
    
    def get_next_player(self, region: str) -> Optional[Dict]:
        """
        Get next player to check using tier cascading.
        Tries each tier in priority order until finding a due player.
        """
        with db_pool.get_cursor() as cursor:
            # Try each tier in order
            for tier in self.TIER_ORDER:
                cursor.execute("""
                    SELECT * FROM players 
                    WHERE next_check_after < CURRENT_TIMESTAMP 
                      AND region = %s
                      AND tier = %s
                    ORDER BY next_check_after ASC
                    LIMIT 1
                """, (region, tier))
                
                player = cursor.fetchone()
                if player:
                    return player
            
            # No one due in any tier
            return None
    
    def get_oldest_checked_player(self, region: str) -> Optional[Dict]:
        """
        Fallback: Get player checked longest ago.
        Used when queue is empty to prevent idle collector.
        """
        with db_pool.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM players
                WHERE region = %s
                ORDER BY next_check_after ASC
                LIMIT 1
            """, (region,))
            
            return cursor.fetchone()
    
    def update_player_checked(self, puuid: str, last_match_id: Optional[str], tier: str):
        """
        Update player after checking, setting next check time based on tier.
        """
        interval_days = self.TIER_INTERVALS.get(tier, 14)
        next_check = datetime.now() + timedelta(days=interval_days)
        
        with db_pool.get_cursor() as cursor:
            cursor.execute("""
                UPDATE players 
                SET last_match_id = %s,
                    next_check_after = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE puuid = %s
            """, (last_match_id, next_check, puuid))
    
    def boost_player_priority(self, puuid: str):
        """
        Boost active player priority - check them sooner.
        Called when player has 20+ new matches.
        """
        next_check = datetime.now() + timedelta(hours=12)
        
        with db_pool.get_cursor() as cursor:
            cursor.execute("""
                UPDATE players
                SET next_check_after = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE puuid = %s
            """, (next_check, puuid))
    
    def get_queue_stats(self, region: Optional[str] = None) -> Dict:
        """Get queue statistics"""
        with db_pool.get_cursor() as cursor:
            if region:
                cursor.execute("""
                    SELECT 
                        tier,
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE next_check_after < CURRENT_TIMESTAMP) as due
                    FROM players
                    WHERE region = %s
                    GROUP BY tier
                    ORDER BY 
                        CASE tier
                            WHEN 'CHALLENGER' THEN 1
                            WHEN 'GRANDMASTER' THEN 2
                            WHEN 'MASTER' THEN 3
                            WHEN 'DIAMOND' THEN 4
                            WHEN 'EMERALD' THEN 5
                            ELSE 6
                        END
                """, (region,))
            else:
                cursor.execute("""
                    SELECT 
                        tier,
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE next_check_after < CURRENT_TIMESTAMP) as due
                    FROM players
                    GROUP BY tier
                    ORDER BY 
                        CASE tier
                            WHEN 'CHALLENGER' THEN 1
                            WHEN 'GRANDMASTER' THEN 2
                            WHEN 'MASTER' THEN 3
                            WHEN 'DIAMOND' THEN 4
                            WHEN 'EMERALD' THEN 5
                            ELSE 6
                        END
                """)
            
            return cursor.fetchall()