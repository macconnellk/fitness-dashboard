import requests
from cache_manager import cache

def fetch_oura_api_data(access_token: str, use_cache: bool = True):
    """Fetches V2 data using a Bearer Token."""
    
    if use_cache:
        cached = cache.get('oura_api_data', max_age_days=1)
        if cached: return cached[0]

    headers = {"Authorization": f"Bearer {access_token}"}
    base_url = "https://api.ouraring.com/v2/usercollection"
    
    # We fetch the most critical daily summaries
    endpoints = {
        'daily_sleep': f"{base_url}/daily_sleep",
        'daily_readiness': f"{base_url}/daily_readiness",
        'daily_activity': f"{base_url}/daily_activity"
    }
    
    combined_data = {}
    for key, url in endpoints.items():
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                combined_data[key] = response.json().get('data', [])
        except Exception as e:
            print(f"Error fetching {key}: {e}")

    if combined_data:
        cache.set('oura_api_data', combined_data)
        
    return combined_data
