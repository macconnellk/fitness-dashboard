"""
Oura Ring API Client
Fetches sleep, readiness, and activity data from Oura API v2.
"""
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import config
from cache_manager import cache


class OuraAPIClient:
    """Client for Oura Ring API v2."""
    
    def __init__(self, api_token: str = None):
        self.api_token = api_token or config.OURA_API_TOKEN
        self.base_url = config.OURA_API_BASE_URL
        self.headers = {
            'Authorization': f'Bearer {self.api_token}'
        }
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make authenticated request to Oura API."""
        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                print("❌ Oura API authentication failed (token invalid or expired)")
            else:
                print(f"❌ Oura API error: {e}")
            return None
        except Exception as e:
            print(f"❌ Oura API request failed: {e}")
            return None
    
    def get_sleep_data(self, start_date: str = None, end_date: str = None) -> Optional[List[Dict]]:
        """
        Get sleep data for date range.
        
        Args:
            start_date: Start date (YYYY-MM-DD), defaults to 7 days ago
            end_date: End date (YYYY-MM-DD), defaults to today
        
        Returns:
            List of sleep records or None if failed
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        params = {
            'start_date': start_date,
            'end_date': end_date
        }
        
        result = self._make_request('usercollection/sleep', params)
        if result:
            return result.get('data', [])
        return None
    
    def get_daily_sleep(self, start_date: str = None, end_date: str = None) -> Optional[List[Dict]]:
        """
        Get daily sleep summaries (includes scores if subscription active).
        
        Args:
            start_date: Start date (YYYY-MM-DD), defaults to 7 days ago
            end_date: End date (YYYY-MM-DD), defaults to today
        
        Returns:
            List of daily sleep records or None if failed
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        params = {
            'start_date': start_date,
            'end_date': end_date
        }
        
        result = self._make_request('usercollection/daily_sleep', params)
        if result:
            return result.get('data', [])
        return None
    
    def get_daily_readiness(self, start_date: str = None, end_date: str = None) -> Optional[List[Dict]]:
        """
        Get daily readiness data (includes scores if subscription active).
        
        Args:
            start_date: Start date (YYYY-MM-DD), defaults to 7 days ago
            end_date: End date (YYYY-MM-DD), defaults to today
        
        Returns:
            List of daily readiness records or None if failed
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        params = {
            'start_date': start_date,
            'end_date': end_date
        }
        
        result = self._make_request('usercollection/daily_readiness', params)
        if result:
            return result.get('data', [])
        return None
    
    def get_daily_activity(self, start_date: str = None, end_date: str = None) -> Optional[List[Dict]]:
        """
        Get daily activity data.
        
        Args:
            start_date: Start date (YYYY-MM-DD), defaults to 7 days ago
            end_date: End date (YYYY-MM-DD), defaults to today
        
        Returns:
            List of daily activity records or None if failed
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        params = {
            'start_date': start_date,
            'end_date': end_date
        }
        
        result = self._make_request('usercollection/daily_activity', params)
        if result:
            return result.get('data', [])
        return None
    
    def get_heart_rate(self, start_datetime: str = None, end_datetime: str = None) -> Optional[List[Dict]]:
        """
        Get heart rate data.
        
        Args:
            start_datetime: Start datetime (ISO format), defaults to 24 hours ago
            end_datetime: End datetime (ISO format), defaults to now
        
        Returns:
            List of heart rate records or None if failed
        """
        if not start_datetime:
            start_datetime = (datetime.now() - timedelta(days=1)).isoformat()
        if not end_datetime:
            end_datetime = datetime.now().isoformat()
        
        params = {
            'start_datetime': start_datetime,
            'end_datetime': end_datetime
        }
        
        result = self._make_request('usercollection/heartrate', params)
        if result:
            return result.get('data', [])
        return None
    
    def get_all_recent_data(self, days: int = 7) -> Optional[Dict]:
        """
        Get all relevant data for the last N days.
        
        Args:
            days: Number of days to fetch (default: 7)
        
        Returns:
            Dictionary with all data or None if failed
        """
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"📊 Fetching Oura data from {start_date} to {end_date}...")
        
        data = {
            'sleep': self.get_sleep_data(start_date, end_date),
            'daily_sleep': self.get_daily_sleep(start_date, end_date),
            'daily_readiness': self.get_daily_readiness(start_date, end_date),
            'daily_activity': self.get_daily_activity(start_date, end_date),
            'fetched_at': datetime.now().isoformat()
        }
        
        # Check if we got at least some data
        if any(v for v in data.values() if isinstance(v, list) and len(v) > 0):
            print(f"✓ Oura API data fetched successfully")
            # Cache the data
            cache.set('oura_api_data', data)
            return data
        else:
            print("⚠️  Oura API returned no data")
            return None


def fetch_oura_api_data(use_cache: bool = True, cache_max_age: int = 1) -> Optional[Dict]:
    """
    Fetch Oura data from API with caching.
    
    Args:
        use_cache: If True, try cache first
        cache_max_age: Maximum cache age in days
    
    Returns:
        Oura data dictionary or None if failed
    """
    # Try cache first
    if use_cache:
        cached = cache.get('oura_api_data', max_age_days=cache_max_age)
        if cached:
            data, age = cached
            print(f"✓ Using cached Oura API data (age: {age} days)")
            return data
    
    # Fetch fresh data
    if not config.OURA_API_TOKEN:
        print("⚠️  No Oura API token configured")
        return None
    
    client = OuraAPIClient()
    return client.get_all_recent_data(days=7)


if __name__ == '__main__':
    # Test Oura API client
    print("Testing Oura API Client...")
    print(f"Token configured: {bool(config.OURA_API_TOKEN)}")
    
    if config.OURA_API_TOKEN:
        data = fetch_oura_api_data(use_cache=False)
        
        if data:
            print("\n✓ Data retrieved:")
            print(f"  Sleep records: {len(data.get('sleep', []))}")
            print(f"  Daily sleep: {len(data.get('daily_sleep', []))}")
            print(f"  Daily readiness: {len(data.get('daily_readiness', []))}")
            print(f"  Daily activity: {len(data.get('daily_activity', []))}")
            
            # Show sample of most recent sleep data
            if data.get('daily_sleep'):
                latest = data['daily_sleep'][-1]
                print(f"\n  Latest sleep:")
                print(f"    Date: {latest.get('day')}")
                print(f"    Score: {latest.get('score')}")
                print(f"    Total sleep: {latest.get('contributors', {}).get('total_sleep', 'N/A')}")
        else:
            print("❌ Failed to fetch data")
    else:
        print("⚠️  Configure OURA_API_TOKEN in .env to test")
