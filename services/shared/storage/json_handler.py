"""
Neural Nexus v3.0 - JSON Storage Handler
Saves match data as gzipped JSON files with proper directory structure
"""

import json
import gzip
from pathlib import Path
from typing import Dict, Any, Tuple
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from shared.config.settings import settings


class JSONHandler:
    """Handles saving and loading match data as gzipped JSON"""
    
    def __init__(self):
        self.data_path = settings.DATA_PATH
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        for service in ['apex', 'nexus']:
            for region in settings.REGIONS:
                # Match directories
                match_dir = self.data_path / 'matches' / service / region
                match_dir.mkdir(parents=True, exist_ok=True)
                
                # Timeline directories
                timeline_dir = self.data_path / 'timelines' / service / region
                timeline_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_match_path(self, match_id: str, region: str, service: str) -> Path:
        """
        Get file path for match data
        
        Args:
            match_id: Match ID (e.g., 'NA1_1234567890')
            region: Region code
            service: 'apex' or 'nexus'
        
        Returns:
            Path to match file
        """
        return self.data_path / 'matches' / service / region / f"{match_id}.json.gz"
    
    def _get_timeline_path(self, match_id: str, region: str, service: str) -> Path:
        """
        Get file path for timeline data
        
        Args:
            match_id: Match ID
            region: Region code
            service: 'apex' or 'nexus'
        
        Returns:
            Path to timeline file
        """
        return self.data_path / 'timelines' / service / region / f"{match_id}.json.gz"
    
    def save_match(self, match_data: Dict[str, Any], timeline_data: Dict[str, Any], 
                   region: str, service: str) -> Tuple[str, str]:
        """
        Save match and timeline data
        
        Args:
            match_data: Match data from API
            timeline_data: Timeline data from API
            region: Region code
            service: 'apex' or 'nexus'
        
        Returns:
            Tuple of (match_path, timeline_path)
        """
        match_id = match_data['metadata']['matchId']
        
        # Save match data
        match_path = self._get_match_path(match_id, region, service)
        with gzip.open(match_path, 'wt', encoding='utf-8') as f:
            json.dump(match_data, f)
        
        # Save timeline data
        timeline_path = self._get_timeline_path(match_id, region, service)
        with gzip.open(timeline_path, 'wt', encoding='utf-8') as f:
            json.dump(timeline_data, f)
        
        return str(match_path), str(timeline_path)
    
    def load_match(self, match_id: str, region: str, service: str) -> Dict[str, Any]:
        """
        Load match data
        
        Args:
            match_id: Match ID
            region: Region code
            service: 'apex' or 'nexus'
        
        Returns:
            Match data dict
        """
        match_path = self._get_match_path(match_id, region, service)
        
        if not match_path.exists():
            raise FileNotFoundError(f"Match file not found: {match_path}")
        
        with gzip.open(match_path, 'rt', encoding='utf-8') as f:
            return json.load(f)
    
    def load_timeline(self, match_id: str, region: str, service: str) -> Dict[str, Any]:
        """
        Load timeline data
        
        Args:
            match_id: Match ID
            region: Region code
            service: 'apex' or 'nexus'
        
        Returns:
            Timeline data dict
        """
        timeline_path = self._get_timeline_path(match_id, region, service)
        
        if not timeline_path.exists():
            raise FileNotFoundError(f"Timeline file not found: {timeline_path}")
        
        with gzip.open(timeline_path, 'rt', encoding='utf-8') as f:
            return json.load(f)
    
    def match_exists(self, match_id: str, region: str, service: str) -> bool:
        """Check if match file exists"""
        match_path = self._get_match_path(match_id, region, service)
        return match_path.exists()
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        stats = {
            'apex': {},
            'nexus': {},
            'total_matches': 0,
            'total_timelines': 0,
            'total_size_mb': 0
        }
        
        for service in ['apex', 'nexus']:
            service_stats = {}
            
            for region in settings.REGIONS:
                match_dir = self.data_path / 'matches' / service / region
                timeline_dir = self.data_path / 'timelines' / service / region
                
                match_count = len(list(match_dir.glob('*.json.gz'))) if match_dir.exists() else 0
                timeline_count = len(list(timeline_dir.glob('*.json.gz'))) if timeline_dir.exists() else 0
                
                # Calculate size
                match_size = sum(f.stat().st_size for f in match_dir.glob('*.json.gz')) if match_dir.exists() else 0
                timeline_size = sum(f.stat().st_size for f in timeline_dir.glob('*.json.gz')) if timeline_dir.exists() else 0
                
                service_stats[region] = {
                    'matches': match_count,
                    'timelines': timeline_count,
                    'size_mb': (match_size + timeline_size) / (1024 * 1024)
                }
                
                stats['total_matches'] += match_count
                stats['total_timelines'] += timeline_count
                stats['total_size_mb'] += (match_size + timeline_size) / (1024 * 1024)
            
            stats[service] = service_stats
        
        return stats


