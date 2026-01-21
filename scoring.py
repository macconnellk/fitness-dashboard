"""
Scoring Algorithms
Custom sleep, readiness, and recovery scoring based on Oura data.
"""
from typing import Dict, Optional, List, Tuple
from datetime import datetime
import config


def calculate_sleep_score(sleep_data: Dict, baselines: Dict) -> Tuple[int, Dict]:
    """
    Calculate custom sleep score (0-100).
    
    Components:
    - Duration (40 points): Optimal 7-9 hours
    - Efficiency (30 points): Time asleep / time in bed
    - Deep Sleep % (15 points): Should be 15-25% of total
    - REM Sleep % (15 points): Should be 20-25% of total
    
    Args:
        sleep_data: Sleep data from Oura
        baselines: Baseline values
    
    Returns:
        Tuple of (score, breakdown_dict)
    """
    breakdown = {}
    
    # Extract sleep metrics (handle different API formats)
    total_sleep_seconds = sleep_data.get('total_sleep_duration', 0)
    time_in_bed_seconds = sleep_data.get('time_in_bed', total_sleep_seconds)
    deep_sleep_seconds = sleep_data.get('deep_sleep_duration', 0)
    rem_sleep_seconds = sleep_data.get('rem_sleep_duration', 0)
    light_sleep_seconds = sleep_data.get('light_sleep_duration', 0)
    
    # Convert to hours/percentages
    total_sleep_hours = total_sleep_seconds / 3600
    time_in_bed_hours = time_in_bed_seconds / 3600
    
    # Calculate efficiency
    if time_in_bed_seconds > 0:
        efficiency = (total_sleep_seconds / time_in_bed_seconds) * 100
    else:
        efficiency = 0
    
    # Calculate sleep stage percentages
    if total_sleep_seconds > 0:
        deep_pct = (deep_sleep_seconds / total_sleep_seconds) * 100
        rem_pct = (rem_sleep_seconds / total_sleep_seconds) * 100
    else:
        deep_pct = 0
        rem_pct = 0
    
    # === DURATION SCORE (40 points) ===
    if total_sleep_hours >= 8:
        duration_score = 40
    elif total_sleep_hours >= 7:
        duration_score = 35
    elif total_sleep_hours >= 6:
        duration_score = 25
    else:
        duration_score = 10
    
    breakdown['duration_hours'] = round(total_sleep_hours, 1)
    breakdown['duration_score'] = duration_score
    
    # === EFFICIENCY SCORE (30 points) ===
    if efficiency >= 90:
        efficiency_score = 30
    elif efficiency >= 85:
        efficiency_score = 25
    elif efficiency >= 80:
        efficiency_score = 20
    else:
        efficiency_score = 10
    
    breakdown['efficiency_pct'] = round(efficiency, 1)
    breakdown['efficiency_score'] = efficiency_score
    
    # === DEEP SLEEP SCORE (15 points) ===
    if 15 <= deep_pct <= 25:
        deep_score = 15
    elif 10 <= deep_pct < 15 or 25 < deep_pct <= 30:
        deep_score = 10
    else:
        deep_score = 5
    
    breakdown['deep_pct'] = round(deep_pct, 1)
    breakdown['deep_score'] = deep_score
    
    # === REM SLEEP SCORE (15 points) ===
    if 20 <= rem_pct <= 25:
        rem_score = 15
    elif 15 <= rem_pct < 20 or 25 < rem_pct <= 30:
        rem_score = 10
    else:
        rem_score = 5
    
    breakdown['rem_pct'] = round(rem_pct, 1)
    breakdown['rem_score'] = rem_score
    
    # === TOTAL SCORE ===
    total_score = duration_score + efficiency_score + deep_score + rem_score
    
    # Score interpretation
    if total_score >= 85:
        breakdown['rating'] = 'Excellent'
        breakdown['emoji'] = '😴'
    elif total_score >= 70:
        breakdown['rating'] = 'Good'
        breakdown['emoji'] = '😊'
    elif total_score >= 55:
        breakdown['rating'] = 'Fair'
        breakdown['emoji'] = '😐'
    else:
        breakdown['rating'] = 'Poor'
        breakdown['emoji'] = '😴💤'
    
    return total_score, breakdown


