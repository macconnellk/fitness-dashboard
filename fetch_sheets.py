import os
import requests
from datetime import datetime

def fetch_lean_mass_data(use_cache=True):
    """Fetch lean mass data from Google Apps Script and format for Analyzer"""
    script_url = os.environ.get('GOOGLE_SCRIPT_URL')
    
    if not script_url:
        print("⚠️  No Google Script URL configured")
        return None
    
    try:
        response = requests.get(script_url, timeout=10)
        response.raise_for_status()
        raw_data = response.json()
        
        # BRIDGE: Map 'actual' from your Script to 'current' for your Analyzer
        formatted_data = {
            "current": {
                "date": raw_data['actual'].get('date'),
                "weight": raw_data['actual'].get('weight_lbs'),
                "bf_pct": raw_data['actual'].get('body_fat_pct'),
                "lean_mass": raw_data['actual'].get('fat_free_mass_lbs'),
                "ffmi": raw_data['actual'].get('ffmi')
            },
            "goals": raw_data.get('goals', {}),
            "long_term": raw_data.get('long_term_goals', {})
        }
        
        print(f"✅ Fetched and formatted lean mass data for analyzer")
        return formatted_data
        
    except Exception as e:
        print(f"❌ Error fetching/formatting Google Sheet: {e}")
        return None

if __name__ == '__main__':
    data = fetch_lean_mass_data()
    if data:
        import json
        print(json.dumps(data, indent=2, default=str))
