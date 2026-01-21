"""
Cache Manager for Fitness Dashboard
Handles caching of data from various sources with age tracking.
"""
import json
import pickle
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Optional, Tuple
import config


class CacheManager:
    """Manages caching of API data with age tracking."""
    
    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or config.CACHE_DIR
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_path(self, key: str, use_json: bool = True) -> Path:
        """Get the file path for a cache key."""
        ext = '.json' if use_json else '.pkl'
        return self.cache_dir / f"{key}{ext}"
    
    def set(self, key: str, data: Any, use_json: bool = True) -> bool:
        """
        Cache data with timestamp.
        
        Args:
            key: Cache key identifier
            data: Data to cache
            use_json: If True, use JSON (for simple data), else use pickle
        
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_path = self._get_cache_path(key, use_json)
            
            cache_obj = {
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            
            if use_json:
                with open(cache_path, 'w') as f:
                    json.dump(cache_obj, f, indent=2, default=str)
            else:
                with open(cache_path, 'wb') as f:
                    pickle.dump(cache_obj, f)
            
            return True
        except Exception as e:
            print(f"❌ Failed to cache {key}: {e}")
            return False
    
    def get(self, key: str, use_json: bool = True, 
            max_age_days: Optional[int] = None) -> Optional[Tuple[Any, int]]:
        """
        Get cached data with age information.
        
        Args:
            key: Cache key identifier
            use_json: If True, expect JSON cache
            max_age_days: Maximum age in days (None = no limit)
        
        Returns:
            Tuple of (data, age_in_days) if found and valid, None otherwise
        """
        try:
            cache_path = self._get_cache_path(key, use_json)
            
            if not cache_path.exists():
                return None
            
            # Load cache
            if use_json:
                with open(cache_path, 'r') as f:
                    cache_obj = json.load(f)
            else:
                with open(cache_path, 'rb') as f:
                    cache_obj = pickle.load(f)
            
            # Calculate age
            timestamp = datetime.fromisoformat(cache_obj['timestamp'])
            age_days = (datetime.now() - timestamp).days
            
            # Check if too old
            max_age = max_age_days or config.MAX_CACHE_AGE_DAYS
            if age_days > max_age:
                print(f"⚠️  Cache for {key} is {age_days} days old (max: {max_age})")
                return None
            
            return cache_obj['data'], age_days
            
        except Exception as e:
            print(f"❌ Failed to read cache {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete cached data."""
        try:
            for use_json in [True, False]:
                cache_path = self._get_cache_path(key, use_json)
                if cache_path.exists():
                    cache_path.unlink()
            return True
        except Exception as e:
            print(f"❌ Failed to delete cache {key}: {e}")
            return False
    
    def get_age_days(self, key: str, use_json: bool = True) -> Optional[int]:
        """Get age of cached data in days without loading the data."""
        try:
            cache_path = self._get_cache_path(key, use_json)
            
            if not cache_path.exists():
                return None
            
            if use_json:
                with open(cache_path, 'r') as f:
                    cache_obj = json.load(f)
            else:
                with open(cache_path, 'rb') as f:
                    cache_obj = pickle.load(f)
            
            timestamp = datetime.fromisoformat(cache_obj['timestamp'])
            return (datetime.now() - timestamp).days
            
        except:
            return None
    
    def clear_all(self) -> int:
        """Clear all cached data. Returns number of files deleted."""
        count = 0
        try:
            for cache_file in self.cache_dir.glob('*'):
                if cache_file.is_file():
                    cache_file.unlink()
                    count += 1
            return count
        except Exception as e:
            print(f"❌ Failed to clear cache: {e}")
            return count
    
    def clear_old(self, max_age_days: int = None) -> int:
        """Clear cached data older than max_age_days. Returns number deleted."""
        max_age = max_age_days or config.MAX_CACHE_AGE_DAYS
        count = 0
        
        try:
            for cache_file in self.cache_dir.glob('*'):
                if not cache_file.is_file():
                    continue
                
                # Check age
                age = (datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)).days
                
                if age > max_age:
                    cache_file.unlink()
                    count += 1
            
            if count > 0:
                print(f"🗑️  Cleared {count} old cache files (>{max_age} days)")
            
            return count
        except Exception as e:
            print(f"❌ Failed to clear old cache: {e}")
            return count


# Global cache instance
cache = CacheManager()


if __name__ == '__main__':
    # Test cache manager
    print("Testing Cache Manager...")
    
    # Test set/get
    test_data = {'test': 'data', 'timestamp': datetime.now()}
    cache.set('test_key', test_data)
    
    result = cache.get('test_key')
    if result:
        data, age = result
        print(f"✓ Retrieved cached data (age: {age} days)")
        print(f"  Data: {data}")
    else:
        print("❌ Failed to retrieve cache")
    
    # Test age
    age = cache.get_age_days('test_key')
    print(f"✓ Cache age: {age} days")
    
    # Test delete
    cache.delete('test_key')
    print("✓ Cache deleted")
    
    # Verify deleted
    result = cache.get('test_key')
    if result is None:
        print("✓ Cache successfully deleted")
    else:
        print("❌ Cache still exists")
