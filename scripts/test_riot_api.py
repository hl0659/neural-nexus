import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.config.settings import settings
from services.collector.api.riot_client import RiotAPIClient

def main():
    print("🧪 Testing Riot API Endpoints\n")
    
    api_client = RiotAPIClient(settings.RIOT_API_KEY_COLLECTION)
    
    # Step 1: Get Challenger league
    print("=" * 60)
    print("Step 1: Getting NA Challenger League")
    print("=" * 60)
    
    league = api_client.get_challenger_league('na1')
    
    if not league or 'entries' not in league:
        print("❌ Failed to get Challenger league")
        return
    
    # Get first player
    first_player = league['entries'][0]
    print(f"\n✅ Top Challenger Player:")
    print(json.dumps(first_player, indent=2))
    
    puuid = first_player.get('puuid')
    if not puuid:
        print("\n❌ No PUUID in entry")
        return
    
    print(f"\n📋 PUUID: {puuid}")
    
    # Step 2: Test ACCOUNT-V1 with regional routing
    print("\n" + "=" * 60)
    print("Step 2: Testing ACCOUNT-V1 (regional routing)")
    print("=" * 60)
    
    # Manually construct account-v1 request
    import httpx
    account_url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-puuid/{puuid}"
    
    print(f"\nURL: {account_url}")
    
    try:
        response = httpx.get(account_url, headers={'X-Riot-Token': settings.RIOT_API_KEY_COLLECTION})
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            account_data = response.json()
            print(f"\n✅ ACCOUNT-V1 Response:")
            print(json.dumps(account_data, indent=2))
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    # Step 3: Test SUMMONER-V4 by PUUID
    print("\n" + "=" * 60)
    print("Step 3: Testing SUMMONER-V4 by PUUID (platform routing)")
    print("=" * 60)
    
    summoner_url = f"https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
    print(f"\nURL: {summoner_url}")
    
    try:
        response = httpx.get(summoner_url, headers={'X-Riot-Token': settings.RIOT_API_KEY_COLLECTION})
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            summoner_data = response.json()
            print(f"\n✅ SUMMONER-V4 Response:")
            print(json.dumps(summoner_data, indent=2))
            
            summoner_id = summoner_data.get('id')
            
            # Step 4: Get ranked info with summoner ID
            if summoner_id:
                print("\n" + "=" * 60)
                print("Step 4: Testing LEAGUE-V4 (get rank)")
                print("=" * 60)
                
                league_url = f"https://na1.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}"
                print(f"\nURL: {league_url}")
                
                response = httpx.get(league_url, headers={'X-Riot-Token': settings.RIOT_API_KEY_COLLECTION})
                print(f"Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    league_entries = response.json()
                    print(f"\n✅ LEAGUE-V4 Response:")
                    print(json.dumps(league_entries, indent=2))
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Request failed: {e}")
    # Step 4: Test SUMMONER-V4 by Riot ID
    print("\n" + "=" * 60)
    print("Step 4: Testing SUMMONER-V4 by Riot ID")
    print("=" * 60)

    import urllib.parse
    game_name = urllib.parse.quote("cant type")
    tag_line = "1998"

    summoner_by_riot_id_url = f"https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-riot-id/{game_name}/{tag_line}"
    print(f"\nURL: {summoner_by_riot_id_url}")

    try:
        response = httpx.get(summoner_by_riot_id_url, headers={'X-Riot-Token': settings.RIOT_API_KEY_COLLECTION})
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            summoner_data = response.json()
            print(f"\n✅ SUMMONER-V4 by Riot ID Response:")
            print(json.dumps(summoner_data, indent=2))
        else:
            print(f"❌ Error Response:")
            print(response.text)
    except Exception as e:
        print(f"❌ Request failed: {e}")

    api_client.close()
    
    print("\n" + "=" * 60)
    print("✅ API Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    main()