"""
Neural Nexus v3.0 - APEX Seeder
Seeds Challenger players from all regions in parallel
"""

import sys
import os
from threading import Thread
from queue import Queue

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared.config.settings import settings
from shared.database.connection import db_pool
from services.shared.api.riot_client import RiotAPIClient
from database.operations.player_ops import insert_player
from database.operations.queue_ops import add_to_queue
from database.operations.status_ops import update_service_status


class ApexSeeder:
    """Seeds high-elo players (Challenger/Grandmaster) from all regions"""
    
    def __init__(self):
        self.api_client = RiotAPIClient('apex')
        self.total_seeded = 0
    
    def seed_region(self, region: str) -> int:
        """
        Seed Challenger players from one region
        
        Args:
            region: Region code (e.g., 'na1', 'euw1', 'kr')
        
        Returns:
            Number of players seeded
        """
        print(f"\n{'='*60}")
        print(f"[{region.upper()}] Seeding Challenger")
        print(f"{'='*60}")
        
        seeded_count = 0
        
        # Seed Challenger only
        print(f"[{region.upper()}] Fetching Challenger league...")
        challenger = self.api_client.get_challenger_league(region)
        
        if challenger and 'entries' in challenger:
            print(f"[{region.upper()}] Found {len(challenger['entries'])} Challenger players")
            seeded_count += self._process_league_entries(
                challenger['entries'],
                region,
                'CHALLENGER'
            )
        else:
            print(f"[{region.upper()}] ❌ Failed to fetch Challenger league")
        
        print(f"[{region.upper()}] ✅ Seeded {seeded_count} players")
        return seeded_count
    
    def _process_league_entries(self, entries: list, region: str, tier: str) -> int:
        """
        Process league entries and insert players
        
        Args:
            entries: League entries from API
            region: Region code
            tier: 'CHALLENGER'
        
        Returns:
            Number of players inserted
        """
        inserted = 0
        
        for i, entry in enumerate(entries, 1):
            try:
                # Extract PUUID from entry
                apex_puuid = entry.get('puuid')
                if not apex_puuid:
                    print(f"[{region.upper()}]   ⚠️  Entry {i}: No PUUID found")
                    continue
                
                # Get Riot ID from PUUID
                account_data = self.api_client.get_account_by_puuid(apex_puuid, region)
                
                if not account_data:
                    print(f"[{region.upper()}]   ⚠️  Entry {i}: Could not get Riot ID for PUUID")
                    continue
                
                game_name = account_data.get('gameName')
                tag_line = account_data.get('tagLine')
                
                if not game_name or not tag_line:
                    print(f"[{region.upper()}]   ⚠️  Entry {i}: Missing gameName or tagLine")
                    continue
                
                # Insert player
                success = insert_player(
                    region=region,
                    game_name=game_name,
                    tag_line=tag_line,
                    apex_puuid=apex_puuid,
                    tier=tier,
                    rank=entry.get('rank', 'I'),
                    league_points=entry.get('leaguePoints', 0),
                    wins=entry.get('wins', 0),
                    losses=entry.get('losses', 0),
                    league_id=entry.get('leagueId'),
                    discovered_by='apex',
                    is_seed_player=True
                )
                
                if success:
                    # Add to APEX collection queue
                    add_to_queue(region, game_name, tag_line, 'apex', priority=10)
                    inserted += 1
                    
                    # Show first player as verification
                    if inserted == 1:
                        print(f"[{region.upper()}]   First player: {game_name}#{tag_line}")
                    
                    if i % 50 == 0:
                        print(f"[{region.upper()}]   Processed {i}/{len(entries)}...")
                
                # Update status every 10 players
                if inserted % 10 == 0:
                    update_service_status(
                        service_name='apex',
                        players_processed=10,
                        api_calls_made=20  # 2 API calls per player (league + account)
                    )
            
            except Exception as e:
                print(f"[{region.upper()}]   ❌ Error processing entry {i}: {e}")
                continue
        
        return inserted
    
    def seed_all_regions_parallel(self) -> int:
        """
        Seed all configured regions in parallel using threads
        
        Returns:
            Total number of players seeded across all regions
        """
        print("="*60)
        print("APEX SEEDER - Seeding Challenger Players (Parallel)")
        print("="*60)
        print(f"Regions: {', '.join(settings.REGIONS)}")
        print(f"Mode: Parallel (all regions simultaneously)")
        
        # Results queue
        results = Queue()
        
        def seed_region_thread(region):
            """Thread function to seed one region - creates own API client"""
            try:
                # Each thread needs its own API client (not thread-safe to share)
                thread_client = RiotAPIClient('apex')
                # Temporarily swap the client
                original_client = self.api_client
                self.api_client = thread_client
                
                count = self.seed_region(region)
                results.put((region, count))
                
                # Cleanup
                thread_client.close()
                self.api_client = original_client
            except Exception as e:
                print(f"[{region.upper()}] ❌ Thread error: {e}")
                results.put((region, 0))
        
        # Create and start threads for each region
        threads = []
        for region in settings.REGIONS:
            thread = Thread(target=seed_region_thread, args=(region,))
            thread.start()
            threads.append(thread)
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Collect results
        total = 0
        region_counts = {}
        while not results.empty():
            region, count = results.get()
            region_counts[region] = count
            total += count
        
        print(f"\n{'='*60}")
        print(f"SEEDING COMPLETE")
        print(f"{'='*60}")
        for region, count in region_counts.items():
            print(f"  {region.upper()}: {count} players")
        print(f"  TOTAL: {total} players")
        print(f"  API calls: ~{total * 2}")
        
        return total
    
    def close(self):
        """Close API client"""
        self.api_client.close()


if __name__ == "__main__":
    # Test seeder
    print("Testing APEX Seeder (Parallel)...")
    print("="*60)
    
    db_pool.initialize()
    
    # Update status
    from database.operations.status_ops import mark_service_active
    mark_service_active('apex', 'seeding')
    
    # Create seeder
    seeder = ApexSeeder()
    
    # Seed all regions in parallel
    total = seeder.seed_all_regions_parallel()
    
    print(f"\n✅ Seeding complete! {total} players seeded.")
    
    # Check results
    from database.operations.player_ops import get_player_count, get_players_by_tier
    from database.operations.queue_ops import get_queue_depth
    
    print(f"\nDatabase stats:")
    print(f"  Total players: {get_player_count()}")
    print(f"  Challenger: {len(get_players_by_tier('CHALLENGER'))}")
    print(f"  APEX queue depth: {get_queue_depth('apex')}")
    
    # Cleanup
    seeder.close()
    db_pool.close()
    
    print("\n✅ APEX Seeder test complete!")