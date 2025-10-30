"""
Neural Nexus v3.0 - Check NEXUS Queue Composition
Shows regional breakdown and tier distribution of players needing resolution
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.database.connection import db_pool
from database.operations.player_ops import get_players_without_nexus_puuid


if __name__ == "__main__":
    print("="*60)
    print("NEXUS QUEUE ANALYSIS")
    print("="*60)
    
    db_pool.initialize()
    
    # Get all players needing resolution
    players = get_players_without_nexus_puuid(limit=1000)
    
    print(f"\nTotal players needing NEXUS PUUID: {len(players)}")
    
    if not players:
        print("✅ No players need resolution!")
        db_pool.close()
        exit(0)
    
    # Regional breakdown
    region_counts = {}
    for player in players:
        region_counts[player.region] = region_counts.get(player.region, 0) + 1
    
    print(f"\n{'='*60}")
    print("REGIONAL BREAKDOWN")
    print(f"{'='*60}")
    for region, count in sorted(region_counts.items()):
        print(f"  {region.upper()}: {count} players")
    
    # Tier breakdown
    tier_counts = {}
    for player in players:
        tier = player.tier or 'UNRANKED'
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
    
    print(f"\n{'='*60}")
    print("TIER BREAKDOWN")
    print(f"{'='*60}")
    
    tier_order = ['MASTER', 'DIAMOND', 'EMERALD', 'PLATINUM', 'GOLD', 'SILVER', 'BRONZE', 'IRON', 'UNRANKED']
    for tier in tier_order:
        if tier in tier_counts:
            print(f"  {tier}: {tier_counts[tier]} players")
    
    # Sample players from each region
    print(f"\n{'='*60}")
    print("SAMPLE PLAYERS BY REGION")
    print(f"{'='*60}")
    
    for region in sorted(region_counts.keys()):
        region_players = [p for p in players if p.region == region][:3]
        print(f"\n{region.upper()}:")
        for player in region_players:
            print(f"  - {player.game_name}#{player.tag_line} ({player.tier or 'UNRANKED'})")
    
    print(f"\n{'='*60}")
    print(f"Total API calls needed: ~{len(players)}")
    print(f"Estimated time: ~{len(players) * 0.5 / 60:.1f} minutes")
    print(f"{'='*60}\n")
    
    db_pool.close()