"""
Test Dashboard Generator
Creates a sample dashboard with mock data for testing.
"""
from datetime import datetime
from pathlib import Path
import generate_dashboard


def create_mock_analysis() -> dict:
    """Create mock analysis data for testing."""
    return {
        'generated_at': datetime.now().isoformat(),
        'warnings': [
            'Using mock data - configure API credentials for real data'
        ],
        'errors': [],
        
        'oura_status': {
            'success': True,
            'source': 'mock',
            'age_days': 0,
            'message': 'Mock data'
        },
        
        'baselines': {
            'hrv_baseline': 65.0,
            'rhr_baseline': 52.0,
            'typical_sleep_hours': 7.5,
            'hrv_samples': 14,
            'rhr_samples': 14,
            'calculated_at': datetime.now().isoformat(),
            'data_source': 'mock'
        },
        
        'sleep': {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'score': 78,
            'breakdown': {
                'duration_hours': 7.2,
                'duration_score': 35,
                'efficiency_pct': 89.5,
                'efficiency_score': 25,
                'deep_pct': 18.5,
                'deep_score': 15,
                'rem_pct': 22.0,
                'rem_score': 15,
                'rating': 'Good',
                'emoji': '😊'
            },
            'oura_score': None
        },
        
        'readiness': {
            'score': 76,
            'breakdown': {
                'hrv': 68.0,
                'hrv_baseline': 65.0,
                'hrv_change_pct': 4.6,
                'hrv_score': 30,
                'hrv_trend': '↑',
                'rhr': 53.0,
                'rhr_baseline': 52.0,
                'rhr_change': 1.0,
                'rhr_score': 15,
                'rhr_trend': '→',
                'sleep_component': 19.5,
                'recent_workouts': 2,
                'load_score': 10,
                'rating': 'Good to go',
                'emoji': '👍'
            }
        },
        
        'recovery': {
            'score': 76,
            'trend': 'stable',
            'trend_emoji': '➡️',
            'status': 'YELLOW',
            'emoji': '🟢',
            'recommendation': 'PROCEED',
            'detail_text': 'Normal training fatigue. Train as planned. Listen to your body on warm-ups.'
        },
        
        'training': {
            'runs': 1,
            'lifts': 2,
            'run_minutes': 35,
            'run_target': 3,
            'lift_target': 2,
            'lift_bonus_target': 3,
            'run_minutes_target': 60,
            'activities': [],
            'week_start': '2026-01-19',
            'fetched_at': datetime.now().isoformat()
        },
        
        'lean_mass': {
            'current': {
                'date': 'Sun 1/18/2026',
                'weight': 168.7,
                'bf_pct': 19.4,
                'lean_mass': 135.9,
                'ffmi': 19.54,
                'percentile': 58
            },
            'recent_trend': [],
            'goals': {
                'target_weight': 175.0,
                'target_bf_pct': 15.5,
                'target_lean_mass': 147.625
            },
            'fetched_at': datetime.now().isoformat()
        },
        
        'action_items': [
            'Need 2 more runs this week (13+ min each)',
            'All lift targets met! 🎉',
            'Aim for 7-8 hours sleep tonight'
        ]
    }


def main():
    """Generate test dashboard with mock data."""
    print("=" * 70)
    print("🧪 GENERATING TEST DASHBOARD (MOCK DATA)")
    print("=" * 70)
    print()
    print("This creates a sample dashboard to show you what it will look like")
    print("when connected to real data sources.")
    print()
    
    # Create mock analysis
    analysis = create_mock_analysis()
    
    # Generate dashboard
    output_path = generate_dashboard.generate_dashboard(
        analysis,
        output_path=Path('output/test_dashboard.html')
    )
    
    print("\n" + "=" * 70)
    print("✅ TEST DASHBOARD READY!")
    print("=" * 70)
    print(f"\n📱 Open in browser: file://{output_path.absolute()}")
    print()
    print("To generate with real data:")
    print("  1. Configure API credentials in .env")
    print("  2. Run: python generate_dashboard.py")
    print()


if __name__ == '__main__':
    main()
