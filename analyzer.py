"""
Training Analyzer
Combines all data sources and generates training recommendations.
"""
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import oura_manager
import fetch_strava
import fetch_sheets
import calculate_baselines
import scoring


class TrainingAnalyzer:
    """Analyzes all data and generates training recommendations."""
    
    def __init__(self):
        self.baseline_calc = calculate_baselines.baseline_calculator
    
    def analyze(self, force_refresh: bool = False) -> Dict:
        """
        Perform complete analysis of all data sources.
        
        Args:
            force_refresh: If True, fetch fresh data (skip cache)
        
        Returns:
            Complete analysis dictionary ready for dashboard
        """
        print("=" * 70)
        print("🎯 TRAINING DASHBOARD ANALYSIS")
        print("=" * 70)
        
        analysis = {
            'generated_at': datetime.now().isoformat(),
            'errors': [],
            'warnings': []
        }
        
        # =====================================================================
        # 1. FETCH OURA DATA
        # =====================================================================
        print("\n📊 Fetching Oura Ring data...")
        oura_data, oura_status = oura_manager.get_oura_data(force_refresh=force_refresh)
        
        analysis['oura_status'] = {
            'success': oura_status.success,
            'source': oura_status.source,
            'age_days': oura_status.age_days,
            'message': oura_status.message
        }
        
        if not oura_status.success:
            analysis['errors'].append(f"Oura data unavailable: {oura_status.message}")
        elif oura_status.age_days > 0:
            analysis['warnings'].append(f"Oura data is {oura_status.age_days} days old")
        
        # =====================================================================
        # 2. CALCULATE/UPDATE BASELINES
        # =====================================================================
        print("\n📐 Calculating baselines...")
        baselines = self.baseline_calc.get_baselines(
            oura_data=oura_data,
            force_recalculate=force_refresh,
            max_age_days=7
        )
        analysis['baselines'] = baselines
        
        # =====================================================================
        # 3. ANALYZE OURA DATA
        # =====================================================================
        if oura_data:
            print("\n😴 Analyzing sleep and recovery...")
            
            # Get latest sleep data
            latest_sleep = oura_manager.get_latest_sleep_data(oura_data)
            latest_readiness = oura_manager.get_latest_readiness_data(oura_data)
            
            if latest_sleep:
                # Calculate custom sleep score
                sleep_score, sleep_breakdown = scoring.calculate_sleep_score(
                    latest_sleep, baselines
                )
                
                analysis['sleep'] = {
                    'date': latest_sleep.get('day'),
                    'score': sleep_score,
                    'breakdown': sleep_breakdown,
                    'oura_score': latest_sleep.get('score')  # Original Oura score if available
                }
                
                print(f"  Sleep: {sleep_score}/100 ({sleep_breakdown['rating']})")
                print(f"    Duration: {sleep_breakdown['duration_hours']}h")
                print(f"    Efficiency: {sleep_breakdown['efficiency_pct']}%")
                print(f"    Deep: {sleep_breakdown['deep_pct']}% | REM: {sleep_breakdown['rem_pct']}%")
            else:
                analysis['warnings'].append("No sleep data available")
                sleep_score = 70  # Default
            
            # Extract HRV and RHR
            if latest_readiness:
                hrv = latest_readiness.get('heart_rate_variability') or latest_readiness.get('hrv_balance') or baselines['hrv_baseline']
                # RHR might be in sleep data
                rhr = latest_sleep.get('lowest_heart_rate') if latest_sleep else baselines['rhr_baseline']
            elif latest_sleep:
                hrv = baselines['hrv_baseline']
                rhr = latest_sleep.get('lowest_heart_rate') or baselines['rhr_baseline']
            else:
                hrv = baselines['hrv_baseline']
                rhr = baselines['rhr_baseline']
                analysis['warnings'].append("Using baseline HRV/RHR (no recent data)")
        else:
            # No Oura data - use defaults
            analysis['warnings'].append("No Oura data - using estimated values")
            sleep_score = 70
            hrv = baselines['hrv_baseline']
            rhr = baselines['rhr_baseline']
            analysis['sleep'] = {
                'score': sleep_score,
                'breakdown': {'rating': 'Unknown', 'emoji': '❓'}
            }
        
        # =====================================================================
        # 4. FETCH STRAVA DATA
        # =====================================================================
        print("\n🏃 Fetching Strava activities...")
        strava_data = fetch_strava.fetch_strava_data(use_cache=not force_refresh)
        
        if strava_data:
            analysis['training'] = strava_data
            
            # Get recent activities for readiness calculation (last 3 days)
            recent_activities = []
            if strava_data.get('activities'):
                cutoff = datetime.now() - timedelta(days=3)
                for act in strava_data['activities']:
                    act_date = datetime.fromisoformat(act['start_date'].replace('Z', '+00:00'))
                    if act_date > cutoff:
                        recent_activities.append(act)
            
            print(f"  This week: {strava_data['runs']}/{strava_data['run_target']} runs, "
                  f"{strava_data['lifts']}/{strava_data['lift_target']} lifts")
            print(f"  Run minutes: {strava_data['run_minutes']}/{strava_data['run_minutes_target']}")
        else:
            analysis['warnings'].append("No Strava data available")
            analysis['training'] = {
                'runs': 0,
                'lifts': 0,
                'run_minutes': 0,
                'run_target': 3,
                'lift_target': 2,
                'run_minutes_target': 60
            }
            recent_activities = []
        
        # =====================================================================
        # 5. CALCULATE READINESS SCORE
        # =====================================================================
        print("\n💪 Calculating readiness...")
        
        readiness_score, readiness_breakdown = scoring.calculate_readiness_score(
            sleep_score=sleep_score,
            hrv=hrv,
            rhr=rhr,
            recent_activities=recent_activities,
            baselines=baselines
        )
        
        analysis['readiness'] = {
            'score': readiness_score,
            'breakdown': readiness_breakdown
        }
        
        print(f"  Readiness: {readiness_score}/100 ({readiness_breakdown['rating']})")
        print(f"    HRV: {readiness_breakdown['hrv']} {readiness_breakdown['hrv_trend']} (baseline: {readiness_breakdown['hrv_baseline']})")
        print(f"    RHR: {readiness_breakdown['rhr']} {readiness_breakdown['rhr_trend']} (baseline: {readiness_breakdown['rhr_baseline']})")
        
        # =====================================================================
        # 6. CALCULATE RECOVERY STATUS & RECOMMENDATION
        # =====================================================================
        print("\n🎯 Generating training recommendation...")
        
        # Get trend (would need historical readiness scores - simplified for now)
        recent_scores = [readiness_score]  # In full version, would pull from history
        
        status, recommendation, recovery_details = scoring.calculate_recovery_status(
            readiness_score=readiness_score,
            recent_readiness_scores=recent_scores
        )
        
        analysis['recovery'] = recovery_details
        
        print(f"  Status: {recovery_details['emoji']} {recovery_details['status']}")
        print(f"  Recommendation: {recommendation}")
        print(f"  {recovery_details['detail_text']}")
        
        # =====================================================================
        # 7. FETCH LEAN MASS DATA
        # =====================================================================
        print("\n📈 Fetching lean mass data...")
        lean_mass_data = fetch_sheets.fetch_lean_mass_data(use_cache=not force_refresh)
        
        if lean_mass_data:
            analysis['lean_mass'] = lean_mass_data
            current = lean_mass_data['current']
            print(f"  Current: {current['weight']} lbs @ {current['bf_pct']}% BF")
            print(f"  Lean mass: {current['lean_mass']} lbs (FFMI: {current['ffmi']})")
        else:
            analysis['warnings'].append("No lean mass data available")
        
        # =====================================================================
        # 8. GENERATE WEEKLY ACTION ITEMS
        # =====================================================================
        print("\n📋 Generating action items...")
        action_items = self._generate_action_items(analysis)
        analysis['action_items'] = action_items
        
        for item in action_items:
            print(f"  • {item}")
        
        # =====================================================================
        # SUMMARY
        # =====================================================================
        print("\n" + "=" * 70)
        print(f"✓ Analysis complete!")
        print(f"  {len(analysis['errors'])} errors, {len(analysis['warnings'])} warnings")
        print("=" * 70)
        
        return analysis
    
    def _generate_action_items(self, analysis: Dict) -> List[str]:
        """Generate specific action items based on analysis."""
        items = []
        
        # Training needs
        training = analysis.get('training', {})
        runs_needed = training.get('run_target', 3) - training.get('runs', 0)
        lifts_needed = training.get('lift_target', 2) - training.get('lifts', 0)
        minutes_needed = training.get('run_minutes_target', 60) - training.get('run_minutes', 0)
        
        if runs_needed > 0:
            avg_min = minutes_needed / runs_needed if runs_needed > 0 else 20
            items.append(f"Need {runs_needed} more run(s) this week ({avg_min:.0f}+ min each)")
        
        if lifts_needed > 0:
            items.append(f"Need {lifts_needed} more lift session(s) this week")
        
        if runs_needed == 0 and minutes_needed > 0:
            items.append(f"Need {minutes_needed} more running minutes this week")
        
        # Recovery-based suggestions
        recovery = analysis.get('recovery', {})
        if recovery.get('status') == 'RED':
            items.append("Prioritize recovery today - consider rest or very light activity")
        elif recovery.get('status') == 'ORANGE':
            items.append("Reduce workout intensity or volume today")
        
        # Sleep suggestions
        sleep = analysis.get('sleep', {})
        if sleep and sleep.get('breakdown', {}).get('duration_hours', 8) < 7:
            items.append("Aim for 7-8 hours sleep tonight")
        
        if not items:
            items.append("All weekly targets met! Maintain current training pace")
        
        return items


