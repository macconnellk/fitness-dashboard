"""
Oura Manager - Smart Data Fetcher
Handles fallback chain: API (OAuth2) → Export (Scraper) → Cache
Provides unified interface for getting Oura data regardless of source.
"""
import os
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
        else:
            return f"❌ Oura data unavailable: {self.message}"

def get_oura_data(force_refresh: bool = False) -> Tuple[Optional[Dict], OuraDataStatus]:
    """
    Get Oura data using best available method.
    
    Tries in order:
    1. Oura API (using Refresh Token to get fresh Access Token)
    2. Automated export download (Playwright Scraper)
    3. Cached data (as last resort)
    """
    print("📊 Fetching Oura data...")
    
    # ===========================================================================
    # 1. TRY OURA API (OAuth2 Refresh Flow)
    # ===========================================================================
    if config.OURA_REFRESH_TOKEN:
        print("  → Attempting Oura API (OAuth2 Refresh)...")
        try:
            # Step A: Exchange Refresh Token for a fresh Access Token
            # Oura Access Tokens typically expire every 24 hours
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
                print("  ✅ Token refreshed successfully.")
                
                # Step B: Fetch data using the new token
                data = oura_api.fetch_oura_api_data(
                    access_token=access_token,
                    use_cache=not force_refresh
                )
                
                if data:
                    return data, OuraDataStatus(True, 'api', 0, "Fetched via OAuth2 API")
            
            elif token_response.status_code == 403:
                # 403 specifically indicates an expired Oura subscription
                print("  ⚠️ API Access Forbidden (Subscription likely expired).")
            else:
                print(f"  ⚠️ Token refresh failed: {token_response.status_code}")
                
        except Exception as e:
            print(f"  ⚠️ API flow failed: {e}")
    else:
        print("  ⚠️ No OURA_REFRESH_TOKEN configured, skipping API")

    # ===========================================================================
    # 2. TRY OURA EXPORT (Scraper Fallback)
    # ===========================================================================
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
            
            return data, OuraDataStatus(True, 'export', age_days, "Fetched via Playwright Scraper")
    
    except Exception as e:
        print(f"  ⚠️ Export fetch failed: {e}")

    # ===========================================================================
    # 3. TRY CACHED DATA (Last Resort)
    # ===========================================================================
    if not force_refresh:
        print("  → Checking cache as last resort...")
        for cache_key, label in [('oura_api_data', 'API'), ('oura_export_data', 'export')]:
            cached = cache.get(cache_key, max_age_days=config.MAX_CACHE_AGE_DAYS)
            if cached:
                data, age_days = cached
                return data, OuraDataStatus(True, f'cache ({label})', age_days, f"Using {age_days} day old cache")

    # ===========================================================================
    # 4. COMPLETE FAILURE
    # ===========================================================================
    status = OuraDataStatus(False, 'failed', -1, "All fetch methods failed.")
    print(f"  {status}")
    return None, status

# ... (Keep all your existing helper functions: get_latest_sleep_data, etc.) ...

if __name__ == '__main__':
    # Test the manager
    data, status = get_oura_data()
    print(f"\nFinal Status: {status}")