# Global JSON handler
json_handler = JSONHandler()


if __name__ == "__main__":
    # Test JSON handler
    print("Testing JSON Handler...")
    print("="*60)
    
    # Create test data
    test_match_data = {
        'metadata': {
            'matchId': 'NA1_TEST_9999999'
        },
        'info': {
            'gameCreation': 1234567890,
            'gameDuration': 1800,
            'participants': [
                {'puuid': 'test-puuid-1', 'championName': 'Ahri'},
                {'puuid': 'test-puuid-2', 'championName': 'Zed'}
            ]
        }
    }
    
    test_timeline_data = {
        'metadata': {
            'matchId': 'NA1_TEST_9999999'
        },
        'info': {
            'frames': []
        }
    }
    
    # Test 1: Save match
    print("\nTest 1: Saving test match...")
    try:
        match_path, timeline_path = json_handler.save_match(
            test_match_data, 
            test_timeline_data, 
            'na1', 
            'apex'
        )
        print(f"✅ Match saved to: {match_path}")
        print(f"✅ Timeline saved to: {timeline_path}")
    except Exception as e:
        print(f"❌ Failed to save: {e}")
    
    # Test 2: Check if exists
    print("\nTest 2: Checking if match exists...")
    exists = json_handler.match_exists('NA1_TEST_9999999', 'na1', 'apex')
    print(f"{'✅' if exists else '❌'} Match exists: {exists}")
    
    # Test 3: Load match
    print("\nTest 3: Loading match...")
    try:
        loaded_match = json_handler.load_match('NA1_TEST_9999999', 'na1', 'apex')
        print(f"✅ Match loaded")
        print(f"  Match ID: {loaded_match['metadata']['matchId']}")
        print(f"  Participants: {len(loaded_match['info']['participants'])}")
    except Exception as e:
        print(f"❌ Failed to load: {e}")
    
    # Test 4: Load timeline
    print("\nTest 4: Loading timeline...")
    try:
        loaded_timeline = json_handler.load_timeline('NA1_TEST_9999999', 'na1', 'apex')
        print(f"✅ Timeline loaded")
        print(f"  Match ID: {loaded_timeline['metadata']['matchId']}")
    except Exception as e:
        print(f"❌ Failed to load: {e}")
    
    # Test 5: Storage stats
    print("\nTest 5: Storage statistics...")
    stats = json_handler.get_storage_stats()
    print(f"  Total matches: {stats['total_matches']}")
    print(f"  Total timelines: {stats['total_timelines']}")
    print(f"  Total size: {stats['total_size_mb']:.2f} MB")
    
    # Cleanup test file
    test_match_path = json_handler._get_match_path('NA1_TEST_9999999', 'na1', 'apex')
    test_timeline_path = json_handler._get_timeline_path('NA1_TEST_9999999', 'na1', 'apex')
    
    if test_match_path.exists():
        test_match_path.unlink()
    if test_timeline_path.exists():
        test_timeline_path.unlink()
    
    print("\n✅ JSON handler tests complete!")