"""
Baseline Calculator
Calculates personalized HRV and RHR baselines from historical Oura data.
Updates automatically as more data is collected.
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import statistics
import config
from cache_manager import cache


class BaselineCalculator:
    """Calculates and manages personalized baselines."""
    
    def __init__(self):
        self.baselines_file = config.CACHE_DIR / 'baselines.json'
    
    def calculate_from_oura_data(self, oura_data: Dict, 
                                 min_days: int = 7) -> Optional[Dict]:
        """
        Calculate baselines from Oura data.
        
        Args:
            oura_data: Oura data dictionary
            min_days: Minimum number of days needed for reliable baseline
        
        Returns:
            Dictionary with baseline values or None if insufficient data
        """
        if not oura_data:
            return None
        
        # Extract HRV and RHR values
        hrv_values = []
        rhr_values = []
        
        # Try daily readiness data first (has HRV)
        readiness_data = oura_data.get('daily_readiness', [])
        for day in readiness_data:
            # HRV might be in different fields depending on API version
            hrv = day.get('heart_rate_variability') or day.get('hrv_balance')
            if hrv and isinstance(hrv, (int, float)) and hrv > 0:
                hrv_values.append(hrv)
        
        # Try sleep data for RHR
        sleep_data = oura_data.get('daily_sleep', []) or oura_data.get('sleep', [])
        for day in sleep_data:
            # RHR might be in different fields
            rhr = day.get('lowest_heart_rate') or day.get('heart_rate', {}).get('resting')
            if rhr and isinstance(rhr, (int, float)) and rhr > 0:
                rhr_values.append(rhr)
        
        # Check if we have enough data
        if len(hrv_values) < min_days:
            print(f"⚠️  Only {len(hrv_values)} days of HRV data (need {min_days})")
            print(f"   Using default HRV baseline: {config.HRV_BASELINE}")
            hrv_baseline = config.HRV_BASELINE
        else:
            # Use median to be resistant to outliers
            hrv_baseline = statistics.median(hrv_values)
            print(f"✓ Calculated HRV baseline: {hrv_baseline:.1f} (from {len(hrv_values)} days)")
        
        if len(rhr_values) < min_days:
            print(f"⚠️  Only {len(rhr_values)} days of RHR data (need {min_days})")
            print(f"   Using default RHR baseline: {config.RHR_BASELINE}")
            rhr_baseline = config.RHR_BASELINE
        else:
            rhr_baseline = statistics.median(rhr_values)
            print(f"✓ Calculated RHR baseline: {rhr_baseline:.1f} (from {len(rhr_values)} days)")
        
        # Calculate typical sleep duration if available
        sleep_durations = []
        for day in sleep_data:
            duration = day.get('total_sleep_duration')
            if duration:
                # Convert to hours
                sleep_durations.append(duration / 3600)
        
        if sleep_durations:
            typical_sleep = statistics.median(sleep_durations)
        else:
            typical_sleep = 7.5  # Default
        
        baselines = {
            'hrv_baseline': round(hrv_baseline, 1),
            'rhr_baseline': round(rhr_baseline, 1),
            'typical_sleep_hours': round(typical_sleep, 1),
            'hrv_samples': len(hrv_values),
            'rhr_samples': len(rhr_values),
            'calculated_at': datetime.now().isoformat(),
            'data_source': oura_data.get('source', 'api')
        }
        
        return baselines
    
    def save_baselines(self, baselines: Dict) -> bool:
        """Save baselines to file."""
        try:
            with open(self.baselines_file, 'w') as f:
                json.dump(baselines, f, indent=2)
            print(f"✓ Baselines saved to {self.baselines_file}")
            return True
        except Exception as e:
            print(f"❌ Failed to save baselines: {e}")
            return False
    
    def load_baselines(self) -> Optional[Dict]:
        """Load baselines from file."""
        try:
            if not self.baselines_file.exists():
                return None
            
            with open(self.baselines_file, 'r') as f:
                baselines = json.load(f)
            
            # Check age
            calculated_at = datetime.fromisoformat(baselines['calculated_at'])
            age_days = (datetime.now() - calculated_at).days
            
            print(f"✓ Loaded baselines (age: {age_days} days)")
            return baselines
            
        except Exception as e:
            print(f"❌ Failed to load baselines: {e}")
            return None
    
    def get_baselines(self, oura_data: Optional[Dict] = None, 
                     force_recalculate: bool = False,
                     max_age_days: int = 7) -> Dict:
        """
        Get baselines, calculating if needed.
        
        Args:
            oura_data: Oura data to calculate from (if recalculating)
            force_recalculate: If True, recalculate even if cached
            max_age_days: Recalculate if baselines older than this
        
        Returns:
            Dictionary with baseline values
        """
        # Load existing baselines
        baselines = self.load_baselines()
        
        # Check if we should recalculate
        should_recalculate = force_recalculate
        
        if baselines:
            calculated_at = datetime.fromisoformat(baselines['calculated_at'])
            age_days = (datetime.now() - calculated_at).days
            
            if age_days > max_age_days:
                print(f"ℹ️  Baselines are {age_days} days old, recalculating...")
                should_recalculate = True
        else:
            should_recalculate = True
        
        # Recalculate if needed and we have data
        if should_recalculate and oura_data:
            new_baselines = self.calculate_from_oura_data(oura_data)
            if new_baselines:
                self.save_baselines(new_baselines)
                return new_baselines
        
        # Return existing baselines or defaults
        if baselines:
            return baselines
        else:
            print("⚠️  No baselines calculated yet, using defaults from config")
            return {
                'hrv_baseline': config.HRV_BASELINE,
                'rhr_baseline': config.RHR_BASELINE,
                'typical_sleep_hours': 7.5,
                'hrv_samples': 0,
                'rhr_samples': 0,
                'calculated_at': datetime.now().isoformat(),
                'data_source': 'default'
            }
    
    def get_current_deviation(self, current_hrv: float, current_rhr: float,
                             baselines: Dict) -> Tuple[float, float]:
        """
        Calculate current deviation from baselines.
        
        Args:
            current_hrv: Current HRV value
            current_rhr: Current RHR value
            baselines: Baselines dictionary
        
        Returns:
            Tuple of (hrv_deviation_pct, rhr_deviation_bpm)
        """
        hrv_baseline = baselines['hrv_baseline']
        rhr_baseline = baselines['rhr_baseline']
        
        # HRV deviation as percentage
        if hrv_baseline > 0:
            hrv_dev_pct = ((current_hrv - hrv_baseline) / hrv_baseline) * 100
        else:
            hrv_dev_pct = 0
        
        # RHR deviation in bpm
        rhr_dev_bpm = current_rhr - rhr_baseline
        
        return round(hrv_dev_pct, 1), round(rhr_dev_bpm, 1)


# Global instance
baseline_calculator = BaselineCalculator()


if __name__ == '__main__':
    # Test baseline calculator
    print("Testing Baseline Calculator...")
    print("=" * 60)
    
    # Try to load existing baselines
    baselines = baseline_calculator.load_baselines()
    
    if baselines:
        print("\n✓ Existing baselines found:")
        print(f"  HRV: {baselines['hrv_baseline']} ({baselines['hrv_samples']} samples)")
        print(f"  RHR: {baselines['rhr_baseline']} ({baselines['rhr_samples']} samples)")
        print(f"  Typical sleep: {baselines['typical_sleep_hours']} hours")
        print(f"  Calculated: {baselines['calculated_at']}")
        print(f"  Source: {baselines['data_source']}")
        
        # Test deviation calculation
        print("\n  Testing deviation calculation:")
        test_hrv = 68
        test_rhr = 55
        hrv_dev, rhr_dev = baseline_calculator.get_current_deviation(
            test_hrv, test_rhr, baselines
        )
        print(f"    Current HRV {test_hrv} → {hrv_dev:+.1f}% from baseline")
        print(f"    Current RHR {test_rhr} → {rhr_dev:+.1f} bpm from baseline")
    else:
        print("\n⚠️  No baselines calculated yet")
        print("   Baselines will be calculated when dashboard runs with Oura data")
        
        # Show what defaults would be used
        default_baselines = baseline_calculator.get_baselines()
        print(f"\n  Using defaults:")
        print(f"    HRV: {default_baselines['hrv_baseline']}")
        print(f"    RHR: {default_baselines['rhr_baseline']}")
        print(f"    Sleep: {default_baselines['typical_sleep_hours']} hours")
