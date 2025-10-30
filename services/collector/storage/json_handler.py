import gzip
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple
from shared.config.settings import settings

class JSONStorageHandler:
    """Handles compressed JSON storage for matches and timelines"""
    
    def __init__(self):
        self.data_path = settings.DATA_PATH
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create directory structure if it doesn't exist"""
        for region in settings.REGIONS:
            Path(f"{self.data_path}/matches/{region}").mkdir(parents=True, exist_ok=True)
            Path(f"{self.data_path}/timelines/{region}").mkdir(parents=True, exist_ok=True)
    
    def _get_date_folder(self) -> str:
        """Get current year-month folder (e.g., '2025-10')"""
        return datetime.now().strftime('%Y-%m')
    
    def save_match(self, match_data: Dict, timeline_data: Optional[Dict], region: str) -> Tuple[str, Optional[str]]:
        """
        Save match and timeline data as compressed JSON.
        Returns: (match_path, timeline_path)
        """
        match_id = match_data['metadata']['matchId']
        date_folder = self._get_date_folder()
        
        # Save match data
        match_dir = f"{self.data_path}/matches/{region}/{date_folder}"
        Path(match_dir).mkdir(parents=True, exist_ok=True)
        
        match_path = f"{match_dir}/{match_id}.json.gz"
        self._write_compressed(match_path, match_data)
        
        # Save timeline data if valid
        timeline_path = None
        if timeline_data and self._validate_timeline(timeline_data):
            timeline_dir = f"{self.data_path}/timelines/{region}/{date_folder}"
            Path(timeline_dir).mkdir(parents=True, exist_ok=True)
            
            timeline_path = f"{timeline_dir}/{match_id}_timeline.json.gz"
            self._write_compressed(timeline_path, timeline_data)
        
        return match_path, timeline_path
    
    def _write_compressed(self, filepath: str, data: Dict):
        """Write JSON data as gzipped file with atomic write"""
        temp_path = f"{filepath}.tmp"
        
        try:
            # Write to temp file first
            with gzip.open(temp_path, 'wt', encoding='utf-8') as f:
                json.dump(data, f, separators=(',', ':'))  # Compact JSON
            
            # Atomic rename
            os.replace(temp_path, filepath)
            
        except Exception as e:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e
    
    def _validate_timeline(self, timeline_data: Dict) -> bool:
        """Validate timeline data is complete"""
        if not timeline_data:
            return False
        
        # Check for basic structure
        if 'info' not in timeline_data:
            return False
        
        if 'frames' not in timeline_data['info']:
            return False
        
        # Should have at least a few frames
        if len(timeline_data['info']['frames']) < 2:
            return False
        
        return True
    
    def load_match(self, match_path: str) -> Optional[Dict]:
        """Load match data from compressed file"""
        try:
            with gzip.open(match_path, 'rt', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Failed to load match from {match_path}: {e}")
            return None
    
    def load_timeline(self, timeline_path: str) -> Optional[Dict]:
        """Load timeline data from compressed file"""
        try:
            with gzip.open(timeline_path, 'rt', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Failed to load timeline from {timeline_path}: {e}")
            return None
    
    def get_storage_stats(self) -> Dict:
        """Get storage statistics"""
        stats = {
            'total_matches': 0,
            'total_timelines': 0,
            'total_size_mb': 0,
            'by_region': {}
        }
        
        for region in settings.REGIONS:
            match_dir = f"{self.data_path}/matches/{region}"
            timeline_dir = f"{self.data_path}/timelines/{region}"
            
            match_count = 0
            timeline_count = 0
            total_size = 0
            
            if os.path.exists(match_dir):
                for root, dirs, files in os.walk(match_dir):
                    match_count += len([f for f in files if f.endswith('.json.gz')])
                    total_size += sum(os.path.getsize(os.path.join(root, f)) for f in files)
            
            if os.path.exists(timeline_dir):
                for root, dirs, files in os.walk(timeline_dir):
                    timeline_count += len([f for f in files if f.endswith('.json.gz')])
                    total_size += sum(os.path.getsize(os.path.join(root, f)) for f in files)
            
            stats['by_region'][region] = {
                'matches': match_count,
                'timelines': timeline_count,
                'size_mb': round(total_size / 1024 / 1024, 2)
            }
            
            stats['total_matches'] += match_count
            stats['total_timelines'] += timeline_count
            stats['total_size_mb'] += total_size / 1024 / 1024
        
        stats['total_size_mb'] = round(stats['total_size_mb'], 2)
        return stats