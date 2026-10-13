"""
@name: Spec Version Patterns
@description: Common patterns untuk spec version management, tracking, dan R&D drift detection
"""

from typing import List, Dict, Optional, Set
from datetime import datetime
import json


# ============================================
# PATTERN 1: Spec Version Data Model
# ============================================
def create_spec_version_model() -> Dict:
    """
    Standard structure untuk spec version
    """
    return {
        'id': 'spec-prod-001-v1.0',
        'product_id': 'prod-001',
        'version_number': '1.0',
        'description': 'Initial spec dengan padding 5mm dan jahitan 2mm',
        'specification': {
            'material': 'Cotton 100%',
            'size': 'M',
            'padding_mm': 5,
            'stitch_size_mm': 2,
            'color': 'White',
            'quality_standard': 'ISO 9001',
        },
        'created_by': 'rd-team',
        'created_at': '2026-10-13T10:00:00Z',
        'status': 'approved',
        'changes': 'Initial version from R&D',
        'change_history': [
            {
                'type': 'created',
                'timestamp': '2026-10-13T10:00:00Z',
                'actor': 'rd-team',
                'note': 'Initial creation',
            }
        ],
    }


# ============================================
# PATTERN 2: Track Spec Changes
# ============================================
def track_spec_change(
    version: Dict,
    change_type: str,
    changed_fields: Dict,
    actor: str = 'system',
    reason: str = ''
) -> Dict:
    """
    Track perubahan pada spec version
    
    Args:
        version (Dict): Current version
        change_type (str): Tipe perubahan (e.g., 'material_change', 'size_change')
        changed_fields (Dict): Field yang berubah
        actor (str): Siapa yang bikin perubahan
        reason (str): Alasan perubahan
    
    Returns:
        Dict: Updated version
    """
    change_record = {
        'type': change_type,
        'timestamp': datetime.now().isoformat(),
        'actor': actor,
        'changed_fields': changed_fields,
        'reason': reason,
    }
    
    version['change_history'].append(change_record)
    version['updated_at'] = datetime.now().isoformat()
    
    return version


# ============================================
# PATTERN 3: Spec Compliance Check
# ============================================
def check_spec_compliance(
    current_spec: Dict,
    approved_spec: Dict,
    tolerance: float = 5.0
) -> Dict:
    """
    Check apakah current spec masih compliant dengan approved spec
    
    Args:
        current_spec (Dict): Current spec
        approved_spec (Dict): Approved spec (baseline)
        tolerance (float): Tolerance percentage untuk numeric values
    
    Returns:
        Dict: Compliance check result
    """
    compliance_issues = []
    
    # Check all keys in approved spec
    for key, approved_value in approved_spec.items():
        if key not in current_spec:
            compliance_issues.append({
                'field': key,
                'issue': 'missing',
                'approved_value': approved_value,
            })
        else:
            current_value = current_spec[key]
            
            # Numeric comparison dengan tolerance
            if isinstance(approved_value, (int, float)) and isinstance(current_value, (int, float)):
                deviation = abs(current_value - approved_value) / approved_value * 100
                if deviation > tolerance:
                    compliance_issues.append({
                        'field': key,
                        'issue': 'out_of_tolerance',
                        'approved_value': approved_value,
                        'current_value': current_value,
                        'deviation_percent': round(deviation, 2),
                    })
            
            # String comparison
            elif isinstance(approved_value, str) and isinstance(current_value, str):
                if approved_value != current_value:
                    compliance_issues.append({
                        'field': key,
                        'issue': 'mismatch',
                        'approved_value': approved_value,
                        'current_value': current_value,
                    })
    
    return {
        'is_compliant': len(compliance_issues) == 0,
        'issues': compliance_issues,
        'issue_count': len(compliance_issues),
    }


# ============================================
# PATTERN 4: Version Lineage Tracking
# ============================================
def trace_version_lineage(
    versions: List[Dict],
    target_version_id: str
) -> List[Dict]:
    """
    Trace lineage dari target version sampai initial version
    
    Args:
        versions (List[Dict]): All versions
        target_version_id (str): Target version ID
    
    Returns:
        List[Dict]: Lineage trace
    """
    lineage = []
    version_map = {v['id']: v for v in versions}
    
    current_id = target_version_id
    while current_id and current_id in version_map:
        version = version_map[current_id]
        lineage.append({
            'id': version['id'],
            'version_number': version['version_number'],
            'created_at': version.get('created_at'),
            'created_by': version.get('created_by'),
        })
        
        # Find parent version
        current_id = None
        for change in version.get('change_history', []):
            if change.get('type') == 'created' and change.get('parent_version'):
                current_id = change['parent_version']
                break
    
    return list(reversed(lineage))


