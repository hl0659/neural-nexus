import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.config.settings import settings
from shared.database.connection import db_pool
from services.collector.api.riot_client import RiotAPIClient

def seed_region(region: str, api_key: str):
    """Seed players from a region's ranked ladders"""
    
    api_client = RiotAPIClient(api_key)
    
    # Only seed Challenger and Grandmaster
    tiers_to_seed = [
        ('CHALLENGER', 'get_challenger_league'),
        ('GRANDMASTER', 'get_grandmaster_league'),
    ]
    
    total_added = 0
    
    for tier_name, api_method in tiers_to_seed:
        print(f"\n🔍 Fetching {tier_name} players from {region}...")
        
        # Get league data
        method = getattr(api_client, api_method)
        league_data = method(region)
        
        if not league_data or 'entries' not in league_data:
            print(f"❌ Failed to fetch {tier_name} league")
            continue
        
        entries = league_data['entries']
        print(f"📋 Found {len(entries)} {tier_name} players")
        
        # Process each entry
        added = 0
        for i, entry in enumerate(entries, 1):
            try:
                # PUUID is directly in the entry now!
                puuid = entry.get('puuid')
                if not puuid:
                    print(f"  ⚠️  Entry missing puuid")
                    continue
                
                # Calculate next check time
                recheck_days = {
                    'CHALLENGER': 2,
                    'GRANDMASTER': 3,
                }
                next_check = datetime.now() + timedelta(days=recheck_days[tier_name])
                
                # Insert player (we'll enrich summoner details later)
                with db_pool.get_cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO players (
                            puuid, tier, rank, league_points,
                            wins, losses, region, next_check_after
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (puuid) DO NOTHING
                        RETURNING puuid
                    """, (
                        puuid,
                        tier_name,
                        entry.get('rank', 'I'),
                        entry.get('leaguePoints', 0),
                        entry.get('wins', 0),
                        entry.get('losses', 0),  # Note: API has 'lossses' typo
                        region,
                        next_check
                    ))
                    
                    result = cursor.fetchone()
                    if result:
                        added += 1
                
                if i % 50 == 0:
                    print(f"  Progress: {i}/{len(entries)} ({added} new)")
                
            except Exception as e:
                print(f"  ⚠️  Error processing entry {i}: {e}")
                continue
        
        print(f"✅ Added {added} new {tier_name} players")
        total_added += added
    
    api_client.close()
    return total_added

def main():
    """Main seeding function"""
    print("🌱 Neural Nexus - Player Seeding")
    print("=" * 50)
    
    # Validate API key
    if not settings.RIOT_API_KEY_COLLECTION:
        print("❌ Error: RIOT_API_KEY_COLLECTION not set in .env file")
        sys.exit(1)
    
    # Initialize database
    db_pool.initialize()
    
    # Seed each region
    total_players = 0
    for region in settings.REGIONS:
        print(f"\n{'=' * 50}")
        print(f"Seeding region: {region.upper()}")
        print(f"{'=' * 50}")
        
        try:
            count = seed_region(region, settings.RIOT_API_KEY_COLLECTION)
            total_players += count
        except Exception as e:
            print(f"❌ Error seeding {region}: {e}")
    
    # Close database
    db_pool.close()
    
    print(f"\n{'=' * 50}")
    print(f"✅ Seeding complete!")
    print(f"Total players added: {total_players}")
    print(f"\nRun 'python -m services.collector.main' to start collection")

if __name__ == "__main__":
    main()