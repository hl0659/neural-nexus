"""
Neural Nexus v3.0 - APEX Parallel Collection Runner
Runs collection for all regions in parallel for maximum throughput
"""

import sys
import os
import time
from datetime import datetime, timedelta
from threading import Thread, Lock
from queue import Queue

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared.config.settings import settings
from shared.database.connection import db_pool
from services.apex.collector import ApexCollector
from database.operations.queue_ops import get_next_from_queue, mark_queue_processing, mark_queue_complete, mark_queue_error
from database.operations.status_ops import mark_service_active, update_service_status


class ParallelCollectionRunner:
    """Runs collection across all regions in parallel"""
    
    def __init__(self, duration_hours: float):
        self.duration_hours = duration_hours
        self.end_time = datetime.now() + timedelta(hours=duration_hours)
        self.should_stop = False
        
        # Thread-safe stats
        self.stats_lock = Lock()
        self.players_processed = 0
        self.total_matches_collected = 0
        self.total_matches_skipped = 0
        self.total_api_calls = 0
        self.errors = 0
        
        # Per-region stats
        self.region_stats = {region: {'players': 0, 'matches': 0} for region in settings.REGIONS}
    
    def update_stats(self, region: str, players: int = 0, matches_collected: int = 0, 
                    matches_skipped: int = 0, api_calls: int = 0, errors: int = 0):
        """Thread-safe stats update"""
        with self.stats_lock:
            self.players_processed += players
            self.total_matches_collected += matches_collected
            self.total_matches_skipped += matches_skipped
            self.total_api_calls += api_calls
            self.errors += errors
            
            if region in self.region_stats:
                self.region_stats[region]['players'] += players
                self.region_stats[region]['matches'] += matches_collected
    
    def print_stats(self):
        """Print current statistics"""
        with self.stats_lock:
            time_remaining = self.end_time - datetime.now()
            hours_remaining = max(0, time_remaining.total_seconds() / 3600)
            
            print(f"\n{'='*60}")
            print(f"SESSION STATS")
            print(f"{'='*60}")
            print(f"  Players processed: {self.players_processed}")
            print(f"  Matches collected: {self.total_matches_collected}")
            print(f"  Matches skipped: {self.total_matches_skipped}")
            print(f"  API calls made: {self.total_api_calls}")
            print(f"  Errors: {self.errors}")
            print(f"  Time remaining: {hours_remaining:.2f} hours")
            print(f"\n  Per-region breakdown:")
            for region, stats in self.region_stats.items():
                print(f"    {region.upper()}: {stats['players']} players, {stats['matches']} matches")
            print(f"{'='*60}\n")
    
    def process_region(self, region: str):
        """Process players from one region's queue"""
        # Each thread gets its own collector (not thread-safe to share)
        collector = ApexCollector()
        
        region_players = 0
        
        print(f"[{region.upper()}] Thread started")
        
        try:
            while datetime.now() < self.end_time and not self.should_stop:
                # Get next player from this region's queue
                players = get_next_from_queue('apex', limit=1)
                
                if not players:
                    print(f"[{region.upper()}] Queue empty, waiting 30 seconds...")
                    time.sleep(30)
                    continue
                
                player = players[0]
                
                # Skip if not from our region (another thread might grab it)
                if player.region != region:
                    continue
                
                # Mark as processing
                mark_queue_processing(player.region, player.game_name, player.tag_line, 'apex')
                
                try:
                    # Collect matches
                    stats = collector.collect_player_matches(
                        region=player.region,
                        game_name=player.game_name,
                        tag_line=player.tag_line
                    )
                    
                    if stats['success']:
                        mark_queue_complete(player.region, player.game_name, player.tag_line, 'apex')
                        
                        region_players += 1
                        self.update_stats(
                            region=region,
                            players=1,
                            matches_collected=stats['matches_collected'],
                            matches_skipped=stats['matches_skipped'],
                            api_calls=stats['api_calls']
                        )
                        
                        # Print stats every 5 players
                        if region_players % 5 == 0:
                            self.print_stats()
                    
                    else:
                        mark_queue_error(
                            player.region,
                            player.game_name,
                            player.tag_line,
                            'apex',
                            stats.get('error', 'Unknown error')
                        )
                        self.update_stats(region=region, errors=1)
                
                except Exception as e:
                    print(f"[{region.upper()}] ❌ Error processing {player.game_name}#{player.tag_line}: {e}")
                    mark_queue_error(
                        player.region,
                        player.game_name,
                        player.tag_line,
                        'apex',
                        str(e)
                    )
                    self.update_stats(region=region, errors=1)
        
        finally:
            collector.close()
            print(f"[{region.upper()}] Thread finished - {region_players} players processed")
    
    def run(self):
        """Run parallel collection"""
        print("="*60)
        print("APEX PARALLEL COLLECTION RUNNER")
        print("="*60)
        print(f"Duration: {self.duration_hours} hours")
        print(f"Regions: {', '.join(settings.REGIONS)}")
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"End time: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Mode: Parallel (all regions simultaneously)")
        print("="*60)
        
        # Initialize database
        db_pool.initialize()
        mark_service_active('apex', 'collecting_parallel')
        
        # Create threads for each region
        threads = []
        for region in settings.REGIONS:
            thread = Thread(target=self.process_region, args=(region,))
            thread.start()
            threads.append(thread)
        
        try:
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            print("\n" + "="*60)
            print("COLLECTION COMPLETE")
            print("="*60)
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Collection interrupted by user")
            self.should_stop = True
            
            # Wait for threads to finish
            for thread in threads:
                thread.join(timeout=5)
        
        finally:
            # Final stats
            print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.print_stats()
            
            # Update service status
            update_service_status(
                service_name='apex',
                is_active=False,
                current_phase='idle'
            )
            
            # Show final database stats
            from database.operations.match_ops import get_match_count, get_matches_by_service
            from database.operations.player_ops import get_player_count
            
            print(f"\nFinal database stats:")
            print(f"  Total players: {get_player_count()}")
            print(f"  Total matches: {get_match_count()}")
            print(f"  APEX matches: {get_matches_by_service('apex')}")
            
            db_pool.close()
            
            print("\n✅ Parallel collection runner finished!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run APEX collection in parallel for all regions')
    parser.add_argument(
        '--hours',
        type=float,
        default=5.0,
        help='Number of hours to run (default: 5.0)'
    )
    
    args = parser.parse_args()
    
    runner = ParallelCollectionRunner(duration_hours=args.hours)
    runner.run()