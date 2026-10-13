"""
Time Study Pattern Analysis Utilities
Detects patterns, trends, and outliers in time study data
"""

from typing import Dict, List, Tuple, Any
import statistics
from math import sqrt


def analyze_time_patterns(cycle_times: List[float]) -> Dict[str, Any]:
    """
    Analyze patterns in cycle time data
    
    Args:
        cycle_times: List of cycle times in milliseconds
        
    Returns:
        Dictionary with pattern analysis results
    """
    if not cycle_times or len(cycle_times) < 2:
        return {"error": "Insufficient data for pattern analysis"}

    sorted_times = sorted(cycle_times)
    n = len(sorted_times)
    
    # Basic statistics
    mean = statistics.mean(cycle_times)
    median = statistics.median(cycle_times)
    stdev = statistics.stdev(cycle_times) if n > 1 else 0
    q1 = sorted_times[n // 4]
    q3 = sorted_times[3 * n // 4]
    iqr = q3 - q1
    
    # Coefficient of variation (variability indicator)
    cv = (stdev / mean * 100) if mean > 0 else 0
    
    # Trend detection (simple linear regression)
    trend = _detect_trend(cycle_times)
    
    # Distribution classification
    distribution = _classify_distribution(cycle_times, mean, stdev)
    
    return {
        "mean": round(mean, 2),
        "median": round(median, 2),
        "std_dev": round(stdev, 2),
        "q1": round(q1, 2),
        "q3": round(q3, 2),
        "iqr": round(iqr, 2),
        "coeff_of_variation": round(cv, 2),
        "min": round(min(cycle_times), 2),
        "max": round(max(cycle_times), 2),
        "range": round(max(cycle_times) - min(cycle_times), 2),
        "trend": trend,
        "distribution": distribution,
        "sample_count": n,
    }


def detect_outliers(
    cycle_times: List[float],
    method: str = "iqr",
    threshold: float = 1.5,
) -> Dict[str, Any]:
    """
    Detect outliers in cycle time data
    
    Args:
        cycle_times: List of cycle times
        method: 'iqr' (InterQuartile Range) or 'zscore'
        threshold: Threshold for outlier detection
        
    Returns:
        Dictionary with outlier information
    """
    if not cycle_times:
        return {"outliers": [], "outlier_count": 0}

    outliers = []
    outlier_indices = []
    
    if method == "iqr":
        sorted_times = sorted(cycle_times)
        n = len(sorted_times)
        q1 = sorted_times[n // 4]
        q3 = sorted_times[3 * n // 4]
        iqr = q3 - q1
        
        lower_bound = q1 - threshold * iqr
        upper_bound = q3 + threshold * iqr
        
        for idx, time in enumerate(cycle_times):
            if time < lower_bound or time > upper_bound:
                outliers.append(time)
                outlier_indices.append(idx)
                
    elif method == "zscore":
        mean = statistics.mean(cycle_times)
        stdev = statistics.stdev(cycle_times) if len(cycle_times) > 1 else 0
        
        if stdev > 0:
            for idx, time in enumerate(cycle_times):
                z_score = abs((time - mean) / stdev)
                if z_score > threshold:
                    outliers.append(time)
                    outlier_indices.append(idx)
    
    return {
        "method": method,
        "outliers": sorted(outliers),
        "outlier_count": len(outliers),
        "outlier_indices": outlier_indices,
        "outlier_percent": round(len(outliers) / len(cycle_times) * 100, 2),
    }


def _detect_trend(values: List[float]) -> str:
    """Detect if data shows increasing, decreasing, or stable trend"""
    if len(values) < 3:
        return "insufficient_data"
    
    # Simple trend: compare first third with last third
    third = len(values) // 3
    first_third_mean = statistics.mean(values[:third])
    last_third_mean = statistics.mean(values[-third:])
    
    # Calculate percentage change
    if first_third_mean > 0:
        percent_change = (last_third_mean - first_third_mean) / first_third_mean * 100
        
        if percent_change > 5:
            return "increasing"
        elif percent_change < -5:
            return "decreasing"
    
    return "stable"


def _classify_distribution(values: List[float], mean: float, stdev: float) -> str:
    """Classify distribution type"""
    if stdev == 0:
        return "uniform"
    
    # Skewness approximation
    median = statistics.median(values)
    skewness = 3 * (mean - median) / stdev if stdev > 0 else 0
    
    if abs(skewness) < 0.5:
        return "normal"
    elif skewness > 0.5:
        return "right_skewed"
    else:
        return "left_skewed"


def calculate_standard_time(
    mean_cycle_time: float,
    confidence_level: float = 0.95,
    allowance_percent: float = 15.0,
) -> Dict[str, float]:
    """
    Calculate standard time based on mean cycle time and allowances
    
    Args:
        mean_cycle_time: Mean observed cycle time
        confidence_level: Confidence level (typically 0.90 or 0.95)
        allowance_percent: Personal + Fatigue + Delay allowance percentage
        
    Returns:
        Dictionary with standard time calculations
    """
    # Performance rating factor (typically 1.0 for 100% rating)
    rating_factor = 1.0
    
    # Normal time = mean * rating factor
    normal_time = mean_cycle_time * rating_factor
    
    # Standard time = normal time / (1 - allowance_percent/100)
    allowance_multiplier = 1 - (allowance_percent / 100)
    if allowance_multiplier > 0:
        standard_time = normal_time / allowance_multiplier
    else:
        standard_time = normal_time
    
    return {
        "mean_cycle_time": round(mean_cycle_time, 2),
        "normal_time": round(normal_time, 2),
        "allowance_percent": allowance_percent,
        "standard_time": round(standard_time, 2),
        "confidence_level": confidence_level,
    }
