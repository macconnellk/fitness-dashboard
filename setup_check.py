"""
Setup Checker
Validates that all configuration is correct before deploying to GitHub.
"""
import sys
from pathlib import Path
import config


def check_mark(condition):
    """Return checkmark or X based on condition."""
    return "✅" if condition else "❌"


def check_oura_config():
    """Check Oura configuration."""
    print("\n🔍 Checking Oura Ring configuration...")
    
    has_api = bool(config.OURA_API_TOKEN)
    has_export_creds = bool(config.OURA_EMAIL and config.OURA_PASSWORD)
    
    print(f"  {check_mark(has_api)} API Token configured")
    print(f"  {check_mark(has_export_creds)} Export credentials configured (email/password)")
    
    if not has_api and not has_export_creds:
        print("  ⚠️  WARNING: No Oura credentials configured")
        print("     Dashboard will use cached or mock data")
        return False
    
    if not has_api:
        print("  ℹ️  API token not set - will use export method")
    
    if not has_export_creds:
        print("  ℹ️  Export credentials not set - API only (will fail when subscription ends)")
    
    return True


def check_strava_config():
    """Check Strava configuration."""
    print("\n🏃 Checking Strava configuration...")
    
    has_client_id = bool(config.STRAVA_CLIENT_ID)
    has_client_secret = bool(config.STRAVA_CLIENT_SECRET)
    has_refresh_token = bool(config.STRAVA_REFRESH_TOKEN)
    
    print(f"  {check_mark(has_client_id)} Client ID configured")
    print(f"  {check_mark(has_client_secret)} Client Secret configured")
    print(f"  {check_mark(has_refresh_token)} Refresh Token configured")
    
    all_set = has_client_id and has_client_secret and has_refresh_token
    
    if not all_set:
        print("  ⚠️  WARNING: Incomplete Strava configuration")
        print("     Weekly training progress will not be available")
        return False
    
    return True


def check_sheets_config():
    """Check Google Sheets configuration."""
    print("\n📊 Checking Google Sheets configuration...")
    
    has_sheet_id = bool(config.GOOGLE_SHEET_ID)
    
    print(f"  {check_mark(has_sheet_id)} Sheet ID configured")
    
    if not has_sheet_id:
        print("  ⚠️  WARNING: No Sheet ID configured")
        print("     Lean mass tracking will not be available")
        return False
    
    # Validate sheet ID format
    if has_sheet_id:
        sheet_id = config.GOOGLE_SHEET_ID
        if len(sheet_id) < 20 or ' ' in sheet_id or '/' in sheet_id:
            print("  ⚠️  WARNING: Sheet ID looks invalid")
            print(f"     Current value: '{sheet_id}'")
            print("     Should be ~44 characters, no spaces or slashes")
            return False
    
    return True


def check_files():
    """Check that all required files exist."""
    print("\n📁 Checking project files...")
    
    required_files = [
        'config.py',
        'analyzer.py',
        'generate_dashboard.py',
        'dashboard_template.html',
        'requirements.txt',
        '.github/workflows/daily-run.yml',
        '.gitignore',
        'README.md',
        'DEPLOYMENT_GUIDE.md'
    ]
    
    all_exist = True
    for file in required_files:
        exists = Path(file).exists()
        print(f"  {check_mark(exists)} {file}")
        if not exists:
            all_exist = False
    
    return all_exist


def check_git_setup():
    """Check if Git is configured."""
    print("\n🔧 Checking Git setup...")
    
    git_dir = Path('.git')
    is_repo = git_dir.exists() and git_dir.is_dir()
    
    print(f"  {check_mark(is_repo)} Git repository initialized")
    
    if not is_repo:
        print("  ℹ️  Run: git init")
        return False
    
    # Check for .env in gitignore
    gitignore = Path('.gitignore')
    if gitignore.exists():
        content = gitignore.read_text()
        env_ignored = '.env' in content
        print(f"  {check_mark(env_ignored)} .env in .gitignore (CRITICAL)")
        if not env_ignored:
            print("  ❌ DANGER: .env not in .gitignore!")
            print("     Your API keys could be exposed!")
            return False
    
    return True


def test_dashboard_generation():
    """Test if dashboard can be generated."""
    print("\n🎨 Testing dashboard generation...")
    
    try:
        import generate_dashboard
        print("  ✅ generate_dashboard.py imports successfully")
        
        # Try to generate with cached/mock data
        print("  ℹ️  Attempting to generate dashboard (may show warnings)...")
        print("  " + "-" * 60)
        
        import analyzer
        analysis = analyzer.generate_dashboard_data(force_refresh=False)
        
        print("  " + "-" * 60)
        print("  ✅ Analysis completed")
        
        output_path = generate_dashboard.generate_dashboard(
            analysis,
            output_path=Path('output/setup_test.html')
        )
        
        if output_path.exists():
            print("  ✅ Dashboard generated successfully")
            print(f"  📱 Preview: file://{output_path.absolute()}")
            return True
        else:
            print("  ❌ Dashboard file not created")
            return False
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def main():
    """Run all checks."""
    print("=" * 70)
    print("🔍 TRAINING DASHBOARD - SETUP CHECKER")
    print("=" * 70)
    print()
    print("This script validates your configuration before deployment.")
    print()
    
    results = {
        'oura': check_oura_config(),
        'strava': check_strava_config(),
        'sheets': check_sheets_config(),
        'files': check_files(),
        'git': check_git_setup(),
        'generation': test_dashboard_generation()
    }
    
    # Summary
    print("\n" + "=" * 70)
    print("📋 SETUP SUMMARY")
    print("=" * 70)
    
    print(f"\n  Oura Ring:      {check_mark(results['oura'])}")
    print(f"  Strava:         {check_mark(results['strava'])}")
    print(f"  Google Sheets:  {check_mark(results['sheets'])}")
    print(f"  Project Files:  {check_mark(results['files'])}")
    print(f"  Git Setup:      {check_mark(results['git'])}")
    print(f"  Test Generate:  {check_mark(results['generation'])}")
    
    all_critical = results['files'] and results['git'] and results['generation']
    some_data = results['oura'] or results['strava'] or results['sheets']
    
    print("\n" + "=" * 70)
    
    if all_critical and some_data:
        print("✅ READY TO DEPLOY!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. Review DEPLOYMENT_GUIDE.md")
        print("  2. Create GitHub repository")
        print("  3. Push code to GitHub")
        print("  4. Add secrets to GitHub")
        print("  5. Enable GitHub Pages")
        print()
        return 0
    
    elif all_critical:
        print("⚠️  PARTIALLY READY")
        print("=" * 70)
        print()
        print("Core setup is complete, but you're missing data sources:")
        print()
        if not results['oura']:
            print("  • Configure Oura credentials in .env")
        if not results['strava']:
            print("  • Configure Strava API in .env")
        if not results['sheets']:
            print("  • Configure Google Sheet ID in .env")
        print()
        print("Dashboard will work but show limited data.")
        print("You can deploy now and add credentials later.")
        print()
        return 0
    
    else:
        print("❌ NOT READY")
        print("=" * 70)
        print()
        print("Please fix the issues above before deploying.")
        print()
        return 1


if __name__ == '__main__':
    sys.exit(main())
