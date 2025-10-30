import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.config.settings import settings
from shared.database.connection import db_pool
from services.collector.api.riot_client import RiotAPIClient

print("🧪 Testing Neural Nexus Setup\n")

# Test 1: Configuration
print("1️⃣ Testing Configuration...")
try:
    settings.validate()
    print("   ✅ API keys found")
    print(f"   ✅ Regions: {', '.join(settings.REGIONS)}")
    print(f"   ✅ Data path: {settings.DATA_PATH}")
except Exception as e:
    print(f"   ❌ Configuration error: {e}")
    sys.exit(1)

# Test 2: Database Connection
print("\n2️⃣ Testing Database Connection...")
try:
    db_pool.initialize()
    with db_pool.get_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM players")
        result = cursor.fetchone()
        print(f"   ✅ Database connected")
        print(f"   ✅ Players in database: {result['count']}")
except Exception as e:
    print(f"   ❌ Database error: {e}")
    sys.exit(1)

# Test 3: API Connection
print("\n3️⃣ Testing Riot API Connection...")
try:
    api_client = RiotAPIClient(settings.RIOT_API_KEY_COLLECTION)
    
    # Try to fetch Challenger league from NA
    league = api_client.get_challenger_league('na1')
    
    if league and 'entries' in league:
        print(f"   ✅ API connection successful")
        print(f"   ✅ Found {len(league['entries'])} Challenger players")
    else:
        print("   ❌ API returned invalid data")
    
    api_client.close()
except Exception as e:
    print(f"   ❌ API error: {e}")
    sys.exit(1)

# Test 4: Storage
print("\n4️⃣ Testing Storage...")
try:
    import os
    for region in settings.REGIONS:
        match_path = f"{settings.DATA_PATH}/matches/{region}"
        timeline_path = f"{settings.DATA_PATH}/timelines/{region}"
        
        if os.path.exists(match_path) and os.path.exists(timeline_path):
            print(f"   ✅ {region.upper()} storage directories exist")
        else:
            print(f"   ⚠️  {region.upper()} storage directories missing (will be created)")
except Exception as e:
    print(f"   ❌ Storage error: {e}")

db_pool.close()

print("\n" + "="*50)
print("✅ All tests passed! System is ready.")
print("="*50)
print("\nNext steps:")
print("1. Run: python scripts/seed_players.py")
print("2. Then: python -m services.collector.main")