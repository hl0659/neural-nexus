"""
Neural Nexus v3.0 - Unified Parallel Collection Runner (with Progress Tracking)
Runs APEX collection, automatically falls back to NEXUS queue when APEX is empty
Includes graceful shutdown and progress persistence
"""

import sys
import os
import time
from datetime import datetime, timedelta
from threading import Thread, Lock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared.config.settings import settings
from shared.database.connection import db_pool
from services.apex.collector import ApexCollector
from services.nexus.collector import NexusCollector
from services.shared.utils.progress_tracker import ProgressTracker
from services.shared.utils.signal_handler import GracefulShutdown
from database.operations.queue_ops import get_next_from_queue, mark_queue_processing, mark_queue_complete, mark_queue_error, get_queue_depth
from database.operations.status_ops import mark_service_active, update_service_status


class UnifiedCollectionRunner:
    """Runs collection with automatic APEX → NEXUS fallback"""
    
    def __init__(self, duration_hours: float):
        self.duration_hours = duration_hours
        self.end_time = datetime.now() + timedelta(hours=duration_hours)
        self.should_stop = False
        
        # Progress tracking
        self.progress = ProgressTracker('unified')
        
        # Graceful shutdown
        self.shutdown_handler = GracefulShutdown(self._on_shutdown)
        
        # Thread-safe stats
        self.stats_lock = Lock()
        self.apex_players = 0
        self.nexus_players = 0
        self.apex_matches = 0
        self.nexus_matches = 0
        self.total_api_calls = 0
        self.errors = 0
        
        # Per-region stats
        self.region_stats = {
            region: {
                'apex_players': 0,
                'nexus_players': 0,
                'apex_matches': 0,
                'nexus_matches': 0
            } for region in settings.REGIONS
        }
    
    def _on_shutdown(self):
        """Called when shutdown is requested"""
        print("\n  → Stopping collection threads...")
        self.should_stop = True
        
        print("  → Saving progress...")
        self.progress.save()
        
        print("  → Updating database status...")
        try:
            update_service_status('apex', is_active=False, current_phase='interrupted')
            update_service_status('nexus', is_active=False, current_phase='interrupted')
        except:
            pass
        
        print("  ✓ Shutdown complete!")
    
    def update_stats(self, region: str, service: str, players: int = 0, 
                    matches: int = 0, api_calls: int = 0, errors: int = 0):
        """Thread-safe stats update"""
        with self.stats_lock:
            if service == 'apex':
                self.apex_players += players
                self.apex_matches += matches
                self.region_stats[region]['apex_players'] += players
                self.region_stats[region]['apex_matches'] += matches
            else:  # nexus
                self.nexus_players += players
                self.nexus_matches += matches
                self.region_stats[region]['nexus_players'] += players
                self.region_stats[region]['nexus_matches'] += matches
            
            self.total_api_calls += api_calls
            self.errors += errors
            
            # Update progress tracker
            self.progress.update(
                region=region,
                players=players,
                matches=matches,
                api_calls=api_calls,
                errors=errors
            )
    
    def print_stats(self):
        """Print current statistics"""
        with self.stats_lock:
            time_remaining = self.end_time - datetime.now()
            hours_remaining = max(0, time_remaining.total_seconds() / 3600)
            
            print(f"\n{'='*60}")
            print(f"UNIFIED COLLECTION STATS")
            print(f"{'='*60}")
            print(f"  APEX:")
            print(f"    Players: {self.apex_players}")
            print(f"    Matches: {self.apex_matches}")
            print(f"  NEXUS:")
            print(f"    Players: {self.nexus_players}")
            print(f"    Matches: {self.nexus_matches}")
            print(f"  TOTAL:")
            print(f"    Players: {self.apex_players + self.nexus_players}")
            print(f"    Matches: {self.apex_matches + self.nexus_matches}")
            print(f"    API calls: {self.total_api_calls}")
            print(f"    Errors: {self.errors}")
            print(f"    Time remaining: {hours_remaining:.2f} hours")
            print(f"\n  Per-region breakdown:")
            for region, stats in self.region_stats.items():
                total_players = stats['apex_players'] + stats['nexus_players']
                total_matches = stats['apex_matches'] + stats['nexus_matches']
                print(f"    {region.upper()}: {total_players} players, {total_matches} matches")
                print(f"      (APEX: {stats['apex_matches']}, NEXUS: {stats['nexus_matches']})")
            print(f"{'='*60}\n")
    
    def process_region(self, region: str):
        """Process players from one region with APEX → NEXUS fallback"""
        # Each thread gets its own collectors
        apex_collector = ApexCollector()
        nexus_collector = NexusCollector()
        
        region_players = 0
        consecutive_empty_checks = 0
        
        print(f"[{region.upper()}] Thread started (unified mode)")
        
        try:
            while datetime.now() < self.end_time and not self.should_stop and not self.shutdown_handler.should_stop():
                # Check queue depths
                apex_depth = get_queue_depth('apex')
                nexus_depth = get_queue_depth('nexus')
                
                # Try APEX first
                players = get_next_from_queue('apex', limit=1)
                service = 'apex'
                collector = apex_collector
                
                # Fallback to NEXUS if APEX is empty
                if not players:
                    players = get_next_from_queue('nexus', limit=1)
                    service = 'nexus'
                    collector = nexus_collector
                
                if not players:
                    consecutive_empty_checks += 1
                    
                    if consecutive_empty_checks == 1:
                        print(f"[{region.upper()}] Both queues empty (APEX: {apex_depth}, NEXUS: {nexus_depth})")
                    
                    if consecutive_empty_checks >= 6:  # 3 minutes of empty
                        print(f"[{region.upper()}] No work for 3 minutes, stopping thread")
                        break
                    
                    time.sleep(30)
                    continue
                
                consecutive_empty_checks = 0
                player = players[0]
                
                # Skip if not from our region
                if player.region != region:
                    continue
                
                # Mark as processing
                mark_queue_processing(player.region, player.game_name, player.tag_line, service)
                
                print(f"[{service.upper()}:{region.upper()}] Processing {player.game_name}#{player.tag_line} ({player.tier})...")
                
                try:
                    # Collect matches
                    stats = collector.collect_player_matches(
                        region=player.region,
                        game_name=player.game_name,
                        tag_line=player.tag_line
                    )
                    
                    if stats['success']:
                        mark_queue_complete(player.region, player.game_name, player.tag_line, service)
                        
                        region_players += 1
                        self.update_stats(
                            region=region,
                            service=service,
                            players=1,
                            matches=stats['matches_collected'],
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
                            service,
                            stats.get('error', 'Unknown error')
                        )
                        self.update_stats(region=region, service=service, errors=1)
                
                except Exception as e:
                    print(f"[{service.upper()}:{region.upper()}] ❌ Error processing {player.game_name}#{player.tag_line}: {e}")
                    mark_queue_error(
                        player.region,
                        player.game_name,
                        player.tag_line,
                        service,
                        str(e)
                    )
                    self.update_stats(region=region, service=service, errors=1)
        
        finally:
            apex_collector.close()
            nexus_collector.close()
            print(f"[{region.upper()}] Thread finished - {region_players} players processed")
    
    def run(self):
        """Run unified collection"""
        print("="*60)
        print("UNIFIED PARALLEL COLLECTION RUNNER")
        print("="*60)
        print(f"Duration: {self.duration_hours} hours")
        print(f"Regions: {', '.join(settings.REGIONS)}")
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"End time: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Mode: Unified (APEX → NEXUS fallback)")
        print(f"Progress tracking: ENABLED")
        print(f"Graceful shutdown: ENABLED (Ctrl+C to stop)")
        print("="*60)
        
        # Load previous progress if exists
        if self.progress.stats['players_processed'] > 0:
            print("\n⚠️  Found previous progress!")
            self.progress.print_summary()
            response = input("Resume from previous session? (yes/no): ")
            if response.lower() != 'yes':
                self.progress.reset()
                print("✓ Starting fresh session")
        
        # Check initial queue depths
        print("\nInitial Queue Status:")
        apex_depth = get_queue_depth('apex')
        nexus_depth = get_queue_depth('nexus')
        print(f"  APEX: {apex_depth} players")
        print(f"  NEXUS: {nexus_depth} players")
        print(f"  TOTAL: {apex_depth + nexus_depth} players")
        print("="*60)
        
        # Initialize database
        db_pool.initialize()
        mark_service_active('apex', 'unified_collection')
        mark_service_active('nexus', 'unified_collection')
        
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
            print("\n\n⚠️  Shutdown in progress...")
            # Shutdown handler already called via signal
        
        finally:
            # Final stats
            print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.print_stats()
            self.progress.print_summary()
            
            # Update service status
            update_service_status(
                service_name='apex',
                is_active=False,
                current_phase='idle',
                matches_collected=self.apex_matches
            )
            update_service_status(
                service_name='nexus',
                is_active=False,
                current_phase='idle',
                matches_collected=self.nexus_matches
            )
            
            # Show final database stats
            from database.operations.match_ops import get_match_count, get_matches_by_service
            from database.operations.player_ops import get_player_count
            
            print(f"\nFinal database stats:")
            print(f"  Total players: {get_player_count()}")
            print(f"  Total matches: {get_match_count()}")
            print(f"  APEX matches: {get_matches_by_service('apex')}")
            print(f"  NEXUS matches: {get_matches_by_service('nexus')}")
            
            db_pool.close()
            
            print("\n✅ Unified collection runner finished!")
            print(f"Progress saved to: {self.progress.progress_file}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run unified collection (APEX + NEXUS)')
    parser.add_argument(
        '--hours',
        type=float,
        default=2.0,
        help='Number of hours to run (default: 2.0)'
    )
    
    args = parser.parse_args()
    
    runner = UnifiedCollectionRunner(duration_hours=args.hours)
    runner.run()