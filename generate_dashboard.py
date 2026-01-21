"""
Dashboard Generator
Generates the HTML dashboard from analyzed data.
"""
from datetime import datetime
from pathlib import Path
from jinja2 import Template
import config
import analyzer


def format_time(dt_string: str) -> str:
    """Format ISO datetime string for display."""
    try:
        dt = datetime.fromisoformat(dt_string)
        return dt.strftime('%a, %b %d at %I:%M %p')
    except:
        return dt_string


def get_status_class(status: str) -> str:
    """Convert status to CSS class."""
    mapping = {
        'GREEN': 'green',
        'YELLOW': 'yellow',
        'ORANGE': 'orange',
        'RED': 'red'
    }
    return mapping.get(status, 'yellow')


def get_sleep_status_class(rating: str) -> str:
    """Convert sleep rating to CSS class."""
    if rating in ['Excellent', 'Good']:
        return 'good'
    elif rating in ['Fair']:
        return 'fair'
    else:
        return 'poor'


def calculate_progress_class(current: int, target: int) -> str:
    """Determine progress bar class based on completion."""
    if current >= target:
        return 'complete'
    elif current >= target * 0.7:
        return ''  # Default blue
    else:
        return 'warning'


def generate_dashboard(analysis: dict, output_path: Path = None) -> Path:
    """
    Generate HTML dashboard from analysis data.
    
    Args:
        analysis: Analysis dictionary from analyzer.py
        output_path: Path to save HTML (defaults to output/index.html)
    
    Returns:
        Path to generated HTML file
    """
    if output_path is None:
        output_path = config.OUTPUT_DIR / 'index.html'
    
    # Load template
    template_path = Path(__file__).parent / 'dashboard_template.html'
    with open(template_path, 'r') as f:
        template_content = f.read()
    
    template = Template(template_content)
    
    # =========================================================================
    # PREPARE TEMPLATE VARIABLES
    # =========================================================================
    
    # Header
    vars = {
        'updated_time': format_time(analysis['generated_at']),
        'generated_date': datetime.now().strftime('%Y-%m-%d')
    }
    
    # Warnings
    vars['warnings'] = analysis.get('warnings', []) + analysis.get('errors', [])
    
    # Main Recommendation
    recovery = analysis.get('recovery', {})
    vars['recommendation'] = recovery.get('recommendation', 'LOADING')
    vars['recommendation_emoji'] = recovery.get('emoji', '⏳')
    vars['recommendation_detail'] = recovery.get('detail_text', 'Analyzing data...')
    vars['recovery_score'] = recovery.get('score', 0)
    vars['recovery_rating'] = analysis.get('readiness', {}).get('breakdown', {}).get('rating', 'Unknown')
    vars['status_class'] = get_status_class(recovery.get('status', 'YELLOW'))
    vars['trend_text'] = recovery.get('trend', 'stable').capitalize()
    vars['trend_emoji'] = recovery.get('trend_emoji', '➡️')
    
    # Recovery Card
    sleep_data = analysis.get('sleep', {})
    sleep_breakdown = sleep_data.get('breakdown', {})
    readiness_data = analysis.get('readiness', {})
    readiness_breakdown = readiness_data.get('breakdown', {})
    
    vars['sleep_hours'] = sleep_breakdown.get('duration_hours', 0)
    vars['hrv_value'] = readiness_breakdown.get('hrv', 0)
    vars['hrv_trend'] = readiness_breakdown.get('hrv_trend', '→')
    vars['rhr_value'] = readiness_breakdown.get('rhr', 0)
    vars['rhr_trend'] = readiness_breakdown.get('rhr_trend', '→')
    vars['sleep_status'] = sleep_breakdown.get('rating', 'Unknown')
    vars['sleep_status_class'] = get_sleep_status_class(sleep_breakdown.get('rating', 'Fair'))
    
    # Training Card
    training = analysis.get('training', {})
    
    lifts_done = training.get('lifts', 0)
    lifts_target = training.get('lift_target', 2)
    runs_done = training.get('runs', 0)
    runs_target = training.get('run_target', 3)
    run_minutes = training.get('run_minutes', 0)
    run_minutes_target = training.get('run_minutes_target', 60)
    
    vars['lifts_done'] = lifts_done
    vars['lifts_target'] = lifts_target
    vars['lifts_percent'] = min(100, int((lifts_done / lifts_target) * 100)) if lifts_target > 0 else 0
    vars['lifts_class'] = calculate_progress_class(lifts_done, lifts_target)
    
    vars['runs_done'] = runs_done
    vars['runs_target'] = runs_target
    vars['runs_percent'] = min(100, int((runs_done / runs_target) * 100)) if runs_target > 0 else 0
    vars['runs_class'] = calculate_progress_class(runs_done, runs_target)
    
    vars['run_minutes'] = run_minutes
    vars['run_minutes_target'] = run_minutes_target
    vars['minutes_percent'] = min(100, int((run_minutes / run_minutes_target) * 100)) if run_minutes_target > 0 else 0
    vars['minutes_class'] = calculate_progress_class(run_minutes, run_minutes_target)
    
    # Training action text
    runs_needed = runs_target - runs_done
    lifts_needed = lifts_target - lifts_done
    
    if runs_needed > 0 and lifts_needed > 0:
        vars['training_action'] = f"Need {runs_needed} run(s) + {lifts_needed} lift(s)"
    elif runs_needed > 0:
        vars['training_action'] = f"Need {runs_needed} more run(s)"
    elif lifts_needed > 0:
        vars['training_action'] = f"Need {lifts_needed} more lift(s)"
    else:
        vars['training_action'] = "All targets met! 🎉"
    
    # Action Items
    vars['action_items'] = analysis.get('action_items', [])
    
    # Lean Mass
    lean_mass = analysis.get('lean_mass')
    if lean_mass:
        current = lean_mass.get('current', {})
        goals = lean_mass.get('goals', {})
        
        vars['lean_mass'] = True
        vars['current_weight'] = current.get('weight', 0)
        vars['current_bf'] = current.get('bf_pct', 0)
        vars['lean_mass_lbs'] = round(current.get('lean_mass', 0), 1)
        vars['ffmi'] = current.get('ffmi', 0)
        vars['percentile'] = f"{current.get('percentile', 'N/A')}"
        vars['target_weight'] = goals.get('target_weight', 175)
        
        # Determine phase (simplified - could be enhanced)
        current_date = current.get('date', '')
        if 'Cut' in current_date or current.get('bf_pct', 20) > 17:
            vars['phase_name'] = 'Cut Phase'
        elif 'Bulk' in current_date:
            vars['phase_name'] = 'Bulk Phase'
        else:
            vars['phase_name'] = 'Maintenance'
    else:
        vars['lean_mass'] = False
    
    # =========================================================================
    # RENDER TEMPLATE
    # =========================================================================
    
    html = template.render(**vars)
    
    # Save to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(html)
    
    print(f"\n✓ Dashboard generated: {output_path}")
    print(f"  Open in browser: file://{output_path.absolute()}")
    
    return output_path


