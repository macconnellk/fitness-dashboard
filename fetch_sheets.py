"""
Google Sheets Data Fetcher
Fetches lean mass tracking data from published Google Sheet.
"""
import requests
import csv
from io import StringIO
from datetime import datetime
from typing import Dict, List, Optional
import config
from cache_manager import cache


def fetch_sheet_as_csv(sheet_id: str) -> Optional[str]:
    """
    Fetch Google Sheet as CSV using public URL.
    
    Args:
        sheet_id: Google Sheet ID
    
    Returns:
        CSV content as string or None if failed
    """
    try:
        # Construct CSV export URL
        url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv'
        
        response = requests.get(url)
        response.raise_for_status()
        
        return response.text
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print("❌ Google Sheet not found or not published")
            print("   Make sure sheet is published: File → Share → Publish to web")
        else:
            print(f"❌ Failed to fetch Google Sheet: {e}")
        return None
    except Exception as e:
        print(f"❌ Failed to fetch Google Sheet: {e}")
        return None


def parse_lean_mass_data(csv_content: str) -> Optional[Dict]:
    """
    Parse lean mass tracking data from CSV.
    
    Args:
        csv_content: CSV content as string
    
    Returns:
        Parsed data dictionary or None if failed
    """
    try:
        # Parse CSV
        reader = csv.DictReader(StringIO(csv_content))
        rows = list(reader)
        
        if not rows:
            print("⚠️  No data found in Google Sheet")
            return None
        
        # Filter out rows with missing data (empty date or weight)
        valid_rows = []
        for row in rows:
            date_str = row.get('Date', '').strip()
            weight_str = row.get('Weight (lbs)', '').strip()
            
            # Skip empty rows and header-like rows
            if not date_str or not weight_str or date_str == 'Date':
                continue
            
            # Skip rows with #NUM! or other errors
            if '#NUM!' in weight_str or '#VALUE!' in weight_str:
                continue
            
            try:
                # Parse date to validate
                datetime.strptime(date_str, '%a %m/%d/%Y')
                # Parse weight to validate
                float(weight_str)
                valid_rows.append(row)
            except (ValueError, AttributeError):
                continue
        
        if not valid_rows:
            print("⚠️  No valid data rows found in Google Sheet")
            return None
        
        # Get most recent entry
        latest = valid_rows[-1]
        
        # Parse latest values
        current_weight = float(latest.get('Weight (lbs)', 0))
        current_bf_pct = float(latest.get('Body Fat %', 0))
        current_lean_mass = float(latest.get('Fat-Free Mass (lbs)', 0))
        current_ffmi = float(latest.get('Fat Free Mass Index (FFMI)', 0))
        current_percentile = latest.get('Male Percentile US 1988-1994', 'N/A')
        
        # Try to parse percentile
        try:
            current_percentile = int(current_percentile)
        except (ValueError, TypeError):
            current_percentile = None
        
        # Get last few entries for trend
        recent_entries = []
        for row in valid_rows[-8:]:  # Last 8 weeks
            try:
                entry = {
                    'date': row.get('Date', ''),
                    'weight': float(row.get('Weight (lbs)', 0)),
                    'bf_pct': float(row.get('Body Fat %', 0)),
                    'lean_mass': float(row.get('Fat-Free Mass (lbs)', 0)),
                    'ffmi': float(row.get('Fat Free Mass Index (FFMI)', 0))
                }
                recent_entries.append(entry)
            except (ValueError, KeyError):
                continue
        
        # Determine current phase from "Lean Mass Plan" section if available
        # This is more complex - would need to check another sheet or section
        # For now, we'll just note the date
        
        data = {
            'current': {
                'date': latest.get('Date'),
                'weight': current_weight,
                'bf_pct': current_bf_pct,
                'lean_mass': current_lean_mass,
                'ffmi': current_ffmi,
                'percentile': current_percentile
            },
            'recent_trend': recent_entries,
            'goals': {
                'target_weight': 175.0,  # From sheet header
                'target_bf_pct': 15.5,   # From sheet header
                'target_lean_mass': 175.0 * (1 - 0.155)  # Calculate
            },
            'fetched_at': datetime.now().isoformat()
        }
        
        return data
        
    except Exception as e:
        print(f"❌ Failed to parse Google Sheet data: {e}")
        return None


def fetch_lean_mass_data(use_cache: bool = True, cache_max_age: int = 1) -> Optional[Dict]:
    """
    Fetch lean mass data from Google Sheets with caching.
    
    Args:
        use_cache: If True, try cache first
        cache_max_age: Maximum cache age in days
    
    Returns:
        Lean mass data dictionary or None if failed
    """
    # Try cache first
    if use_cache:
        cached = cache.get('lean_mass_data', max_age_days=cache_max_age)
        if cached:
            data, age = cached
            print(f"✓ Using cached lean mass data (age: {age} days)")
            return data
    
    # Fetch fresh data
    if not config.GOOGLE_SHEET_ID:
        print("⚠️  Google Sheet ID not configured")
        return None
    
    print("📊 Fetching lean mass data from Google Sheets...")
    
    # Fetch CSV
    csv_content = fetch_sheet_as_csv(config.GOOGLE_SHEET_ID)
    if not csv_content:
        return None
    
    # Parse data
    data = parse_lean_mass_data(csv_content)
    
    if data:
        print(f"✓ Lean mass data fetched successfully")
        print(f"  Current: {data['current']['weight']} lbs @ {data['current']['bf_pct']}% BF")
        print(f"  Lean mass: {data['current']['lean_mass']} lbs (FFMI: {data['current']['ffmi']})")
        
        # Cache the data
        cache.set('lean_mass_data', data)
        
        return data
    
    return None


if __name__ == '__main__':
    # Test Google Sheets fetcher
    print("Testing Google Sheets Fetcher...")
    print(f"Sheet ID configured: {bool(config.GOOGLE_SHEET_ID)}")
    
    if config.GOOGLE_SHEET_ID:
        print(f"\nSheet ID: {config.GOOGLE_SHEET_ID}")
        
        data = fetch_lean_mass_data(use_cache=False)
        
        if data:
            print("\n✓ Data retrieved:")
            current = data['current']
            print(f"\n  Current stats (as of {current['date']}):")
            print(f"    Weight: {current['weight']} lbs")
            print(f"    Body Fat: {current['bf_pct']}%")
            print(f"    Lean Mass: {current['lean_mass']} lbs")
            print(f"    FFMI: {current['ffmi']}")
            if current['percentile']:
                print(f"    Percentile: {current['percentile']}")
            
            goals = data['goals']
            print(f"\n  Goals:")
            print(f"    Target Weight: {goals['target_weight']} lbs")
            print(f"    Target BF%: {goals['target_bf_pct']}%")
            print(f"    Target Lean Mass: {goals['target_lean_mass']:.1f} lbs")
            
            print(f"\n  Recent trend: {len(data['recent_trend'])} data points")
            
        else:
            print("❌ Failed to fetch data")
    else:
        print("\n⚠️  Configure GOOGLE_SHEET_ID in .env to test")
        print("\nSetup instructions:")
        print("1. Open your Google Sheet")
        print("2. File → Share → Publish to web")
        print("3. Choose 'Entire Document' and 'CSV'")
        print("4. Copy the sheet ID from URL:")
        print("   https://docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit")
        print("5. Add GOOGLE_SHEET_ID to .env")