def calculate_readiness_score(sleep_score: int, hrv: float, rhr: float,
                              recent_activities: List[Dict],
                              baselines: Dict) -> Tuple[int, Dict]:
    """
    Calculate custom readiness score (0-100).
    
    Components:
    - HRV Trend (35 points): 7-day average vs baseline
    - Resting HR (25 points): vs baseline
    - Sleep Score (25 points): From sleep scoring
    - Training Load (15 points): Based on recent workouts
    
    Args:
        sleep_score: Sleep score from calculate_sleep_score
        hrv: Current HRV value
        rhr: Current resting heart rate
        recent_activities: List of recent Strava activities
        baselines: Baseline values
    
    Returns:
        Tuple of (score, breakdown_dict)
    """
    breakdown = {}
    
    hrv_baseline = baselines.get('hrv_baseline', config.HRV_BASELINE)
    rhr_baseline = baselines.get('rhr_baseline', config.RHR_BASELINE)
    
    # === HRV TREND SCORE (35 points) ===
    if hrv_baseline > 0:
        hrv_change_pct = ((hrv - hrv_baseline) / hrv_baseline) * 100
    else:
        hrv_change_pct = 0
    
    if hrv_change_pct > 10:
        hrv_score = 35
    elif hrv_change_pct > 0:
        hrv_score = 30
    elif hrv_change_pct > -5:
        hrv_score = 25
    elif hrv_change_pct > -10:
        hrv_score = 15
    else:
        hrv_score = 5
    
    breakdown['hrv'] = round(hrv, 1)
    breakdown['hrv_baseline'] = round(hrv_baseline, 1)
    breakdown['hrv_change_pct'] = round(hrv_change_pct, 1)
    breakdown['hrv_score'] = hrv_score
    
    # Trend indicator
    if hrv_change_pct > 5:
        breakdown['hrv_trend'] = '↑'
    elif hrv_change_pct < -5:
        breakdown['hrv_trend'] = '↓'
    else:
        breakdown['hrv_trend'] = '→'
    
    # === RESTING HR SCORE (25 points) ===
    rhr_change = rhr - rhr_baseline
    
    if rhr_change < -3:
        rhr_score = 25
    elif rhr_change < 0:
        rhr_score = 20
    elif rhr_change == 0:
        rhr_score = 15
    elif rhr_change <= 5:
        rhr_score = 10
    else:
        rhr_score = 5
    
    breakdown['rhr'] = round(rhr, 1)
    breakdown['rhr_baseline'] = round(rhr_baseline, 1)
    breakdown['rhr_change'] = round(rhr_change, 1)
    breakdown['rhr_score'] = rhr_score
    
    # Trend indicator
    if rhr_change < -2:
        breakdown['rhr_trend'] = '↓'
    elif rhr_change > 2:
        breakdown['rhr_trend'] = '↑'
    else:
        breakdown['rhr_trend'] = '→'
    
    # === SLEEP SCORE COMPONENT (25 points) ===
    # Scale sleep score (0-100) to 0-25 points
    sleep_component = (sleep_score / 100) * 25
    breakdown['sleep_component'] = round(sleep_component, 1)
    
    # === TRAINING LOAD SCORE (15 points) ===
    # Count hard workouts in last 3 days
    # This is simplified - could be enhanced with activity intensity
    hard_workouts = len(recent_activities) if recent_activities else 0
    
    if hard_workouts == 0:
        load_score = 15  # Well rested
    elif hard_workouts <= 2:
        load_score = 10  # Normal load
    else:
        load_score = 5   # High load
    
    breakdown['recent_workouts'] = hard_workouts
    breakdown['load_score'] = load_score
    
    # === TOTAL SCORE ===
    total_score = hrv_score + rhr_score + sleep_component + load_score
    
    # Score interpretation
    if total_score >= 85:
        breakdown['rating'] = 'Ready to crush it'
        breakdown['emoji'] = '💪'
    elif total_score >= 70:
        breakdown['rating'] = 'Good to go'
        breakdown['emoji'] = '👍'
    elif total_score >= 55:
        breakdown['rating'] = 'Moderate'
        breakdown['emoji'] = '😐'
    else:
        breakdown['rating'] = 'Recovery needed'
        breakdown['emoji'] = '🛑'
    
    return int(total_score), breakdown


