"""
Neural Nexus v3.0 - Progress Tracker
Saves and resumes collection progress
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class ProgressTracker:
    """Tracks and persists collection progress"""
    
    def __init__(self, service: str, progress_dir: str = "F:/neural_nexus_data_v3/progress"):
        self.service = service
        self.progress_dir = Path(progress_dir)
        self.progress_dir.mkdir(parents=True, exist_ok=True)
        self.progress_file = self.progress_dir / f"{service}_progress.json"
        
        self.stats = {
            'service': service,
            'started_at': None,
            'last_update': None,
            'players_processed': 0,
            'matches_collected': 0,
            'api_calls_made': 0,
            'errors': 0,
            'regions': {
                'na1': {'players': 0, 'matches': 0},
                'euw1': {'players': 0, 'matches': 0},
                'kr': {'players': 0, 'matches': 0}
            }
        }
        
        # Try to load existing progress
        self.load()
    
    def load(self) -> bool:
        """Load progress from file"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r') as f:
                    loaded = json.load(f)
                    self.stats.update(loaded)
                print(f"✓ Loaded progress for {self.service}")
                return True
            except Exception as e:
                print(f"⚠️  Failed to load progress: {e}")
                return False
        return False
    
    def save(self):
        """Save progress to file"""
        try:
            self.stats['last_update'] = datetime.now().isoformat()
            
            with open(self.progress_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            print(f"⚠️  Failed to save progress: {e}")
    
    def update(self, region: str = None, players: int = 0, matches: int = 0, 
               api_calls: int = 0, errors: int = 0):
        """Update progress statistics"""
        if self.stats['started_at'] is None:
            self.stats['started_at'] = datetime.now().isoformat()
        
        self.stats['players_processed'] += players
        self.stats['matches_collected'] += matches
        self.stats['api_calls_made'] += api_calls
        self.stats['errors'] += errors
        
        if region and region in self.stats['regions']:
            self.stats['regions'][region]['players'] += players
            self.stats['regions'][region]['matches'] += matches
        
        # Auto-save every update
        self.save()
    
    def get_summary(self) -> Dict:
        """Get progress summary"""
        return {
            'service': self.stats['service'],
            'running_time': self._calculate_running_time(),
            'players_processed': self.stats['players_processed'],
            'matches_collected': self.stats['matches_collected'],
            'api_calls_made': self.stats['api_calls_made'],
            'errors': self.stats['errors'],
            'regions': self.stats['regions']
        }
    
    def _calculate_running_time(self) -> str:
        """Calculate running time"""
        if not self.stats['started_at']:
            return "Not started"
        
        try:
            started = datetime.fromisoformat(self.stats['started_at'])
            now = datetime.now()
            duration = now - started
            
            hours = duration.total_seconds() / 3600
            return f"{hours:.2f} hours"
        except:
            return "Unknown"
    
    def reset(self):
        """Reset progress"""
        self.stats = {
            'service': self.service,
            'started_at': None,
            'last_update': None,
            'players_processed': 0,
            'matches_collected': 0,
            'api_calls_made': 0,
            'errors': 0,
            'regions': {
                'na1': {'players': 0, 'matches': 0},
                'euw1': {'players': 0, 'matches': 0},
                'kr': {'players': 0, 'matches': 0}
            }
        }
        self.save()
    
    def print_summary(self):
        """Print progress summary"""
        summary = self.get_summary()
        
        print(f"\n{'='*60}")
        print(f"{summary['service'].upper()} PROGRESS SUMMARY")
        print(f"{'='*60}")
        print(f"  Running time: {summary['running_time']}")
        print(f"  Players processed: {summary['players_processed']}")
        print(f"  Matches collected: {summary['matches_collected']}")
        print(f"  API calls made: {summary['api_calls_made']}")
        print(f"  Errors: {summary['errors']}")
        print(f"\n  Regional breakdown:")
        for region, stats in summary['regions'].items():
            print(f"    {region.upper()}: {stats['players']} players, {stats['matches']} matches")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    # Test progress tracker
    print("Testing Progress Tracker...")
    print("="*60)
    
    tracker = ProgressTracker('test')
    
    # Simulate some progress
    print("\nSimulating progress...")
    tracker.update(region='na1', players=5, matches=100, api_calls=250)
    tracker.update(region='euw1', players=3, matches=60, api_calls=150)
    tracker.update(region='kr', players=2, matches=40, api_calls=100, errors=1)
    
    # Print summary
    tracker.print_summary()
    
    # Test reload
    print("\nTesting reload...")
    tracker2 = ProgressTracker('test')
    tracker2.print_summary()
    
    # Cleanup
    tracker.reset()
    
    print("\n✓ Progress tracker tests complete!")