"""
Specification Version Pattern Analysis Utilities
Tracks version changes and identifies drift trends
"""

from typing import Dict, List, Any
from datetime import datetime
from collections import defaultdict


def track_spec_changes(changes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze specification changes over time
    
    Args:
        changes: List of change dictionaries with timestamp, parameter_name, etc.
        
    Returns:
        Dictionary with change tracking analysis
    """
    if not changes:
        return {
            "total_changes": 0,
            "by_type": {},
            "by_parameter": {},
            "change_frequency": 0,
        }

    # Group changes by type
    by_type = defaultdict(int)
    by_parameter = defaultdict(list)
    
    for change in changes:
        change_type = change.get("change_type", "other")
        parameter = change.get("parameter_name", "unknown")
        
        by_type[change_type] += 1
        by_parameter[parameter].append(change)
    
    # Calculate change frequency (changes per day)
    if len(changes) >= 2:
        timestamps = [
            datetime.fromisoformat(c["timestamp"]) for c in changes
            if "timestamp" in c
        ]
        if timestamps:
            time_span = max(timestamps) - min(timestamps)
            days = time_span.total_seconds() / (24 * 3600) if time_span.total_seconds() > 0 else 1
            change_frequency = len(changes) / max(days, 1)
        else:
            change_frequency = 0
    else:
        change_frequency = 0
    
    return {
        "total_changes": len(changes),
        "by_type": dict(by_type),
        "by_parameter": {k: len(v) for k, v in by_parameter.items()},
        "most_changed_parameter": max(by_parameter.items(), key=lambda x: len(x[1]))[0] if by_parameter else None,
        "change_frequency_per_day": round(change_frequency, 2),
        "parameters_affected": len(by_parameter),
    }


def identify_drift_trends(drifts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Identify trends in specification drifts
    
    Args:
        drifts: List of drift dictionaries with severity, parameter_name, timestamp, etc.
        
    Returns:
        Dictionary with drift trend analysis
    """
    if not drifts:
        return {
            "total_drifts": 0,
            "severity_distribution": {},
            "by_parameter": {},
            "trend": "stable",
            "critical_rate": 0,
        }

    # Group drifts by severity
    severity_dist = defaultdict(int)
    by_parameter = defaultdict(lambda: {"count": 0, "critical": 0})
    
    for drift in drifts:
        severity = drift.get("severity", "low")
        parameter = drift.get("parameter_name", "unknown")
        
        severity_dist[severity] += 1
        by_parameter[parameter]["count"] += 1
        if severity == "critical":
            by_parameter[parameter]["critical"] += 1
    
    # Identify critical parameters (high critical drift rate)
    critical_params = [
        param for param, data in by_parameter.items()
        if data["critical"] / max(data["count"], 1) > 0.5
    ]
    
    # Calculate critical drift rate
    critical_count = severity_dist.get("critical", 0)
    critical_rate = critical_count / len(drifts) * 100 if drifts else 0
    
    # Determine overall trend
    trend = _determine_drift_trend(drifts, critical_rate)
    
    return {
        "total_drifts": len(drifts),
        "severity_distribution": dict(severity_dist),
        "by_parameter": dict(by_parameter),
        "critical_parameters": critical_params,
        "critical_rate_percent": round(critical_rate, 2),
        "trend": trend,
        "parameters_with_drift": len(by_parameter),
    }


def _determine_drift_trend(drifts: List[Dict[str, Any]], critical_rate: float) -> str:
    """Determine if drift situation is improving or worsening"""
    if critical_rate > 30:
        return "critical"
    elif critical_rate > 15:
        return "worsening"
    elif critical_rate > 5:
        return "concerning"
    else:
        return "stable"


def calculate_drift_risk_score(drift_data: Dict[str, Any]) -> float:
    """
    Calculate an overall risk score (0-100) for specification drift
    
    Args:
        drift_data: Output from identify_drift_trends()
        
    Returns:
        Risk score from 0 (safe) to 100 (critical)
    """
    score = 0.0
    
    # Factor: number of critical drifts
    severity_dist = drift_data.get("severity_distribution", {})
    critical_count = severity_dist.get("critical", 0)
    score += min(critical_count * 10, 30)
    
    # Factor: critical rate
    critical_rate = drift_data.get("critical_rate_percent", 0)
    score += min(critical_rate * 0.5, 30)
    
    # Factor: trend
    trend = drift_data.get("trend", "stable")
    trend_scores = {
        "critical": 25,
        "worsening": 15,
        "concerning": 8,
        "stable": 0,
    }
    score += trend_scores.get(trend, 0)
    
    # Factor: number of critical parameters
    critical_params = drift_data.get("critical_parameters", [])
    score += min(len(critical_params) * 5, 15)
    
    return min(score, 100.0)


def get_drift_recommendations(drift_data: Dict[str, Any]) -> List[str]:
    """
    Generate recommendations based on drift analysis
    
    Args:
        drift_data: Output from identify_drift_trends()
        
    Returns:
        List of actionable recommendations
    """
    recommendations = []
    
    # Check severity distribution
    severity_dist = drift_data.get("severity_distribution", {})
    if severity_dist.get("critical", 0) > 0:
        recommendations.append("🔴 URGENT: Address critical drifts immediately")
    
    if severity_dist.get("high", 0) > 3:
        recommendations.append("⚠️  Multiple high-severity drifts detected - escalate to engineering")
    
    # Check trend
    trend = drift_data.get("trend", "stable")
    if trend == "worsening":
        recommendations.append("📈 Drift situation is worsening - investigate root cause")
    elif trend == "critical":
        recommendations.append("🚨 CRITICAL: Implement immediate corrective actions")
    
    # Check critical parameters
    critical_params = drift_data.get("critical_parameters", [])
    if critical_params:
        params_str = ", ".join(critical_params[:3])
        recommendations.append(f"🔧 Focus on critical parameters: {params_str}")
    
    # Check parameter count
    param_count = drift_data.get("parameters_with_drift", 0)
    if param_count > 10:
        recommendations.append("📊 Many parameters affected - consider process-wide review")
    
    # Default recommendation
    if not recommendations:
        recommendations.append("✅ Specification drifts are within acceptable limits")
    
    return recommendations


def compare_spec_versions(
    version1_data: Dict[str, Any],
    version2_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Compare two specification versions
    
    Args:
        version1_data: First version data (typically older)
        version2_data: Second version data (typically newer)
        
    Returns:
        Dictionary with comparison results
    """
    changes = {
        "added_parameters": [],
        "removed_parameters": [],
        "modified_parameters": [],
        "unchanged_parameters": [],
    }
    
    params1 = set(version1_data.get("parameters", {}).keys())
    params2 = set(version2_data.get("parameters", {}).keys())
    
    # New parameters
    changes["added_parameters"] = list(params2 - params1)
    
    # Removed parameters
    changes["removed_parameters"] = list(params1 - params2)
    
    # Check modified parameters
    common_params = params1 & params2
    for param in common_params:
        val1 = version1_data["parameters"][param]
        val2 = version2_data["parameters"][param]
        if val1 != val2:
            changes["modified_parameters"].append({
                "parameter": param,
                "old_value": val1,
                "new_value": val2,
            })
        else:
            changes["unchanged_parameters"].append(param)
    
    # Calculate impact
    total_params = len(common_params) + len(changes["added_parameters"])
    change_percent = (
        (len(changes["added_parameters"]) + len(changes["removed_parameters"]) + 
         len(changes["modified_parameters"])) / total_params * 100
        if total_params > 0 else 0
    )
    
    return {
        "version1_id": version1_data.get("version_id"),
        "version2_id": version2_data.get("version_id"),
        "changes": changes,
        "change_percent": round(change_percent, 2),
        "impact_level": _determine_impact_level(changes, change_percent),
    }


def _determine_impact_level(changes: Dict[str, Any], change_percent: float) -> str:
    """Determine impact level of changes"""
    if len(changes["removed_parameters"]) > 0 or len(changes["added_parameters"]) > 2:
        return "high"
    elif change_percent > 20:
        return "medium"
    else:
        return "low"
