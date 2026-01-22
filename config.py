"""
Configuration management for Fitness Dashboard.
Loads settings from .env file and provides defaults.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =============================================================================
# PROJECT PATHS
# =============================================================================
PROJECT_ROOT = Path(__file__).parent
CACHE_DIR = PROJECT_ROOT / os.getenv('CACHE_DIR', '.cache')
OUTPUT_DIR = PROJECT_ROOT / 'output'

# Create directories if they don't exist
CACHE_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# =============================================================================
# OURA RING CONFIGURATION (Updated for OAuth2)
# =============================================================================
OURA_CLIENT_ID = os.getenv('OURA_CLIENT_ID')
OURA_CLIENT_SECRET = os.getenv('OURA_CLIENT_SECRET')
OURA_REFRESH_TOKEN = os.getenv('OURA_REFRESH_TOKEN')

OURA_EMAIL = os.getenv('OURA_EMAIL')
OURA_PASSWORD = os.getenv('OURA_PASSWORD')
OURA_API_BASE_URL = 'https://api.ouraring.com/v2'

# =============================================================================
# STRAVA CONFIGURATION
# =============================================================================
STRAVA_CLIENT_ID = os.getenv('STRAVA_CLIENT_ID')
STRAVA_CLIENT_SECRET = os.getenv('STRAVA_CLIENT_SECRET')
STRAVA_REFRESH_TOKEN = os.getenv('STRAVA_REFRESH_TOKEN')

# =============================================================================
# GOOGLE SHEETS CONFIGURATION
# =============================================================================
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
GOOGLE_CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')

# =============================================================================
# TRAINING TARGETS
# =============================================================================
WEEKLY_LIFT_TARGET = int(os.getenv('WEEKLY_LIFT_TARGET', 2))
WEEKLY_LIFT_BONUS = int(os.getenv('WEEKLY_LIFT_BONUS', 3))
WEEKLY_RUN_TARGET = int(os.getenv('WEEKLY_RUN_TARGET', 3))
WEEKLY_RUN_MINUTES_TARGET = int(os.getenv('WEEKLY_RUN_MINUTES_TARGET', 60))

# =============================================================================
# BASELINE VALUES
# =============================================================================
HRV_BASELINE = float(os.getenv('HRV_BASELINE', 60))
RHR_BASELINE = float(os.getenv('RHR_BASELINE', 55))

# =============================================================================
# CACHE SETTINGS
# =============================================================================
MAX_CACHE_AGE_DAYS = int(os.getenv('MAX_CACHE_AGE_DAYS', 3))

# =============================================================================
# TIMEZONE
# =============================================================================
TIMEZONE = os.getenv('TIMEZONE', 'America/New_York')

# =============================================================================
# VALIDATION
# =============================================================================
def validate_config():
    """Validate that required configuration is present."""
    errors = []
    
    # Check Oura (either OAuth2 Refresh Token or email/password for scraper)
    if not all([OURA_CLIENT_ID, OURA_CLIENT_SECRET, OURA_REFRESH_TOKEN]) and not (OURA_EMAIL and OURA_PASSWORD):
        errors.append("Missing Oura configuration: Need OURA_CLIENT_ID, OURA_CLIENT_SECRET, and OURA_REFRESH_TOKEN (for API) or OURA_EMAIL/OURA_PASSWORD (for Scraper)")
    
    # Check Strava
    if not all([STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, STRAVA_REFRESH_TOKEN]):
        errors.append("Missing Strava configuration: Need CLIENT_ID, CLIENT_SECRET, and REFRESH_TOKEN")
    
    # Check Google Sheets
    if not GOOGLE_SHEET_ID:
        errors.append("Missing GOOGLE_SHEET_ID")
    
    if errors:
        print("❌ Configuration Errors:")
        for error in errors:
            print(f"    - {error}")
        return False
    
    print("✓ Configuration validated successfully")
    return True

if __name__ == '__main__':
    validate_config()