# ============================================
# PATTERN 5: R&D Drift Detection
# ============================================
def detect_spec_drift(
    reference_spec: Dict,
    current_spec: Dict,
    critical_fields: Set[str] = None
) -> Dict:
    """
    Deteksi jika ada "drift" (perubahan tidak terdokumentasi) dalam spec
    
    Args:
        reference_spec (Dict): Reference/baseline spec
        current_spec (Dict): Current spec to check
        critical_fields (Set): Fields yang critical (tidak boleh berubah)
    
    Returns:
        Dict: Drift analysis
    """
    if critical_fields is None:
        critical_fields = {'material', 'size', 'quality_standard'}
    
    drifts = []
    warnings = []
    
    for field in critical_fields:
        ref_value = reference_spec.get(field)
        curr_value = current_spec.get(field)
        
        if ref_value != curr_value:
            drifts.append({
                'field': field,
                'severity': 'critical',
                'reference_value': ref_value,
                'current_value': curr_value,
                'message': f"Critical field '{field}' has drifted",
            })
    
    # Check untuk non-critical fields yang berubah
    all_fields = set(reference_spec.keys()) | set(current_spec.keys())
    for field in all_fields - critical_fields:
        if reference_spec.get(field) != current_spec.get(field):
            warnings.append({
                'field': field,
                'severity': 'warning',
                'reference_value': reference_spec.get(field),
                'current_value': current_spec.get(field),
            })
    
    return {
        'has_critical_drift': len(drifts) > 0,
        'drift_count': len(drifts),
        'warning_count': len(warnings),
        'drifts': drifts,
        'warnings': warnings,
    }


# ============================================
# PATTERN 6: Version Diff
# ============================================
def diff_versions(version1: Dict, version2: Dict) -> Dict:
    """
    Generate diff antara dua versions
    
    Args:
        version1 (Dict): First version
        version2 (Dict): Second version
    
    Returns:
        Dict: Diff result
    """
    spec1 = version1.get('specification', {})
    spec2 = version2.get('specification', {})
    
    added = {}
    removed = {}
    modified = {}
    
    # Check removed dan modified
    for key, value in spec1.items():
        if key not in spec2:
            removed[key] = value
        elif spec2[key] != value:
            modified[key] = {
                'from': value,
                'to': spec2[key],
            }
    
    # Check added
    for key, value in spec2.items():
        if key not in spec1:
            added[key] = value
    
    return {
        'version1_number': version1.get('version_number'),
        'version2_number': version2.get('version_number'),
        'added_fields': added,
        'removed_fields': removed,
        'modified_fields': modified,
        'total_changes': len(added) + len(removed) + len(modified),
    }


# ============================================
# PATTERN 7: Generate Change Report
# ============================================
def generate_change_report(version: Dict) -> str:
    """
    Generate human-readable change report
    
    Args:
        version (Dict): Version object
    
    Returns:
        str: Report text
    """
    lines = [
        f"=== Spec Version Change Report ===",
        f"Version: {version.get('version_number')}",
        f"Product: {version.get('product_id')}",
        f"Created: {version.get('created_at')}",
        f"Created By: {version.get('created_by')}",
        f"Status: {version.get('status')}",
        f"",
        f"Description: {version.get('description')}",
        f"",
        f"Changes: {version.get('changes')}",
        f"",
        f"=== Change History ===",
    ]
    
    for idx, change in enumerate(version.get('change_history', []), 1):
        lines.append(f"\n{idx}. {change.get('type')} - {change.get('timestamp')}")
        lines.append(f"   By: {change.get('actor')}")
        if change.get('note'):
            lines.append(f"   Note: {change.get('note')}")
        if change.get('reason'):
            lines.append(f"   Reason: {change.get('reason')}")
    
    lines.append(f"\n=== Current Specification ===")
    spec = version.get('specification', {})
    for key, value in spec.items():
        lines.append(f"{key}: {value}")
    
    return "\n".join(lines)


# ============================================
# PATTERN 8: Export Version History
# ============================================
def export_version_history_to_csv(versions: List[Dict]) -> str:
    """
    Export version history ke CSV
    
    Args:
        versions (List[Dict]): List of versions
    
    Returns:
        str: CSV content
    """
    lines = [
        "Version Number,Product ID,Status,Created At,Created By,Description",
    ]
    
    for version in sorted(versions, key=lambda v: v.get('created_at', '')):
        line = f"\"{version.get('version_number')}\",\"{version.get('product_id')}\",\"{version.get('status')}\",\"{version.get('created_at')}\",\"{version.get('created_by')}\",\"{version.get('description')}\""
        lines.append(line)
    
    return "\n".join(lines)


# ============================================
# PATTERN 9: Spec Approval Workflow
# ============================================
def approve_spec_version(
    version: Dict,
    approver: str,
    approval_notes: str = ""
) -> Dict:
    """
    Approve spec version
    
    Args:
        version (Dict): Version to approve
        approver (str): Approver name/ID
        approval_notes (str): Approval notes
    
    Returns:
        Dict: Updated version
    """
    if version.get('status') != 'draft':
        raise ValueError(f"Only draft versions can be approved, current status: {version.get('status')}")
    
    version['status'] = 'approved'
    version['approved_at'] = datetime.now().isoformat()
    version['approved_by'] = approver
    
    version['change_history'].append({
        'type': 'approved',
        'timestamp': datetime.now().isoformat(),
        'actor': approver,
        'notes': approval_notes,
    })
    
    return version


# ============================================
# EXPORT FUNCTIONS
# ============================================
if __name__ == "__main__":
    # Example usage
    model = create_spec_version_model()
    print("Model created:", json.dumps(model, indent=2))
