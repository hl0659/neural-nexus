import time
import signal
import sys
from threading import Thread, Event
from shared.config.settings import settings
from shared.database.connection import db_pool
from shared.database.match_ops import insert_match
from services.collector.api.riot_client import RiotAPIClient
from services.collector.storage.json_handler import JSONStorageHandler
from services.collector.queue_manager import QueueManager
from services.collector.match_scanner import MatchScanner
from services.collector.player_discovery import PlayerDiscovery

# Global flag for graceful shutdown
shutdown_event = Event()

class CollectorService:
    """Main collector service that runs per region"""
    
    def __init__(self, region: str, api_key: str):
        self.region = region
        self.api_client = RiotAPIClient(api_key)
        self.storage = JSONStorageHandler()
        self.queue_manager = QueueManager()
        self.match_scanner = MatchScanner(self.api_client)
        self.player_discovery = PlayerDiscovery()
        
        self.stats = {
            'matches_collected': 0,
            'api_calls': 0,
            'errors': 0
        }
    
    def run(self):
        """Main collection loop for this region"""
        print(f"🚀 Starting collector for {self.region}")
        
        while not shutdown_event.is_set():
            try:
                # Get next player to check
                player = self.queue_manager.get_next_player(self.region)
                if shutdown_event.is_set():
                    break

                if not player:
                    # No one due - get oldest checked player
                    player = self.queue_manager.get_oldest_checked_player(self.region)
                    
                    if not player:
                        print(f"⚠️  No players in queue for {self.region}, sleeping...")
                        time.sleep(10)
                        continue
                    
                    print(f"⏰ Queue empty for {self.region}, checking oldest player")
                
                # Find new matches
                new_matches = self.match_scanner.find_new_matches(player)
                if shutdown_event.is_set():
                    break

                print(f"🔍 {self.region} - {player.get('summoner_name', 'Unknown')}: {len(new_matches)} new matches")
                
                # Collect each new match
                for match_id in new_matches:
                    try:
                        # Fetch match data
                        match_data = self.api_client.get_match(match_id, self.region)
                        self.stats['api_calls'] += 1
                        if shutdown_event.is_set():
                            break
                        if not match_data:
                            print(f"❌ Failed to fetch match {match_id}")
                            continue
                        
                        # Fetch timeline
                        timeline_data = self.api_client.get_timeline(match_id, self.region)
                        self.stats['api_calls'] += 1
                        
                        # Save to disk
                        match_path, timeline_path = self.storage.save_match(
                            match_data, timeline_data, self.region
                        )
                        
                        # Discover new players FIRST
                        self.player_discovery.process_match_participants(match_data)

                        # Then save to database
                        insert_match(match_data, match_path, timeline_path)
                                                
                        self.stats['matches_collected'] += 1
                        print(f"✅ Collected {match_id}")
                        
                    except Exception as e:
                        print(f"❌ Error collecting {match_id}: {e}")
                        self.stats['errors'] += 1
                
                # Update player's last check
                last_match = new_matches[0] if new_matches else player.get('last_match_id')
                self.queue_manager.update_player_checked(
                    player['puuid'],
                    last_match,
                    player.get('tier', 'UNKNOWN')
                )
                
                # Boost priority if very active
                if self.match_scanner.is_very_active(len(new_matches)):
                    self.queue_manager.boost_player_priority(player['puuid'])
                    print(f"⚡ Boosted priority for active player")
                
            except Exception as e:
                print(f"❌ Collector error for {self.region}: {e}")
                self.stats['errors'] += 1
                time.sleep(5)
        
        print(f"🛑 Collector stopped for {self.region}")
        self.api_client.close()
    
    def get_stats(self):
        """Get collector statistics"""
        return {
            'region': self.region,
            **self.stats
        }

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n🛑 Shutdown signal received, stopping collectors...")
    shutdown_event.set()

def main():
    """Main entry point - starts collectors for all regions"""
    # Setup signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Validate settings
    try:
        settings.validate()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    
    # Initialize database pool
    db_pool.initialize()
    
    # Start collector thread for each region
    collectors = []
    threads = []
    
    for region in settings.REGIONS:
        collector = CollectorService(region, settings.RIOT_API_KEY_COLLECTION)
        collectors.append(collector)
        
        thread = Thread(target=collector.run, name=f"Collector-{region}")
        thread.start()
        threads.append(thread)
    
    print(f"\n✅ Started {len(collectors)} collectors")
    print("Press Ctrl+C to stop\n")
    
    # Keep main thread alive and print stats periodically
    try:
        while not shutdown_event.is_set():
            time.sleep(60)
            
            # Print stats
            print("\n📊 Collection Stats:")
            for collector in collectors:
                stats = collector.get_stats()
                print(f"  {stats['region']}: {stats['matches_collected']} matches, "
                      f"{stats['api_calls']} API calls, {stats['errors']} errors")
    
    except KeyboardInterrupt:
        pass
    
    # Wait for threads to finish
    print("\n⏳ Waiting for collectors to finish...")
    for thread in threads:
        thread.join(timeout=5)  # Shorter timeout
        if thread.is_alive():
            print(f"⚠️  Thread {thread.name} still running, forcing exit")
    
    # Close database pool
    db_pool.close()
    
    print("✅ Shutdown complete")

if __name__ == "__main__":
    main()