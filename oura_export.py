"""
Oura Data Export Downloader
Automated downloading of Oura data export for use after API subscription ends.
Uses browser automation (Playwright) to download export file.
"""
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict
import config
from cache_manager import cache


def download_oura_export_playwright() -> Optional[Path]:
    """
    Download Oura export using Playwright browser automation.
    
    Returns:
        Path to downloaded export file or None if failed
    """
    try:
        from playwright.sync_api import sync_playwright
        
        print("🌐 Launching browser to download Oura export...")
        
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            # Navigate to Oura login
            print("  → Navigating to Oura login...")
            page.goto('https://cloud.ouraring.com/user/sign-in')
            
            # Fill in credentials
            print("  → Entering credentials...")
            page.fill('input[type="email"]', config.OURA_EMAIL)
            page.fill('input[type="password"]', config.OURA_PASSWORD)
            
            # Click sign in
            page.click('button[type="submit"]')
            
            # Wait for navigation
            page.wait_for_load_state('networkidle')
            time.sleep(2)
            
            # Navigate to export page
            print("  → Navigating to export page...")
            page.goto('https://cloud.ouraring.com/user/settings/personal-info')
            time.sleep(2)
            
            # Set up download handler
            download_path = config.CACHE_DIR / f'oura_export_{datetime.now().strftime("%Y%m%d")}.json'
            
            # Click export button (this varies by Oura's UI)
            # Note: This selector may need updating if Oura changes their UI
            with page.expect_download() as download_info:
                page.click('text=Export Data')  # May need to update this selector
            
            download = download_info.value
            download.save_as(download_path)
            
            print(f"✓ Export downloaded: {download_path}")
            
            browser.close()
            return download_path
            
    except ImportError:
        print("❌ Playwright not installed. Run: playwright install chromium")
        return None
    except Exception as e:
        print(f"❌ Failed to download Oura export: {e}")
        print(f"   This is expected if you don't have credentials configured")
        return None


def download_oura_export_manual() -> Optional[Path]:
    """
    Look for manually downloaded Oura export file.
    
    Returns:
        Path to export file or None if not found
    """
    # Check for export files in cache directory
    export_files = list(config.CACHE_DIR.glob('oura_export*.json'))
    
    if not export_files:
        print("⚠️  No Oura export files found in cache directory")
        print("   Please download export manually from: https://cloud.ouraring.com/user/settings/personal-info")
        print(f"   Save as: {config.CACHE_DIR}/oura_export_<date>.json")
        return None
    
    # Get most recent export
    latest_export = max(export_files, key=lambda p: p.stat().st_mtime)
    age_days = (datetime.now().timestamp() - latest_export.stat().st_mtime) / 86400
    
    print(f"✓ Found Oura export: {latest_export.name} (age: {age_days:.1f} days)")
    
    if age_days > config.MAX_CACHE_AGE_DAYS:
        print(f"⚠️  Export is older than {config.MAX_CACHE_AGE_DAYS} days")
    
    return latest_export


def parse_oura_export(export_path: Path) -> Optional[Dict]:
    """
    Parse Oura export JSON file.
    
    Args:
        export_path: Path to export JSON file
    
    Returns:
        Parsed data dictionary or None if failed
    """
    try:
        with open(export_path, 'r') as f:
            raw_data = json.load(f)
        
        print(f"✓ Parsed Oura export file")
        
        # Transform export format to match API format
        # Oura export structure varies, so we need to handle different formats
        data = {
            'sleep': raw_data.get('sleep', []),
            'daily_sleep': raw_data.get('sleep', []),  # Export doesn't separate these
            'daily_readiness': raw_data.get('readiness', []),
            'daily_activity': raw_data.get('activity', []),
            'fetched_at': datetime.now().isoformat(),
            'source': 'export',
            'export_file': str(export_path)
        }
        
        # Cache the parsed data
        cache.set('oura_export_data', data)
        
        return data
        
    except Exception as e:
        print(f"❌ Failed to parse Oura export: {e}")
        return None


def fetch_oura_export_data(use_cache: bool = True, 
                          attempt_download: bool = True) -> Optional[Dict]:
    """
    Fetch Oura data from export with caching.
    
    Args:
        use_cache: If True, try cached parsed data first
        attempt_download: If True, attempt automated download
    
    Returns:
        Oura data dictionary or None if failed
    """
    # Try cache first
    if use_cache:
        cached = cache.get('oura_export_data', max_age_days=config.MAX_CACHE_AGE_DAYS)
        if cached:
            data, age = cached
            print(f"✓ Using cached Oura export data (age: {age} days)")
            return data
    
    # Try to get export file
    export_path = None
    
    # Option 1: Automated download (if credentials configured)
    if attempt_download and config.OURA_EMAIL and config.OURA_PASSWORD:
        export_path = download_oura_export_playwright()
    
    # Option 2: Look for manual download
    if not export_path:
        export_path = download_oura_export_manual()
    
    # Parse export file if found
    if export_path:
        return parse_oura_export(export_path)
    
    return None


if __name__ == '__main__':
    # Test Oura export downloader
    print("Testing Oura Export Downloader...")
    print(f"Email configured: {bool(config.OURA_EMAIL)}")
    print(f"Password configured: {bool(config.OURA_PASSWORD)}")
    
    # Try manual download first (safer for testing)
    print("\n1. Checking for manual export...")
    export_path = download_oura_export_manual()
    
    if export_path:
        print("\n2. Parsing export file...")
        data = parse_oura_export(export_path)
        
        if data:
            print("\n✓ Data parsed:")
            print(f"  Sleep records: {len(data.get('sleep', []))}")
            print(f"  Readiness records: {len(data.get('daily_readiness', []))}")
            print(f"  Activity records: {len(data.get('daily_activity', []))}")
    else:
        print("\n⚠️  No export file found")
        print("\nTo test:")
        print("1. Go to: https://cloud.ouraring.com/user/settings/personal-info")
        print("2. Click 'Export Data'")
        print(f"3. Save to: {config.CACHE_DIR}/oura_export_20260121.json")
        print("4. Run this script again")
