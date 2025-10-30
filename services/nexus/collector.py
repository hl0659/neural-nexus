"""
Neural Nexus v3.0 - NEXUS Collector
Collects 200 games of match history for network-discovered players
"""

import sys
import os
from typing import Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared.config.settings import settings
from shared.database.connection import db_pool
from services.shared.api.riot_client import RiotAPIClient
from services.shared.storage.json_handler import json_handler
from services.shared.storage.match_lock import match_lock
from database.operations.player_ops import get_player, update_nexus_check
from database.operations.match_ops import insert_match, match_exists
from database.operations.status_ops import update_service_status
from services.nexus.player_processor import NexusPlayerProcessor


class NexusCollector:
    """Collects deep match history (200 games) for network-discovered players"""
    
    def __init__(self):
        self.api_client = RiotAPIClient('nexus')
        self.player_processor = NexusPlayerProcessor()
        self.matches_collected = 0
        self.matches_skipped = 0
        self.api_calls = 0
    
    def collect_player_matches(self, region: str, game_name: str, tag_line: str) -> dict:
        """
        Collect all matches for one player
        
        Args:
            region: Player region
            game_name: Player game name
            tag_line: Player tag line
        
        Returns:
            Dict with collection stats
        """
        # Get player from database
        player = get_player(region, game_name, tag_line)
        
        if not player:
            return {'success': False, 'error': 'Player not found in database'}
        
        if not player.nexus_puuid:
            return {'success': False, 'error': 'Player missing NEXUS PUUID'}
        
        print(f"\n{'='*60}")
        print(f"[NEXUS:{region.upper()}] Collecting matches for {game_name}#{tag_line}")
        print(f"{'='*60}")
        
        stats = {
            'success': True,
            'player': f"{game_name}#{tag_line}",
            'region': region,
            'matches_found': 0,
            'matches_collected': 0,
            'matches_skipped': 0,
            'api_calls': 0
        }
        
        # Get match history (200 games in 2 batches of 100)
        print(f"Fetching match history (up to 200 games)...")
        match_ids = []

        # First 100 matches
        batch1 = self.api_client.get_match_history(
            puuid=player.nexus_puuid,
            platform=region,
            count=100,
            start=0
        )
        stats['api_calls'] += 1
        self.api_calls += 1

        if batch1:
            match_ids.extend(batch1)

        # Next 100 matches
        batch2 = self.api_client.get_match_history(
            puuid=player.nexus_puuid,
            platform=region,
            count=100,
            start=100
        )
        stats['api_calls'] += 1
        self.api_calls += 1

        if batch2:
            match_ids.extend(batch2)
        
        if not match_ids:
            print(f"⚠️  No match history found")
            return stats
        
        stats['matches_found'] = len(match_ids)
        print(f"Found {len(match_ids)} matches")
        
        # Collect each match
        for i, match_id in enumerate(match_ids, 1):
            result = self._collect_single_match(match_id, region)
            
            if result['collected']:
                stats['matches_collected'] += 1
                self.matches_collected += 1
            else:
                stats['matches_skipped'] += 1
                self.matches_skipped += 1
            
            stats['api_calls'] += result['api_calls']
            self.api_calls += result['api_calls']
            
            # Progress update every 20 matches
            if i % 20 == 0:
                print(f"  Progress: {i}/{len(match_ids)} ({stats['matches_collected']} collected, {stats['matches_skipped']} skipped)")
        
        # Update player's last check
        update_nexus_check(region, game_name, tag_line, match_count=stats['matches_collected'])
        
        # Update system status
        update_service_status(
            service_name='nexus',
            players_processed=1,
            matches_collected=stats['matches_collected'],
            api_calls_made=stats['api_calls']
        )
        
        print(f"\n✅ Complete: {stats['matches_collected']} collected, {stats['matches_skipped']} skipped")
        
        return stats
    
    def _collect_single_match(self, match_id: str, region: str) -> dict:
        """
        Collect a single match with locking
        
        Args:
            match_id: Match ID
            region: Region code
        
        Returns:
            Dict with collection result
        """
        result = {
            'collected': False,
            'api_calls': 0,
            'reason': None
        }
        
        # Check if already in database
        if match_exists(match_id):
            result['reason'] = 'already_in_db'
            return result
        
        # Try to acquire lock
        if not match_lock.try_acquire(match_id, 'nexus'):
            result['reason'] = 'locked_by_other'
            return result
        
        try:
            # Fetch match data
            match_data = self.api_client.get_match(match_id, region)
            result['api_calls'] += 1
            
            if not match_data:
                result['reason'] = 'api_error'
                match_lock.release(match_id)
                return result
            
            # Fetch timeline
            timeline_data = self.api_client.get_timeline(match_id, region)
            result['api_calls'] += 1
            
            if not timeline_data:
                result['reason'] = 'timeline_error'
                match_lock.release(match_id)
                return result
            
            # Save to storage
            match_path, timeline_path = json_handler.save_match(
                match_data,
                timeline_data,
                region,
                'nexus'
            )
            
            # Extract match metadata
            info = match_data.get('info', {})
            game_version = info.get('gameVersion', 'unknown')
            game_duration = info.get('gameDuration', 0)
            game_creation = info.get('gameCreation', 0)
            game_mode = info.get('gameMode', 'CLASSIC')
            
            # Get patch (e.g., "13.24" from "13.24.1.1234")
            patch = '.'.join(game_version.split('.')[:2]) if '.' in game_version else game_version
            
            # Save to database
            success = insert_match(
                match_id=match_id,
                region=region,
                collected_by='nexus',
                game_version=game_version,
                game_duration=game_duration,
                game_creation=game_creation,
                patch=patch,
                game_mode=game_mode,
                json_path=match_path,
                timeline_json_path=timeline_path
            )
            
            if success:
                # Process participants (extract all 10 players)
                participant_stats = self.player_processor.process_match_participants(match_data, region)
                
                result['collected'] = True
                result['reason'] = 'success'
                result['participants_processed'] = participant_stats['participants_processed']
                result['players_discovered'] = participant_stats['players_discovered']
                result['api_calls'] += participant_stats['api_calls']
            else:
                result['reason'] = 'db_insert_failed'

            # Release lock (match collected successfully)
            match_lock.release(match_id)
        
        except Exception as e:
            result['reason'] = f'exception: {str(e)}'
            match_lock.release(match_id)
        
        return result
    
    def get_stats(self) -> dict:
        """Get collector statistics"""
        return {
            'matches_collected': self.matches_collected,
            'matches_skipped': self.matches_skipped,
            'api_calls': self.api_calls
        }
    
    def close(self):
        """Close API client"""
        self.api_client.close()
        self.player_processor.close()


