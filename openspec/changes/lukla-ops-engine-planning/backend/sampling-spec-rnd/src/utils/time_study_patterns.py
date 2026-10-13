"""
@name: Time Study Patterns
@description: Common patterns untuk Time Study recording, calculation, dan analysis
"""

from typing import List, Dict, Optional
from statistics import mean, stdev
from datetime import datetime


# ============================================
# PATTERN 1: Time Study Data Model
# ============================================
def create_time_study_model() -> Dict:
    """
    Standard structure untuk time study record
    """
    return {
        'id': 'ts-20261013-001',
        'spec_id': 'spec-001',
        'product_id': 'prod-001',
        'operator': 'operator-id-123',
        'date': '2026-10-13',
        'phases': [
            {
                'id': 'phase-1',
                'name': 'Potong Kain',
                'duration': 120,  # seconds
                'start_time': '10:00:00',
                'end_time': '10:02:00',
                'notes': 'Sempurna, tidak ada reject',
            },
            {
                'id': 'phase-2',
                'name': 'Jahit',
                'duration': 180,
                'start_time': '10:02:00',
                'end_time': '10:05:00',
                'notes': 'Jahitan rapi, sesuai standar',
            },
        ],
        'total_time': 300,  # seconds
        'quality_score': 95,  # QC rating
        'status': 'completed',
        'created_at': '2026-10-13T10:05:00Z',
        'updated_at': '2026-10-13T10:05:00Z',
    }


# ============================================
# PATTERN 2: Calculate Average Time Per Phase
# ============================================
def calculate_average_phase_time(
    time_studies: List[Dict],
    phase_name: str
) -> Optional[Dict]:
    """
    Hitung rata-rata waktu per fase dari multiple time studies
    
    Args:
        time_studies (List[Dict]): Array of time study records
        phase_name (str): Nama fase yang dicari
    
    Returns:
        Dict: Average time dan statistics
    """
    phase_records = []
    for ts in time_studies:
        for phase in ts.get('phases', []):
            if phase['name'] == phase_name:
                phase_records.append(phase)
    
    if not phase_records:
        return {
            'average': 0,
            'count': 0,
            'min': 0,
            'max': 0,
            'std_dev': 0,
        }
    
    durations = [p['duration'] for p in phase_records]
    avg = mean(durations)
    min_duration = min(durations)
    max_duration = max(durations)
    
    # Standard deviation
    std_dev = stdev(durations) if len(durations) > 1 else 0
    
    return {
        'phase_name': phase_name,
        'average': int(avg),
        'count': len(phase_records),
        'min': min_duration,
        'max': max_duration,
        'std_dev': round(std_dev, 2),
    }


# ============================================
# PATTERN 3: Quality Score Based on Time Variance
# ============================================
def calculate_quality_score(
    actual_time: int,
    expected_time: int,
    tolerance: float = 10.0
) -> int:
    """
    Hitung quality score berdasarkan variance dari expected time
    
    Args:
        actual_time (int): Waktu aktual (seconds)
        expected_time (int): Expected time (seconds)
        tolerance (float): Tolerance percentage (default 10%)
    
    Returns:
        int: Quality score 0-100
    """
    if expected_time == 0:
        return 0
    
    deviation = abs(actual_time - expected_time) / expected_time
    tolerance_decimal = tolerance / 100
    
    if deviation <= tolerance_decimal:
        return 100
    
    if deviation > tolerance_decimal * 2:
        return 50
    
    score = 100 - (deviation / (tolerance_decimal * 2)) * 50
    return max(0, min(100, int(score)))


# ============================================
# PATTERN 4: Version Comparison
# ============================================
def compare_spec_versions(
    version1_time_studies: List[Dict],
    version2_time_studies: List[Dict],
    phase_name: str = 'Jahit'
) -> Dict:
    """
    Compare time study results antar versi spesifikasi
    
    Args:
        version1_time_studies (List[Dict]): Time studies untuk version 1
        version2_time_studies (List[Dict]): Time studies untuk version 2
        phase_name (str): Phase mana yang dibandingkan
    
    Returns:
        Dict: Comparison result
    """
    avg1_data = calculate_average_phase_time(version1_time_studies, phase_name)
    avg2_data = calculate_average_phase_time(version2_time_studies, phase_name)
    
    avg1 = avg1_data['average'] if avg1_data else 0
    avg2 = avg2_data['average'] if avg2_data else 0
    
    if avg1 == 0:
        improvement = 0
    else:
        improvement = ((avg1 - avg2) / avg1) * 100
    
    return {
        'version1_avg_time': avg1,
        'version2_avg_time': avg2,
        'improvement_percentage': round(improvement, 2),
        'is_faster': improvement > 0,
        'phase_name': phase_name,
    }


