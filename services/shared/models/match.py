"""
Neural Nexus v3.0 - Match Data Model
Data structures for match information
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class MatchParticipant:
    """Individual participant in a match"""
    
    # Match Identity
    match_id: str
    
    # Player Identity
    region: str
    game_name: str
    tag_line: str
    
    # Match Performance
    participant_id: int
    champion_id: int
    champion_name: str
    team_id: int
    team_position: str
    won: bool
    
    # Stats
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    total_damage_dealt_to_champions: int = 0
    gold_earned: int = 0
    cs_score: int = 0
    vision_score: int = 0
    
    def get_kda(self) -> float:
        """Calculate KDA ratio"""
        if self.deaths == 0:
            return float(self.kills + self.assists)
        return (self.kills + self.assists) / self.deaths
    
    def __str__(self) -> str:
        return f"{self.champion_name} ({self.kills}/{self.deaths}/{self.assists})"


@dataclass
class Match:
    """Match metadata"""
    
    match_id: str
    region: str
    
    # Collection metadata
    collected_by: str  # 'apex' or 'nexus'
    collected_at: Optional[datetime] = None
    
    # Game info
    game_version: Optional[str] = None
    game_duration: Optional[int] = None
    game_creation: Optional[int] = None
    patch: Optional[str] = None
    game_mode: Optional[str] = None
    
    # File paths
    json_path: Optional[str] = None
    timeline_json_path: Optional[str] = None
    
    # Metadata
    created_at: Optional[datetime] = None
    
    def get_patch_version(self) -> str:
        """Extract major.minor patch (e.g., '13.24' from '13.24.1')"""
        if not self.game_version:
            return "Unknown"
        parts = self.game_version.split('.')
        if len(parts) >= 2:
            return f"{parts[0]}.{parts[1]}"
        return self.game_version
    
    def get_duration_minutes(self) -> float:
        """Get duration in minutes"""
        if not self.game_duration:
            return 0.0
        return self.game_duration / 60.0
    
    def __str__(self) -> str:
        return f"{self.match_id} ({self.region.upper()}) - Patch {self.patch or 'Unknown'}"


@dataclass
class MatchBan:
    """Champion ban in a match"""
    
    match_id: str
    team_id: int
    champion_id: int
    pick_turn: int


@dataclass
class MatchStats:
    """Aggregated match statistics"""
    
    total_matches: int = 0
    by_region: dict = None
    by_patch: dict = None
    by_service: dict = None
    apex_matches: int = 0
    nexus_matches: int = 0
    
    def __post_init__(self):
        if self.by_region is None:
            self.by_region = {}
        if self.by_patch is None:
            self.by_patch = {}
        if self.by_service is None:
            self.by_service = {'apex': 0, 'nexus': 0}


if __name__ == "__main__":
    # Test match models
    print("Testing Match Models...")
    print("="*60)
    
    # Create test match
    match = Match(
        match_id='NA1_4567890123',
        region='na1',
        collected_by='apex',
        game_version='13.24.1.1234',
        game_duration=1856,
        patch='13.24',
        game_mode='CLASSIC'
    )
    
    print(f"\nMatch: {match}")
    print(f"Patch Version: {match.get_patch_version()}")
    print(f"Duration: {match.get_duration_minutes():.1f} minutes")
    
    # Create test participant
    participant = MatchParticipant(
        region='na1',
        game_name='TestPlayer',
        tag_line='NA1',
        participant_id=1,
        champion_id=103,
        champion_name='Ahri',
        team_id=100,
        team_position='MIDDLE',
        won=True,
        kills=12,
        deaths=3,
        assists=8,
        total_damage_dealt_to_champions=25000,
        gold_earned=15000,
        cs_score=220,
        vision_score=45
    )
    
    print(f"\nParticipant: {participant}")
    print(f"KDA: {participant.get_kda():.2f}")
    
    # Create test ban
    ban = MatchBan(
        match_id='NA1_4567890123',
        team_id=100,
        champion_id=157,
        pick_turn=1
    )
    
    print(f"\nBan: Team {ban.team_id}, Champion {ban.champion_id}, Turn {ban.pick_turn}")
    
    print("\n✅ Match model tests complete!")