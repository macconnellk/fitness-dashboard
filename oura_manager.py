"""
Oura Manager - Smart Data Fetcher
Handles fallback chain: API (OAuth2) → Export (Scraper) → Cache
"""
import requests
from typing import Optional, Dict, Tuple
from datetime import datetime
import config
from cache_manager import cache
import oura_api
import oura_export

class OuraDataStatus:
    """Status of Oura data fetch."""
    def __init__(self, success: bool, source: str, age_days: int = 0, message: str = ""):
        self.success = success
        self.source = source  # 'api', 'export', 'cache', or 'failed'
        self.age_days = age_days
        self.message = message
    
    def __str__(self):
        if self.success:
            age_str = f" (age: {self.age_days} days)" if self.age_days > 0 else ""
            return f"✓ Oura data from {self.source}{age_str}"
        return f"❌ Oura data unavailable: {self.message}"

def get_oura_data(force_refresh: bool = False) -> Tuple[Optional[Dict], OuraDataStatus]:
    """
    Tries in order:
    1. Oura API (using Refresh Token to get a 24-hour Access Token)
    2. Automated export download (Playwright Scraper)
    3. Cached data (as last resort)
    """
    print("📊 Fetching Oura data...")
    
    # 1. TRY OURA API (OAuth2 Refresh Flow)
    if config.OURA_REFRESH_TOKEN:
        print("  → Attempting Oura API (OAuth2 Refresh)...")
        try:
            token_url = "https://api.ouraring.com/oauth/token"
            token_payload = {
                "grant_type": "refresh_token",
                "refresh_token": config.OURA_REFRESH_TOKEN,
                "client_id": config.OURA_CLIENT_ID,
                "client_secret": config.OURA_CLIENT_SECRET
            }
            
            token_response = requests.post(token_url, data=token_payload)
            
            if token_response.status_code == 200:
                access_token = token_response.json().get("access_token")
                # Step B: Fetch data using the new token
                data = oura_api.fetch_oura_api_data(
                    access_token=access_token,
                    use_cache=not force_refresh
                )
                if data:
                    return data, OuraDataStatus(True, 'api', 0, "Fetched via OAuth2 API")
            
            elif token_response.status_code == 403:
                # 403 means the user's Oura subscription has expired
                print("  ⚠️ API Access Forbidden: Oura subscription likely expired.")
            else:
                print(f"  ⚠️ Token refresh failed (Code: {token_response.status_code})")
                
        except Exception as e:
            print(f"  ⚠️ API flow failed: {e}")

    # 2. TRY OURA EXPORT (Scraper Fallback)
    print("  → Attempting Oura export scraper...")
    try:
        data = oura_export.fetch_oura_export_data(
            use_cache=not force_refresh,
            attempt_download=bool(config.OURA_EMAIL and config.OURA_PASSWORD)
        )
        if data:
            age_days = 0
            if 'fetched_at' in data:
                fetched_dt = datetime.fromisoformat(data['fetched_at'])
                age_days = (datetime.now() - fetched_dt).days
            return data, OuraDataStatus(True, 'export', age_days, "Fetched via Scraper")
    except Exception as e:
        print(f"  ⚠️ Export fetch failed: {e}")

    # 3. TRY CACHED DATA (Last Resort)
    if not force_refresh:
        print("  → Checking cache as last resort...")
        for key, label in [('oura_api_data', 'API'), ('oura_export_data', 'export')]:
            cached = cache.get(key, max_age_days=config.MAX_CACHE_AGE_DAYS)
            if cached:
                data, age_days = cached
                return data, OuraDataStatus(True, f'cache ({label})', age_days, f"Using {age_days}d old cache")

    return None, OuraDataStatus(False, 'failed', -1, "All fetch methods failed.")

# Helper functions for dashboard
def get_latest_sleep_data(data: Dict):
    return sorted(data.get('daily_sleep', []), key=lambda x: x.get('day', ''), reverse=True)[0] if data else None

def get_latest_readiness_data(data: Dict):
    return sorted(data.get('daily_readiness', []), key=lambda x: x.get('day', ''), reverse=True)[0] if data else None
