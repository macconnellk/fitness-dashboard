import os
import requests
from datetime import datetime

def fetch_lean_mass_data(use_cache=True):
    """Fetch lean mass data from Google Apps Script"""
    script_url = os.environ.get('GOOGLE_SCRIPT_URL')
    
    if not script_url:
        print("⚠️  No Google Script URL configured")
        return None
    
    try:
        response = requests.get(script_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ Fetched lean mass data:")
        if data.get('actual'):
            print(f"   Actual: {data['actual'].get('weight_lbs')} lbs, {data['actual'].get('body_fat_pct')}% BF")
        if data.get('goals'):
            print(f"   Goal Week {data['goals'].get('week')}: {data['goals'].get('lifts_per_week')} lifts/week")
        
        return data
        
    except Exception as e:
        print(f"❌ Error fetching Google Sheet: {e}")
        return None

if __name__ == '__main__':
    data = fetch_lean_mass_data()
    if data:
        import json
        print(json.dumps(data, indent=2, default=str))