if __name__ == "__main__":
    # Test collector on a single player
    print("Testing NEXUS Collector...")
    print("="*60)
    
    db_pool.initialize()
    
    # Get first player from NEXUS queue
    from database.operations.queue_ops import get_next_from_queue
    
    players = get_next_from_queue('nexus', limit=1)
    
    if not players:
        print("❌ No players in NEXUS queue. APEX needs to discover players first!")
        db_pool.close()
        exit(1)
    
    player = players[0]
    
    # Check if player has nexus_puuid
    if not player.nexus_puuid:
        print(f"⚠️  Player {player} missing NEXUS PUUID. Run PUUID resolver first!")
        db_pool.close()
        exit(1)
    
    print(f"\nTesting with player: {player}")
    
    # Create collector
    collector = NexusCollector()
    
    # Collect matches for this player
    stats = collector.collect_player_matches(
        region=player.region,
        game_name=player.game_name,
        tag_line=player.tag_line
    )
    
    print(f"\n{'='*60}")
    print("Collection Stats:")
    print(f"{'='*60}")
    print(f"  Matches found: {stats['matches_found']}")
    print(f"  Matches collected: {stats['matches_collected']}")
    print(f"  Matches skipped: {stats['matches_skipped']}")
    print(f"  API calls made: {stats['api_calls']}")
    
    # Check database
    from database.operations.match_ops import get_match_count, get_matches_by_service
    
    print(f"\nDatabase stats:")
    print(f"  Total matches: {get_match_count()}")
    print(f"  APEX matches: {get_matches_by_service('apex')}")
    print(f"  NEXUS matches: {get_matches_by_service('nexus')}")
    
    # Cleanup
    collector.close()
    db_pool.close()
    
    print("\n✅ NEXUS Collector test complete!")