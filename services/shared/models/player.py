"""
Neural Nexus v3.0 - Player Data Model
Data structures for player information
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Player:
    """Player data model"""
    
    # Primary Identifier
    region: str
    game_name: str
    tag_line: str
    
    # Key-specific PUUIDs
    apex_puuid: Optional[str] = None
    nexus_puuid: Optional[str] = None
    
    # Rank Data
    tier: Optional[str] = None
    rank: Optional[str] = None
    league_points: int = 0
    wins: int = 0
    losses: int = 0
    league_id: Optional[str] = None
    
    # Collection Tracking
    last_apex_check: Optional[datetime] = None
    last_nexus_check: Optional[datetime] = None
    apex_match_count: int = 0
    nexus_match_count: int = 0
    
    # Metadata
    discovered_by: Optional[str] = None  # 'apex' or 'nexus'
    is_seed_player: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __str__(self) -> str:
        return f"{self.game_name}#{self.tag_line} ({self.region.upper()}) - {self.tier or 'UNRANKED'}"
    
    def get_riot_id(self) -> str:
        """Get Riot ID in gameName#tagLine format"""
        return f"{self.game_name}#{self.tag_line}"
    
    def has_apex_puuid(self) -> bool:
        """Check if player has APEX PUUID"""
        return self.apex_puuid is not None
    
    def has_nexus_puuid(self) -> bool:
        """Check if player has NEXUS PUUID"""
        return self.nexus_puuid is not None
    
    def is_high_elo(self) -> bool:
        """Check if player is Challenger or Grandmaster"""
        return self.tier in ['CHALLENGER', 'GRANDMASTER']
    
    def get_winrate(self) -> float:
        """Calculate winrate"""
        total = self.wins + self.losses
        if total == 0:
            return 0.0
        return (self.wins / total) * 100


@dataclass
class PlayerStats:
    """Aggregated player statistics"""
    
    total_players: int = 0
    by_tier: dict = None
    by_region: dict = None
    with_apex_puuid: int = 0
    with_nexus_puuid: int = 0
    seed_players: int = 0
    
    def __post_init__(self):
        if self.by_tier is None:
            self.by_tier = {}
        if self.by_region is None:
            self.by_region = {}


if __name__ == "__main__":
    # Test player model
    print("Testing Player Model...")
    print("="*60)
    
    # Create test player
    player = Player(
        region='na1',
        game_name='TestPlayer',
        tag_line='NA1',
        apex_puuid='test-apex-puuid-123',
        tier='CHALLENGER',
        rank='I',
        league_points=1250,
        wins=150,
        losses=100,
        discovered_by='apex',
        is_seed_player=True
    )
    
    print(f"\nPlayer: {player}")
    print(f"Riot ID: {player.get_riot_id()}")
    print(f"Has APEX PUUID: {player.has_apex_puuid()}")
    print(f"Has NEXUS PUUID: {player.has_nexus_puuid()}")
    print(f"Is High Elo: {player.is_high_elo()}")
    print(f"Winrate: {player.get_winrate():.1f}%")
    
    print("\n✅ Player model tests complete!")