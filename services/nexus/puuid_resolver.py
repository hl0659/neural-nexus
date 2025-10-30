"""
Neural Nexus v3.0 - NEXUS PUUID Resolver
Resolves Riot IDs to NEXUS PUUIDs for players discovered by APEX
"""

import sys
import os
from typing import List, Dict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared.config.settings import settings
from shared.database.connection import db_pool
from services.shared.api.riot_client import RiotAPIClient
from database.operations.player_ops import get_players_without_nexus_puuid, update_nexus_puuid
from database.operations.status_ops import update_service_status


class NexusPUUIDResolver:
    """Resolves Riot IDs to NEXUS PUUIDs for players discovered by APEX"""
    
    def __init__(self):
        self.api_client = RiotAPIClient('nexus')
        self.resolved_count = 0
        self.failed_count = 0
        self.api_calls = 0
    
    def resolve_batch(self, batch_size: int = 100) -> Dict:
        """
        Resolve a batch of players
        
        Args:
            batch_size: Number of players to process
        
        Returns:
            Stats dict
        """
        # Get players that need NEXUS PUUID resolution
        players = get_players_without_nexus_puuid(limit=batch_size)
        
        if not players:
            return {
                'success': True,
                'players_found': 0,
                'resolved': 0,
                'failed': 0,
                'api_calls': 0
            }
        
        print(f"\n{'='*60}")
        print(f"NEXUS PUUID RESOLVER")
        print(f"{'='*60}")
        print(f"Found {len(players)} players needing NEXUS PUUID resolution")
        print(f"{'='*60}\n")
        
        stats = {
            'success': True,
            'players_found': len(players),
            'resolved': 0,
            'failed': 0,
            'api_calls': 0
        }
        
        for i, player in enumerate(players, 1):
            result = self._resolve_single_player(player.region, player.game_name, player.tag_line)
            
            if result['success']:
                stats['resolved'] += 1
                self.resolved_count += 1
            else:
                stats['failed'] += 1
                self.failed_count += 1
            
            stats['api_calls'] += result['api_calls']
            self.api_calls += result['api_calls']
            
            # Progress update every 20 players
            if i % 20 == 0:
                print(f"  Progress: {i}/{len(players)} ({stats['resolved']} resolved, {stats['failed']} failed)")
        
        # Update system status
        update_service_status(
            service_name='nexus',
            players_processed=stats['resolved'],
            api_calls_made=stats['api_calls']
        )
        
        print(f"\n✅ Batch complete: {stats['resolved']} resolved, {stats['failed']} failed")
        print(f"   API calls: {stats['api_calls']}")
        
        return stats
    
    def _resolve_single_player(self, region: str, game_name: str, tag_line: str) -> Dict:
        """
        Resolve NEXUS PUUID for a single player
        
        Args:
            region: Player region
            game_name: Player game name
            tag_line: Player tag line
        
        Returns:
            Result dict
        """
        result = {
            'success': False,
            'api_calls': 0,
            'error': None
        }
        
        try:
            # Get account info using NEXUS key (this gives us NEXUS-encrypted PUUID)
            account_data = self.api_client.get_account_by_riot_id(game_name, tag_line, region)
            result['api_calls'] += 1
            
            if not account_data:
                result['error'] = 'API returned no data'
                return result
            
            nexus_puuid = account_data.get('puuid')
            
            if not nexus_puuid:
                result['error'] = 'No PUUID in response'
                return result
            
            # Update database with NEXUS PUUID
            success = update_nexus_puuid(region, game_name, tag_line, nexus_puuid)
            
            if success:
                result['success'] = True
            else:
                result['error'] = 'Database update failed'
        
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def resolve_all(self, max_players: int = None) -> Dict:
        """
        Resolve all players that need NEXUS PUUIDs
        
        Args:
            max_players: Optional limit on total players to process
        
        Returns:
            Overall stats
        """
        print("\n" + "="*60)
        print("NEXUS PUUID RESOLVER - Resolving All Players")
        print("="*60)
        
        overall_stats = {
            'total_resolved': 0,
            'total_failed': 0,
            'total_api_calls': 0,
            'batches_processed': 0
        }
        
        processed = 0
        
        while True:
            # Check if we've hit the limit
            if max_players and processed >= max_players:
                print(f"\n⚠️  Reached max players limit ({max_players})")
                break
            
            # Calculate batch size
            remaining = max_players - processed if max_players else 100
            batch_size = min(100, remaining)
            
            # Process batch
            batch_stats = self.resolve_batch(batch_size=batch_size)
            
            if batch_stats['players_found'] == 0:
                print(f"\n✅ All players resolved!")
                break
            
            overall_stats['total_resolved'] += batch_stats['resolved']
            overall_stats['total_failed'] += batch_stats['failed']
            overall_stats['total_api_calls'] += batch_stats['api_calls']
            overall_stats['batches_processed'] += 1
            
            processed += batch_stats['players_found']
            
            # Small delay between batches
            import time
            time.sleep(0.5)
        
        print(f"\n{'='*60}")
        print("RESOLUTION COMPLETE")
        print(f"{'='*60}")
        print(f"  Total resolved: {overall_stats['total_resolved']}")
        print(f"  Total failed: {overall_stats['total_failed']}")
        print(f"  Total API calls: {overall_stats['total_api_calls']}")
        print(f"  Batches processed: {overall_stats['batches_processed']}")
        print(f"{'='*60}\n")
        
        return overall_stats
    
    def get_stats(self) -> Dict:
        """Get resolver statistics"""
        return {
            'resolved': self.resolved_count,
            'failed': self.failed_count,
            'api_calls': self.api_calls
        }
    
    def close(self):
        """Close API client"""
        self.api_client.close()


if __name__ == "__main__":
    # Test PUUID resolver
    print("Testing NEXUS PUUID Resolver...")
    print("="*60)
    
    db_pool.initialize()
    
    # Check how many players need resolution
    from database.operations.player_ops import get_players_without_nexus_puuid
    
    players_needing_resolution = get_players_without_nexus_puuid(limit=1000)
    
    print(f"\nPlayers needing NEXUS PUUID: {len(players_needing_resolution)}")
    
    if not players_needing_resolution:
        print("✅ No players need resolution!")
        db_pool.close()
        exit(0)
    
    # Show sample of players
    print(f"\nSample players:")
    for player in players_needing_resolution[:5]:
        print(f"  - {player.game_name}#{player.tag_line} ({player.tier or 'UNRANKED'})")
    
    # Ask user to confirm
    print(f"\nResolve {len(players_needing_resolution)} players? (y/n): ", end='')
    response = input().lower().strip()
    
    if response != 'y':
        print("❌ Resolution cancelled")
        db_pool.close()
        exit(0)
    
    # Create resolver and process all players
    resolver = NexusPUUIDResolver()
    
    overall_stats = resolver.resolve_all()
    
    # Check results
    from database.operations.player_ops import get_player_count
    
    remaining = len(get_players_without_nexus_puuid(limit=1000))
    
    print(f"Database stats:")
    print(f"  Total players: {get_player_count()}")
    print(f"  Still need resolution: {remaining}")
    
    # Cleanup
    resolver.close()
    db_pool.close()
    
    print("\n✅ NEXUS PUUID Resolver test complete!")