def generate_dashboard_data(force_refresh: bool = False) -> Dict:
    """
    Generate complete data for dashboard.
    
    Args:
        force_refresh: If True, fetch fresh data
    
    Returns:
        Dashboard data dictionary
    """
    analyzer = TrainingAnalyzer()
    return analyzer.analyze(force_refresh=force_refresh)


if __name__ == '__main__':
    # Test analyzer
    print("Testing Training Analyzer...")
    print()
    
    # Run analysis
    analysis = generate_dashboard_data(force_refresh=False)
    
    # Show summary
    print("\n" + "=" * 70)
    print("ANALYSIS SUMMARY")
    print("=" * 70)
    
    print(f"\n📊 Data Sources:")
    print(f"  Oura: {analysis['oura_status']['source']} ({analysis['oura_status']['message']})")
    print(f"  Baselines: {analysis['baselines']['hrv_samples']} HRV, {analysis['baselines']['rhr_samples']} RHR samples")
    
    if 'sleep' in analysis:
        sleep = analysis['sleep']
        print(f"\n😴 Sleep: {sleep.get('score', 'N/A')}/100 ({sleep.get('breakdown', {}).get('rating', 'N/A')})")
    
    if 'readiness' in analysis:
        readiness = analysis['readiness']
        print(f"\n💪 Readiness: {readiness['score']}/100 ({readiness['breakdown']['rating']})")
    
    if 'recovery' in analysis:
        recovery = analysis['recovery']
        print(f"\n🎯 Today's Call: {recovery['recommendation']}")
        print(f"   {recovery['detail_text']}")
    
    if 'training' in analysis:
        training = analysis['training']
        print(f"\n🏃 This Week:")
        print(f"  Runs: {training['runs']}/{training['run_target']} ({training['run_minutes']}/{training['run_minutes_target']} min)")
        print(f"  Lifts: {training['lifts']}/{training['lift_target']}")
    
    if 'action_items' in analysis:
        print(f"\n📋 Action Items:")
        for item in analysis['action_items']:
            print(f"  • {item}")
    
    if analysis.get('warnings'):
        print(f"\n⚠️  Warnings:")
        for warning in analysis['warnings']:
            print(f"  • {warning}")
    
    if analysis.get('errors'):
        print(f"\n❌ Errors:")
        for error in analysis['errors']:
            print(f"  • {error}")
