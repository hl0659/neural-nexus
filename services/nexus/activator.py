"""
Neural Nexus v3.0 - NEXUS Activator
Monitors NEXUS queue and auto-resolves PUUIDs before collection
"""

import sys
import os
import time
from typing import Optional, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared.database.connection import db_pool
from services.shared.api.riot_client import RiotAPIClient
from database.operations.player_ops import get_player, update_nexus_puuid
from database.operations.queue_ops import get_next_from_queue, mark_queue_error
from services.shared.models.player import Player


class NexusActivator:
    """
    Monitors NEXUS queue and ensures players have nexus_puuid before collection
    """
    
    def __init__(self):
        self.api_client = RiotAPIClient('nexus')
        self.resolved_count = 0
        self.api_calls = 0
    
    def get_next_ready_player(self, region: Optional[str] = None) -> Optional[Player]:
        """
        Get next player from NEXUS queue, resolving PUUID if needed
        
        Args:
            region: Optional - filter by specific region
        
        Returns:
            Player with nexus_puuid, or None if queue empty
        """
        max_attempts = 10
        attempts = 0
        
        while attempts < max_attempts:
            # Get next player from queue
            players = get_next_from_queue('nexus', limit=1)
            
            if not players:
                return None
            
            player = players[0]
            
            # Filter by region if specified
            if region and player.region != region:
                attempts += 1
                continue
            
            # Check if player has nexus_puuid
            if player.nexus_puuid:
                # Ready to collect!
                return player
            
            # Need to resolve PUUID
            print(f"[NEXUS:{player.region.upper()}] Resolving PUUID for {player.game_name}#{player.tag_line}...")
            
            resolved = self._resolve_puuid(player.region, player.game_name, player.tag_line)
            
            if resolved:
                # Refresh player from database with new PUUID
                player = get_player(player.region, player.game_name, player.tag_line)
                return player
            else:
                # Failed to resolve - mark error and try next player
                mark_queue_error(
                    player.region,
                    player.game_name,
                    player.tag_line,
                    'nexus',
                    'Failed to resolve NEXUS PUUID'
                )
                attempts += 1
                continue
        
        return None
    
    def _resolve_puuid(self, region: str, game_name: str, tag_line: str) -> bool:
        """
        Resolve NEXUS PUUID for a player
        
        Args:
            region: Player region
            game_name: Player game name  
            tag_line: Player tag line
        
        Returns:
            True if resolved successfully
        """
        try:
            # Get account info using NEXUS key
            account_data = self.api_client.get_account_by_riot_id(game_name, tag_line, region)
            self.api_calls += 1
            
            if not account_data:
                print(f"  ❌ Failed to get account data")
                return False
            
            nexus_puuid = account_data.get('puuid')
            
            if not nexus_puuid:
                print(f"  ❌ No PUUID in response")
                return False
            
            # Update database
            success = update_nexus_puuid(region, game_name, tag_line, nexus_puuid)
            
            if success:
                print(f"  ✅ Resolved NEXUS PUUID")
                self.resolved_count += 1
                return True
            else:
                print(f"  ❌ Database update failed")
                return False
        
        except Exception as e:
            print(f"  ❌ Exception: {e}")
            return False
    
    def resolve_batch(self, batch_size: int = 50, region: Optional[str] = None) -> int:
        """
        Pre-resolve a batch of players from queue
        
        Args:
            batch_size: Number of players to resolve
            region: Optional region filter
        
        Returns:
            Number of players resolved
        """
        print(f"\n[NEXUS] Pre-resolving batch of {batch_size} players...")
        
        from database.operations.player_ops import get_players_without_nexus_puuid
        
        # Get players needing resolution
        players = get_players_without_nexus_puuid(limit=batch_size)
        
        if region:
            players = [p for p in players if p.region == region]
        
        if not players:
            print(f"  ✅ No players need resolution")
            return 0
        
        resolved = 0
        for player in players:
            if self._resolve_puuid(player.region, player.game_name, player.tag_line):
                resolved += 1
            
            # Small delay to respect rate limits
            time.sleep(0.1)
        
        print(f"  ✅ Resolved {resolved}/{len(players)} players")
        return resolved
    
    def get_stats(self):
        """Get activator statistics"""
        return {
            'resolved': self.resolved_count,
            'api_calls': self.api_calls
        }
    
    def close(self):
        """Close API client"""
        self.api_client.close()


if __name__ == "__main__":
    # Test activator
    print("Testing NEXUS Activator...")
    print("="*60)
    
    db_pool.initialize()
    
    # Check queue
    from database.operations.queue_ops import get_queue_depth
    from database.operations.player_ops import get_players_without_nexus_puuid
    
    queue_depth = get_queue_depth('nexus')
    need_resolution = len(get_players_without_nexus_puuid(limit=1000))
    
    print(f"\nNEXUS Queue depth: {queue_depth}")
    print(f"Players needing resolution: {need_resolution}")
    
    if need_resolution == 0:
        print("✅ All players already have NEXUS PUUID!")
        db_pool.close()
        exit(0)
    
    # Create activator
    activator = NexusActivator()
    
    # Test getting ready player (should auto-resolve)
    print("\nTest 1: Getting next ready player (auto-resolve)...")
    player = activator.get_next_ready_player()
    
    if player:
        print(f"✅ Got player: {player.game_name}#{player.tag_line}")
        print(f"   Has NEXUS PUUID: {player.has_nexus_puuid()}")
    else:
        print("❌ No player available")
    
    # Test batch resolution
    print("\nTest 2: Batch resolving 10 players...")
    resolved = activator.resolve_batch(batch_size=10)
    print(f"✅ Resolved {resolved} players")
    
    # Check stats
    stats = activator.get_stats()
    print(f"\nActivator stats:")
    print(f"  Total resolved: {stats['resolved']}")
    print(f"  API calls: {stats['api_calls']}")
    
    # Cleanup
    activator.close()
    db_pool.close()
    
    print("\n✅ NEXUS Activator test complete!")