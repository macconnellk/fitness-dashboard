"""
Oura Manager - Smart Data Fetcher
Handles fallback chain: API → Export → Cache
Provides unified interface for getting Oura data regardless of source.
"""
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
    1. Oura API (if token configured and valid)
    2. Automated/manual export download
    3. Cached data (if recent enough)
    4. Fail gracefully
    
    Args:
        force_refresh: If True, skip cache and fetch fresh data
    
    Returns:
        Tuple of (data_dict, status_object)
    """
    print("📊 Fetching Oura data...")
    
    # ===========================================================================
    # 1. TRY OURA API (while subscription active)
    # ===========================================================================
    if config.OURA_API_TOKEN:
        print("  → Attempting Oura API...")
        try:
            data = oura_api.fetch_oura_api_data(
                use_cache=not force_refresh,
                cache_max_age=1
            )
            
            if data:
                status = OuraDataStatus(
                    success=True,
                    source='api',
                    age_days=0,
                    message="Fetched from Oura API"
                )
                return data, status
            else:
                print("  ⚠️  API fetch returned no data")
        
        except Exception as e:
            print(f"  ⚠️  API fetch failed: {e}")
    else:
        print("  ⚠️  No API token configured, skipping API")
    
    # ===========================================================================
    # 2. TRY OURA EXPORT (after API subscription ends)
    # ===========================================================================
    print("  → Attempting Oura export...")
    try:
        data = oura_export.fetch_oura_export_data(
            use_cache=not force_refresh,
            attempt_download=bool(config.OURA_EMAIL and config.OURA_PASSWORD)
        )
        
        if data:
            # Check how old the export is
            age_days = 0
            if 'fetched_at' in data:
                fetched_dt = datetime.fromisoformat(data['fetched_at'])
                age_days = (datetime.now() - fetched_dt).days
            
            status = OuraDataStatus(
                success=True,
                source='export',
                age_days=age_days,
                message="Fetched from Oura export"
            )
            return data, status
    
    except Exception as e:
        print(f"  ⚠️  Export fetch failed: {e}")
    
    # ===========================================================================
    # 3. TRY CACHED DATA (last resort)
    # ===========================================================================
    if not force_refresh:
        print("  → Checking cache as last resort...")
        
        # Try API cache first
        cached_api = cache.get('oura_api_data', max_age_days=config.MAX_CACHE_AGE_DAYS)
        if cached_api:
            data, age_days = cached_api
            status = OuraDataStatus(
                success=True,
                source='cache (API)',
                age_days=age_days,
                message=f"Using {age_days} day old cached API data"
            )
            print(f"  ⚠️  {status.message}")
            return data, status
        
        # Try export cache
        cached_export = cache.get('oura_export_data', max_age_days=config.MAX_CACHE_AGE_DAYS)
        if cached_export:
            data, age_days = cached_export
            status = OuraDataStatus(
                success=True,
                source='cache (export)',
                age_days=age_days,
                message=f"Using {age_days} day old cached export data"
            )
            print(f"  ⚠️  {status.message}")
            return data, status
    
    # ===========================================================================
    # 4. COMPLETE FAILURE
    # ===========================================================================
    status = OuraDataStatus(
        success=False,
        source='failed',
        age_days=-1,
        message="No Oura data available. Check API token or download export manually."
    )
    print(f"  {status}")
    
    return None, status


def get_latest_sleep_data(data: Dict) -> Optional[Dict]:
    """Extract latest sleep data from Oura data."""
    if not data:
        return None
    
    # Try daily_sleep first (has scores)
    daily_sleep = data.get('daily_sleep', [])
    if daily_sleep:
        # Sort by date and get most recent
        sorted_sleep = sorted(daily_sleep, key=lambda x: x.get('day', ''), reverse=True)
        return sorted_sleep[0] if sorted_sleep else None
    
    # Fall back to sleep data
    sleep = data.get('sleep', [])
    if sleep:
        sorted_sleep = sorted(sleep, key=lambda x: x.get('day', ''), reverse=True)
        return sorted_sleep[0] if sorted_sleep else None
    
    return None


def get_latest_readiness_data(data: Dict) -> Optional[Dict]:
    """Extract latest readiness data from Oura data."""
    if not data:
        return None
    
    readiness = data.get('daily_readiness', [])
    if readiness:
        # Sort by date and get most recent
        sorted_readiness = sorted(readiness, key=lambda x: x.get('day', ''), reverse=True)
        return sorted_readiness[0] if sorted_readiness else None
    
    return None


def get_recent_sleep_trend(data: Dict, days: int = 7) -> Optional[list]:
    """Get sleep data for last N days."""
    if not data:
        return None
    
    daily_sleep = data.get('daily_sleep', []) or data.get('sleep', [])
    if not daily_sleep:
        return None
    
    # Sort by date (most recent first) and take N days
    sorted_sleep = sorted(daily_sleep, key=lambda x: x.get('day', ''), reverse=True)
    return sorted_sleep[:days]


def get_recent_readiness_trend(data: Dict, days: int = 7) -> Optional[list]:
    """Get readiness data for last N days."""
    if not data:
        return None
    
    readiness = data.get('daily_readiness', [])
    if not readiness:
        return None
    
    # Sort by date (most recent first) and take N days
    sorted_readiness = sorted(readiness, key=lambda x: x.get('day', ''), reverse=True)
    return sorted_readiness[:days]


if __name__ == '__main__':
    # Test Oura Manager
    print("Testing Oura Manager...")
    print("=" * 60)
    
    # Fetch data
    data, status = get_oura_data()
    
    print("\nStatus:", status)
    
    if data:
        print("\n✓ Data available:")
        print(f"  Source: {status.source}")
        print(f"  Age: {status.age_days} days")
        
        # Test helper functions
        latest_sleep = get_latest_sleep_data(data)
        if latest_sleep:
            print(f"\n  Latest sleep:")
            print(f"    Date: {latest_sleep.get('day')}")
            print(f"    Score: {latest_sleep.get('score', 'N/A')}")
        
        latest_readiness = get_latest_readiness_data(data)
        if latest_readiness:
            print(f"\n  Latest readiness:")
            print(f"    Date: {latest_readiness.get('day')}")
            print(f"    Score: {latest_readiness.get('score', 'N/A')}")
        
        recent_sleep = get_recent_sleep_trend(data, days=7)
        if recent_sleep:
            print(f"\n  Sleep trend (7 days): {len(recent_sleep)} records")
    
    else:
        print("\n❌ No data available")
        print("\nNext steps:")
        print("1. Configure OURA_API_TOKEN in .env (for API access)")
        print("2. Or download export manually from Oura website")
        print("3. Or run automated export with OURA_EMAIL/OURA_PASSWORD")