def calculate_recovery_status(readiness_score: int, 
                             recent_readiness_scores: List[int]) -> Tuple[str, str, Dict]:
    """
    Calculate overall recovery status for training decision.
    
    Zones (updated to be more realistic):
    - 85-100: GREEN - Train as planned
    - 70-84: YELLOW - Proceed with awareness (normal training fatigue)
    - 55-69: ORANGE - Modify workout
    - <55: RED - Back off
    
    Also considers trend (improving/stable/declining).
    
    Args:
        readiness_score: Current readiness score
        recent_readiness_scores: List of recent scores for trend
    
    Returns:
        Tuple of (status, recommendation, details_dict)
    """
    details = {
        'score': readiness_score
    }
    
    # Determine trend
    if len(recent_readiness_scores) >= 3:
        avg_recent = sum(recent_readiness_scores[-3:]) / 3
        if readiness_score > avg_recent + 5:
            trend = 'improving'
            trend_emoji = '📈'
        elif readiness_score < avg_recent - 5:
            trend = 'declining'
            trend_emoji = '📉'
        else:
            trend = 'stable'
            trend_emoji = '➡️'
    else:
        trend = 'stable'
        trend_emoji = '➡️'
    
    details['trend'] = trend
    details['trend_emoji'] = trend_emoji
    
    # Determine status and recommendation
    if readiness_score >= 85:
        status = 'GREEN'
        emoji = '✅'
        recommendation = 'TRAIN AS PLANNED'
        detail_text = 'All systems go. Proceed with scheduled workout.'
        
    elif readiness_score >= 70:
        status = 'YELLOW'
        emoji = '🟢'
        
        if trend == 'declining':
            recommendation = 'PROCEED WITH AWARENESS'
            detail_text = 'Normal training fatigue. Train as planned but monitor how you feel. Not the day for PRs if trend continues down.'
        else:
            recommendation = 'PROCEED'
            detail_text = 'Normal training fatigue. Train as planned. Listen to your body on warm-ups.'
        
    elif readiness_score >= 55:
        status = 'ORANGE'
        emoji = '🟡'
        recommendation = 'MODIFY WORKOUT'
        detail_text = 'Consider reducing intensity (80-85% instead of 90%+) or volume. Technical work and speed work still good.'
        
    else:
        status = 'RED'
        emoji = '🔴'
        recommendation = 'BACK OFF'
        detail_text = 'Active recovery, easy cardio, mobility, or complete rest. Your body needs recovery.'
    
    details['status'] = status
    details['emoji'] = emoji
    details['recommendation'] = recommendation
    details['detail_text'] = detail_text
    
    return status, recommendation, details


if __name__ == '__main__':
    # Test scoring algorithms
    print("Testing Scoring Algorithms...")
    print("=" * 60)
    
    # Test sleep score
    print("\n1. Testing Sleep Score:")
    test_sleep = {
        'total_sleep_duration': 7.2 * 3600,  # 7.2 hours in seconds
        'time_in_bed': 8 * 3600,
        'deep_sleep_duration': 1.3 * 3600,  # 18% of 7.2 hours
        'rem_sleep_duration': 1.6 * 3600,    # 22% of 7.2 hours
        'light_sleep_duration': 4.3 * 3600
    }
    
    test_baselines = {
        'hrv_baseline': 65,
        'rhr_baseline': 52,
        'typical_sleep_hours': 7.5
    }
    
    sleep_score, sleep_breakdown = calculate_sleep_score(test_sleep, test_baselines)
    print(f"  Sleep Score: {sleep_score}/100 ({sleep_breakdown['rating']}) {sleep_breakdown['emoji']}")
    print(f"    Duration: {sleep_breakdown['duration_hours']}h → {sleep_breakdown['duration_score']}/40")
    print(f"    Efficiency: {sleep_breakdown['efficiency_pct']}% → {sleep_breakdown['efficiency_score']}/30")
    print(f"    Deep: {sleep_breakdown['deep_pct']}% → {sleep_breakdown['deep_score']}/15")
    print(f"    REM: {sleep_breakdown['rem_pct']}% → {sleep_breakdown['rem_score']}/15")
    
    # Test readiness score
    print("\n2. Testing Readiness Score:")
    readiness_score, readiness_breakdown = calculate_readiness_score(
        sleep_score=sleep_score,
        hrv=68,
        rhr=53,
        recent_activities=[{}, {}],  # 2 recent workouts
        baselines=test_baselines
    )
    print(f"  Readiness Score: {readiness_score}/100 ({readiness_breakdown['rating']}) {readiness_breakdown['emoji']}")
    print(f"    HRV: {readiness_breakdown['hrv']} {readiness_breakdown['hrv_trend']} → {readiness_breakdown['hrv_score']}/35")
    print(f"    RHR: {readiness_breakdown['rhr']} {readiness_breakdown['rhr_trend']} → {readiness_breakdown['rhr_score']}/25")
    print(f"    Sleep: → {readiness_breakdown['sleep_component']}/25")
    print(f"    Load: {readiness_breakdown['recent_workouts']} workouts → {readiness_breakdown['load_score']}/15")
    
    # Test recovery status
    print("\n3. Testing Recovery Status:")
    status, recommendation, details = calculate_recovery_status(
        readiness_score=readiness_score,
        recent_readiness_scores=[72, 75, 76]  # Stable trend
    )
    print(f"  Status: {details['emoji']} {details['status']}")
    print(f"  Recommendation: {recommendation}")
    print(f"  Trend: {details['trend']} {details['trend_emoji']}")
    print(f"  Details: {details['detail_text']}")