# ============================================
# PATTERN 5: Detect R&D Drift
# ============================================
def detect_rnd_drift(
    historical_time_studies: List[Dict],
    current_time_studies: List[Dict],
    threshold: float = 15.0
) -> Dict:
    """
    Deteksi jika ada perubahan signifikan dalam time study dari versi sebelumnya
    
    Args:
        historical_time_studies (List[Dict]): Historical time studies
        current_time_studies (List[Dict]): Current time studies
        threshold (float): Threshold percentage untuk flag (default 15%)
    
    Returns:
        Dict: Drift analysis
    """
    drift_analysis = {}
    
    # Cek semua phases
    all_phases = set()
    for ts in historical_time_studies + current_time_studies:
        for phase in ts.get('phases', []):
            all_phases.add(phase['name'])
    
    for phase_name in all_phases:
        hist_data = calculate_average_phase_time(historical_time_studies, phase_name)
        curr_data = calculate_average_phase_time(current_time_studies, phase_name)
        
        hist_avg = hist_data['average'] if hist_data else 0
        curr_avg = curr_data['average'] if curr_data else 0
        
        if hist_avg > 0:
            drift_percent = abs(hist_avg - curr_avg) / hist_avg * 100
            drift_analysis[phase_name] = {
                'historical_average': hist_avg,
                'current_average': curr_avg,
                'drift_percent': round(drift_percent, 2),
                'has_drift': drift_percent > threshold,
                'direction': 'slower' if curr_avg > hist_avg else 'faster',
            }
    
    return {
        'drift_detected': any(d['has_drift'] for d in drift_analysis.values()),
        'analysis': drift_analysis,
        'threshold': threshold,
    }


# ============================================
# PATTERN 6: Time Study Validation
# ============================================
def validate_time_study(time_study: Dict) -> Dict:
    """
    Validate time study data sebelum save
    
    Args:
        time_study (Dict): Time study data
    
    Returns:
        Dict: Validation result
    """
    errors = []
    
    if not time_study.get('spec_id'):
        errors.append('spec_id is required')
    
    phases = time_study.get('phases', [])
    if not phases or len(phases) == 0:
        errors.append('At least one phase is required')
    
    # Check phase validity
    for idx, phase in enumerate(phases):
        if not phase.get('name'):
            errors.append(f'Phase {idx}: name is required')
        if phase.get('duration', 0) <= 0:
            errors.append(f'Phase {idx}: duration must be > 0')
    
    return {
        'is_valid': len(errors) == 0,
        'errors': errors,
    }


# ============================================
# PATTERN 7: Generate Time Study Report
# ============================================
def generate_time_study_report(
    time_studies: List[Dict],
    spec_version: str = "1.0"
) -> Dict:
    """
    Generate time study report untuk export
    
    Args:
        time_studies (List[Dict]): List of time studies
        spec_version (str): Spec version
    
    Returns:
        Dict: Report data
    """
    if not time_studies:
        return {
            'report_date': datetime.now().isoformat(),
            'spec_version': spec_version,
            'summary': {
                'total_recordings': 0,
                'total_phases': 0,
                'average_total_time': 0,
            },
            'phase_analysis': [],
            'raw_data': [],
        }
    
    total_recordings = len(time_studies)
    total_phases = sum(len(ts.get('phases', [])) for ts in time_studies)
    average_total_time = sum(ts.get('total_time', 0) for ts in time_studies) / total_recordings
    
    # Kumpulkan semua phase names
    all_phases = set()
    for ts in time_studies:
        for phase in ts.get('phases', []):
            all_phases.add(phase['name'])
    
    # Hitung analysis per phase
    phase_analysis = []
    for phase_name in sorted(all_phases):
        analysis = calculate_average_phase_time(time_studies, phase_name)
        if analysis:
            phase_analysis.append(analysis)
    
    return {
        'report_date': datetime.now().isoformat(),
        'spec_version': spec_version,
        'summary': {
            'total_recordings': total_recordings,
            'total_phases': total_phases,
            'average_total_time': int(average_total_time),
        },
        'phase_analysis': phase_analysis,
        'raw_data': time_studies,
    }


# ============================================
# PATTERN 8: Export to CSV
# ============================================
def export_time_study_to_csv(
    time_studies: List[Dict],
    spec_version: str = "1.0"
) -> str:
    """
    Export time study ke format CSV
    
    Args:
        time_studies (List[Dict]): List of time studies
        spec_version (str): Spec version
    
    Returns:
        str: CSV content
    """
    lines = [
        f"Time Study Report - Spec Version {spec_version}",
        f"Generated: {datetime.now().isoformat()}",
        "",
        "Spec ID,Product ID,Operator,Date,Phase Name,Duration (s),Status",
    ]
    
    for ts in time_studies:
        for phase in ts.get('phases', []):
            line = f"{ts.get('spec_id')},{ts.get('product_id')},{ts.get('operator')},{ts.get('date')},{phase.get('name')},{phase.get('duration')},{ts.get('status')}"
            lines.append(line)
    
    return "\n".join(lines)


# ============================================
# EXPORT FUNCTIONS
# ============================================
if __name__ == "__main__":
    # Example usage
    model = create_time_study_model()
    print("Model created:", model)