def main(force_refresh: bool = False):
    """
    Main entry point for dashboard generation.
    
    Args:
        force_refresh: If True, fetch fresh data from all sources
    """
    print("=" * 70)
    print("🎨 GENERATING TRAINING DASHBOARD")
    print("=" * 70)
    
    # Run analysis
    analysis = analyzer.generate_dashboard_data(force_refresh=force_refresh)
    
    # Generate dashboard
    output_path = generate_dashboard(analysis)
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ DASHBOARD READY!")
    print("=" * 70)
    
    recovery = analysis.get('recovery', {})
    print(f"\n🎯 Today's Call: {recovery.get('recommendation', 'N/A')}")
    print(f"   {recovery.get('detail_text', '')}")
    
    if analysis.get('warnings'):
        print(f"\n⚠️  {len(analysis['warnings'])} warnings - check dashboard for details")
    
    print(f"\n📱 Open: file://{output_path.absolute()}")
    print(f"   Or deploy to GitHub Pages for mobile access")
    
    return output_path


if __name__ == '__main__':
    import sys
    
    # Check for --force flag
    force = '--force' in sys.argv or '-f' in sys.argv
    
    if force:
        print("🔄 Force refresh enabled - fetching fresh data from all sources\n")
    
    main(force_refresh=force)
