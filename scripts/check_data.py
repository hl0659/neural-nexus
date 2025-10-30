import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.config.settings import settings
from shared.database.connection import db_pool
from services.collector.storage.json_handler import JSONStorageHandler

def main():
    print("📊 Neural Nexus - Data Check")
    print("=" * 60)
    
    db_pool.initialize()
    storage = JSONStorageHandler()
    
    # Check database stats
    print("\n🗄️  Database Statistics:")
    with db_pool.get_cursor() as cursor:
        # Players
        cursor.execute("SELECT COUNT(*) as count FROM players")
        player_count = cursor.fetchone()['count']
        print(f"  Players: {player_count:,}")
        
        # Players by region and tier
        cursor.execute("""
            SELECT region, tier, COUNT(*) as count
            FROM players
            GROUP BY region, tier
            ORDER BY region, 
                CASE tier
                    WHEN 'CHALLENGER' THEN 1
                    WHEN 'GRANDMASTER' THEN 2
                    WHEN 'MASTER' THEN 3
                    ELSE 4
                END
        """)
        print("\n  Players by Region & Tier:")
        for row in cursor.fetchall():
            print(f"    {row['region'].upper():5} - {row['tier']:12} : {row['count']:4}")
        
        # Matches
        cursor.execute("SELECT COUNT(*) as count FROM matches")
        match_count = cursor.fetchone()['count']
        print(f"\n  Total Matches: {match_count:,}")
        
        # Matches by region
        cursor.execute("""
            SELECT region, COUNT(*) as count
            FROM matches
            GROUP BY region
            ORDER BY region
        """)
        print("\n  Matches by Region:")
        for row in cursor.fetchall():
            print(f"    {row['region'].upper():5} : {row['count']:3} matches")
        
        # Sample recent matches
        cursor.execute("""
            SELECT match_id, region, game_duration, 
                   TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as collected_at
            FROM matches
            ORDER BY created_at DESC
            LIMIT 5
        """)
        print("\n  Recent Matches:")
        for row in cursor.fetchall():
            mins = row['game_duration'] // 60
            secs = row['game_duration'] % 60
            print(f"    {row['match_id']:20} - {mins:2}m {secs:2}s - {row['collected_at']}")
    
    # Check file storage
    print("\n💾 File Storage Statistics:")
    stats = storage.get_storage_stats()
    print(f"  Total Matches: {stats['total_matches']:,}")
    print(f"  Total Timelines: {stats['total_timelines']:,}")
    print(f"  Total Size: {stats['total_size_mb']:.2f} MB")
    
    print("\n  Storage by Region:")
    for region, data in stats['by_region'].items():
        print(f"    {region.upper():5} : {data['matches']:3} matches, "
              f"{data['timelines']:3} timelines, {data['size_mb']:.2f} MB")
    
    # Test loading a match
    print("\n🔍 Sample Match Data:")
    with db_pool.get_cursor() as cursor:
        cursor.execute("""
            SELECT match_id, json_path, timeline_json_path
            FROM matches
            LIMIT 1
        """)
        sample = cursor.fetchone()
        
        if sample:
            print(f"  Match ID: {sample['match_id']}")
            print(f"  Match Path: {sample['json_path']}")
            
            # Try loading the match
            match_data = storage.load_match(sample['json_path'])
            if match_data:
                info = match_data['info']
                print(f"  ✅ Match loads successfully")
                print(f"  Game Duration: {info['gameDuration'] // 60}m {info['gameDuration'] % 60}s")
                print(f"  Game Mode: {info['gameMode']}")
                print(f"  Patch: {info['gameVersion']}")
                
                # Show some participants
                print(f"\n  Participants (first 5):")
                for p in info['participants'][:5]:
                    kda = f"{p['kills']}/{p['deaths']}/{p['assists']}"
                    print(f"    {p['championName']:15} - {kda:9} - {p.get('summonerName', 'Unknown')}")
            
            # Try loading timeline
            if sample['timeline_json_path']:
                timeline_data = storage.load_timeline(sample['timeline_json_path'])
                if timeline_data:
                    frames = len(timeline_data['info']['frames'])
                    print(f"\n  ✅ Timeline loads successfully")
                    print(f"  Timeline Frames: {frames}")
    
    db_pool.close()
    
    print("\n" + "=" * 60)
    print("✅ Data check complete!")

if __name__ == "__main__":
    main()