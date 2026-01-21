"""
Strava API Client
Fetches activities and calculates weekly training progress.
"""
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import config
from cache_manager import cache


class StravaClient:
    """Client for Strava API v3."""
    
    def __init__(self, client_id: str = None, client_secret: str = None, refresh_token: str = None):
        self.client_id = client_id or config.STRAVA_CLIENT_ID
        self.client_secret = client_secret or config.STRAVA_CLIENT_SECRET
        self.refresh_token = refresh_token or config.STRAVA_REFRESH_TOKEN
        self.access_token = None
        self.token_expires_at = 0
    
    def _refresh_access_token(self) -> bool:
        """Refresh the access token using refresh token."""
        try:
            url = 'https://www.strava.com/oauth/token'
            payload = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': self.refresh_token,
                'grant_type': 'refresh_token'
            }
            
            response = requests.post(url, data=payload)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            self.token_expires_at = token_data['expires_at']
            
            # Update refresh token if provided
            if 'refresh_token' in token_data:
                self.refresh_token = token_data['refresh_token']
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to refresh Strava access token: {e}")
            return False
    
    def _ensure_token(self) -> bool:
        """Ensure we have a valid access token."""
        # Check if token needs refresh
        if not self.access_token or datetime.now().timestamp() >= self.token_expires_at:
            return self._refresh_access_token()
        return True
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make authenticated request to Strava API."""
        if not self._ensure_token():
            return None
        
        try:
            url = f'https://www.strava.com/api/v3/{endpoint}'
            headers = {'Authorization': f'Bearer {self.access_token}'}
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            print(f"❌ Strava API error: {e}")
            return None
        except Exception as e:
            print(f"❌ Strava API request failed: {e}")
            return None
    
    def get_activities(self, after: int = None, before: int = None, 
                      page: int = 1, per_page: int = 30) -> Optional[List[Dict]]:
        """
        Get athlete activities.
        
        Args:
            after: Unix timestamp to retrieve activities after
            before: Unix timestamp to retrieve activities before
            page: Page number
            per_page: Number of activities per page (max 200)
        
        Returns:
            List of activity dictionaries or None if failed
        """
        params = {
            'page': page,
            'per_page': per_page
        }
        
        if after:
            params['after'] = after
        if before:
            params['before'] = before
        
        return self._make_request('athlete/activities', params)
    
    def get_recent_activities(self, days: int = 7) -> Optional[List[Dict]]:
        """
        Get activities from the last N days.
        
        Args:
            days: Number of days to look back
        
        Returns:
            List of activities or None if failed
        """
        after = int((datetime.now() - timedelta(days=days)).timestamp())
        return self.get_activities(after=after, per_page=100)


def categorize_activity(activity: Dict) -> str:
    """
    Categorize activity as 'run', 'lift', or 'other'.
    
    Args:
        activity: Strava activity dictionary
    
    Returns:
        Category string
    """
    sport_type = activity.get('sport_type', '').lower()
    activity_type = activity.get('type', '').lower()
    name = activity.get('name', '').lower()
    
    # Running activities
    if any(x in sport_type or x in activity_type for x in ['run', 'jog', 'trail']):
        return 'run'
    
    # Lifting/strength activities
    if any(x in sport_type or x in activity_type or x in name for x in 
           ['weight', 'strength', 'lift', 'gym', 'training']):
        return 'lift'
    
    return 'other'


def calculate_weekly_progress() -> Dict:
    """
    Calculate progress toward weekly training targets.
    
    Returns:
        Dictionary with training progress
    """
    # Get activities from start of this week
    today = datetime.now()
    days_since_sunday = (today.weekday() + 1) % 7  # Sunday = 0
    week_start = today - timedelta(days=days_since_sunday)
    week_start_unix = int(week_start.replace(hour=0, minute=0, second=0).timestamp())
    
    print(f"📊 Calculating weekly progress (week started: {week_start.strftime('%Y-%m-%d')})")
    
    # Fetch activities
    client = StravaClient()
    activities = client.get_activities(after=week_start_unix, per_page=100)
    
    if not activities:
        print("⚠️  No Strava activities found this week")
        return {
            'runs': 0,
            'lifts': 0,
            'run_minutes': 0,
            'run_target': config.WEEKLY_RUN_TARGET,
            'lift_target': config.WEEKLY_LIFT_TARGET,
            'lift_bonus_target': config.WEEKLY_LIFT_BONUS,
            'run_minutes_target': config.WEEKLY_RUN_MINUTES_TARGET,
            'activities': []
        }
    
    # Categorize and sum
    runs = []
    lifts = []
    total_run_minutes = 0
    
    for activity in activities:
        category = categorize_activity(activity)
        
        if category == 'run':
            runs.append(activity)
            # Convert moving_time (seconds) to minutes
            total_run_minutes += activity.get('moving_time', 0) / 60
        elif category == 'lift':
            lifts.append(activity)
    
    progress = {
        'runs': len(runs),
        'lifts': len(lifts),
        'run_minutes': round(total_run_minutes),
        'run_target': config.WEEKLY_RUN_TARGET,
        'lift_target': config.WEEKLY_LIFT_TARGET,
        'lift_bonus_target': config.WEEKLY_LIFT_BONUS,
        'run_minutes_target': config.WEEKLY_RUN_MINUTES_TARGET,
        'activities': activities,
        'week_start': week_start.strftime('%Y-%m-%d'),
        'fetched_at': datetime.now().isoformat()
    }
    
    print(f"✓ Weekly progress:")
    print(f"  Runs: {len(runs)}/{config.WEEKLY_RUN_TARGET} ({round(total_run_minutes)}/{config.WEEKLY_RUN_MINUTES_TARGET} min)")
    print(f"  Lifts: {len(lifts)}/{config.WEEKLY_LIFT_TARGET}")
    
    # Cache the progress
    cache.set('strava_weekly_progress', progress)
    
    return progress


def fetch_strava_data(use_cache: bool = True, cache_max_age: int = 1) -> Optional[Dict]:
    """
    Fetch Strava data with caching.
    
    Args:
        use_cache: If True, try cache first
        cache_max_age: Maximum cache age in days
    
    Returns:
        Strava progress data or None if failed
    """
    # Try cache first
    if use_cache:
        cached = cache.get('strava_weekly_progress', max_age_days=cache_max_age)
        if cached:
            data, age = cached
            # Only use cache if it's from this week
            week_start = data.get('week_start')
            today = datetime.now()
            days_since_sunday = (today.weekday() + 1) % 7
            current_week_start = (today - timedelta(days=days_since_sunday)).strftime('%Y-%m-%d')
            
            if week_start == current_week_start:
                print(f"✓ Using cached Strava data (age: {age} days)")
                return data
            else:
                print(f"⚠️  Cached data is from previous week, fetching fresh data")
    
    # Fetch fresh data
    if not all([config.STRAVA_CLIENT_ID, config.STRAVA_CLIENT_SECRET, config.STRAVA_REFRESH_TOKEN]):
        print("⚠️  Strava API not configured")
        return None
    
    try:
        return calculate_weekly_progress()
    except Exception as e:
        print(f"❌ Failed to fetch Strava data: {e}")
        return None


if __name__ == '__main__':
    # Test Strava client
    print("Testing Strava API Client...")
    print(f"Client ID configured: {bool(config.STRAVA_CLIENT_ID)}")
    print(f"Client Secret configured: {bool(config.STRAVA_CLIENT_SECRET)}")
    print(f"Refresh Token configured: {bool(config.STRAVA_REFRESH_TOKEN)}")
    
    if all([config.STRAVA_CLIENT_ID, config.STRAVA_CLIENT_SECRET, config.STRAVA_REFRESH_TOKEN]):
        print("\nFetching weekly progress...")
        progress = fetch_strava_data(use_cache=False)
        
        if progress:
            print("\n✓ Progress retrieved:")
            print(f"  Week starting: {progress['week_start']}")
            print(f"  Runs: {progress['runs']}/{progress['run_target']} ({progress['run_minutes']}/{progress['run_minutes_target']} min)")
            print(f"  Lifts: {progress['lifts']}/{progress['lift_target']}")
            
            # Show recent activities
            if progress['activities']:
                print(f"\n  Recent activities:")
                for act in progress['activities'][:5]:
                    print(f"    • {act['name']} ({categorize_activity(act)}) - {act['start_date'][:10]}")
        else:
            print("❌ Failed to fetch progress")
    else:
        print("\n⚠️  Configure Strava API credentials in .env to test")
        print("\nSetup instructions:")
        print("1. Go to: https://www.strava.com/settings/api")
        print("2. Create an application")
        print("3. Get Client ID and Client Secret")
        print("4. Use OAuth flow to get Refresh Token")
