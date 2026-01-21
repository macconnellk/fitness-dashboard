import os
import pandas as pd
from datetime import datetime

def fetch_lean_mass_data():
    """Fetch lean mass data from published CSV - both actuals and goals"""
    csv_url = os.environ.get('GOOGLE_SHEET_CSV_URL')
    
    if not csv_url:
        print("⚠️  No Google Sheet CSV URL configured")
        return None
    
    try:
        # Read CSV directly from URL
        df = pd.read_csv(csv_url)
        
        # Clean up - remove completely empty rows
        df = df.dropna(how='all')
        
        # ACTUALS (Left side) - Get most recent entry with actual measurements
        actuals_df = df[df['Weight (lbs)'].notna()].copy()
        if not actuals_df.empty and 'Date' in actuals_df.columns:
            actuals_df['Date'] = pd.to_datetime(actuals_df['Date'], errors='coerce')
            actuals_df = actuals_df.dropna(subset=['Date'])
            actuals_df = actuals_df.sort_values('Date', ascending=False)
            latest_actual = actuals_df.iloc[0]
        else:
            latest_actual = None
        
        # GOALS (Right side) - Get current week's targets
        goals_df = df[df['Week'].notna()].copy()
        if not goals_df.empty:
            # Get most recent week's goal
            current_week_goal = goals_df.iloc[-1]  # Last row with goals
        else:
            current_week_goal = None
        
        # Build combined data structure
        data = {}
        
        # Actuals from left side
        if latest_actual is not None:
            data['actual'] = {
                'date': latest_actual.get('Date', datetime.now()).isoformat() if pd.notna(latest_actual.get('Date')) else datetime.now().isoformat(),
                'weight_lbs': latest_actual.get('Weight (lbs)', None),
                'body_fat_pct': latest_actual.get('Body Fat %', None),
                'fat_free_mass_lbs': latest_actual.get('Fat-Free Mass (lbs)', None),
                'lean_mass_lbs': latest_actual.get('Fat-Free Mass (lbs)', None),
                'neck_inches': latest_actual.get('Neck Circumference (inches)', None),
                'waist_inches': latest_actual.get('Waist Circumference (inches)', None)
            }
        
        # Goals from right side
        if current_week_goal is not None:
            data['goals'] = {
                'week': int(current_week_goal.get('Week', 0)) if pd.notna(current_week_goal.get('Week')) else None,
                'phase': current_week_goal.get('Phase', 'Unknown'),
                'target_weight_lbs': current_week_goal.get('Weight', None),
                'target_bf_pct': current_week_goal.get('BF%', None),
                'target_lean_lbs': current_week_goal.get('Lean', None),
                'target_fat_lbs': current_week_goal.get('Fat', None),
                'target_ffmi': current_week_goal.get('FFMI', None),
                'lifts_per_week': int(current_week_goal.get('Lifts', 0)) if pd.notna(current_week_goal.get('Lifts')) else None
            }
        
        # Static goals from top of sheet
        data['long_term_goals'] = {
            'height_inches': 70,
            'weight_goal_lbs': 175,
            'bf_goal_pct': 15.5
        }
        
        print(f"✅ Fetched lean mass data:")
        print(f"   Actual: {data.get('actual', {}).get('weight_lbs')} lbs, {data.get('actual', {}).get('body_fat_pct')}% BF")
        print(f"   Goal Week {data.get('goals', {}).get('week')}: {data.get('goals', {}).get('lifts_per_week')} lifts/week")
        
        return data
        
    except Exception as e:
        print(f"❌ Error fetching Google Sheet: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    data = fetch_lean_mass_data()
    if data:
        print(f"\nFull data structure:")
        import json
        print(json.dumps(data, indent=2, default=str))
