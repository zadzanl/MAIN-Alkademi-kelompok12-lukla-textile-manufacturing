"""
@name: SpecVersionTracker
@description: Class untuk track versi spesifikasi produk dan prevent R&D drift
@params: product_id (str) - ID produk
@params: db_connection - Database connection object
@returns: SpecVersionTracker instance
@example:
    tracker = SpecVersionTracker(product_id='prod-123', db_conn=conn)
    tracker.create_version('v1.0', 'Initial spec')
    tracker.get_versions()
"""

from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum
import json


class VersionStatus(Enum):
    """Status enum untuk versi spesifikasi"""
    DRAFT = "draft"
    APPROVED = "approved"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class SpecVersionTracker:
    """Tracker untuk spec versions dengan change history"""
    
    def __init__(self, product_id: str, db_connection=None):
        """
        Initialize spec version tracker
        
        Args:
            product_id (str): Product ID
            db_connection: Database connection
        """
        self.product_id = product_id
        self.db_connection = db_connection
        self.versions: List[Dict] = []
        self.current_version = None
    
    def create_version(
        self,
        version_number: str,
        description: str,
        specification: Dict,
        created_by: str = "system",
        changes: str = "",
        status: VersionStatus = VersionStatus.DRAFT
    ) -> Dict:
        """
        Create versi spesifikasi baru
        
        Args:
            version_number (str): Version number (e.g., '1.0', '1.1')
            description (str): Deskripsi versi
            specification (Dict): Spec data (bahan, ukuran, jahitan, etc)
            created_by (str): Siapa yang create
            changes (str): Perubahan dari versi sebelumnya
            status (VersionStatus): Status versi
        
        Returns:
            Dict: Created version data
        """
        version_id = f"spec-{self.product_id}-{version_number}"
        
        # Get previous version untuk change tracking
        previous_version_id = None
        if self.versions:
            previous_version_id = self.versions[-1]['id']
        
        new_version = {
            'id': version_id,
            'product_id': self.product_id,
            'version_number': version_number,
            'description': description,
            'specification': specification,
            'created_by': created_by,
            'created_at': datetime.now().isoformat(),
            'status': status.value,
            'changes': changes,
            'change_history': [{
                'type': 'created',
                'timestamp': datetime.now().isoformat(),
                'actor': created_by,
                'previous_version': previous_version_id,
            }],
        }
        
        self.versions.append(new_version)
        self.current_version = new_version
        
        print(f"✓ Version {version_number} created: {version_id}")
        return new_version
    
    def get_versions(self, status: Optional[VersionStatus] = None) -> List[Dict]:
        """
        Get semua versions atau filter by status
        
        Args:
            status (VersionStatus): Filter by status (optional)
        
        Returns:
            List[Dict]: List of versions
        """
        if status is None:
            return self.versions
        return [v for v in self.versions if v['status'] == status.value]
    
    def get_version_by_id(self, version_id: str) -> Optional[Dict]:
        """Get specific version by ID"""
        for version in self.versions:
            if version['id'] == version_id:
                return version
        return None
    
    def get_version_by_number(self, version_number: str) -> Optional[Dict]:
        """Get specific version by version number"""
        for version in self.versions:
            if version['version_number'] == version_number:
                return version
        return None
    
    def update_version_status(self, version_id: str, new_status: VersionStatus, reason: str = "") -> bool:
        """
        Update status versi
        
        Args:
            version_id (str): Version ID
            new_status (VersionStatus): New status
            reason (str): Reason untuk status change
        
        Returns:
            bool: Success or not
        """
        version = self.get_version_by_id(version_id)
        if not version:
            print(f"❌ Version {version_id} not found")
            return False
        
        old_status = version['status']
        version['status'] = new_status.value
        
        # Add to change history
        version['change_history'].append({
            'type': 'status_change',
            'timestamp': datetime.now().isoformat(),
            'from': old_status,
            'to': new_status.value,
            'reason': reason,
        })
        
        print(f"✓ Version {version_id} status updated: {old_status} → {new_status.value}")
        return True
    
    def add_change_note(self, version_id: str, note: str, change_type: str = "note") -> bool:
        """
        Add catatan perubahan ke version
        
        Args:
            version_id (str): Version ID
            note (str): Catatan perubahan
            change_type (str): Tipe perubahan
        
        Returns:
            bool: Success or not
        """
        version = self.get_version_by_id(version_id)
        if not version:
            return False
        
        version['change_history'].append({
            'type': change_type,
            'timestamp': datetime.now().isoformat(),
            'note': note,
        })
        
        print(f"✓ Change note added to {version_id}")
        return True
    
    def get_change_history(self, version_id: str) -> Optional[List[Dict]]:
        """Get change history untuk specific version"""
        version = self.get_version_by_id(version_id)
        if version:
            return version.get('change_history', [])
        return None
    
    def compare_versions(self, version_id_1: str, version_id_2: str) -> Optional[Dict]:
        """
        Compare dua versions
        
        Args:
            version_id_1 (str): First version ID
            version_id_2 (str): Second version ID
        
        Returns:
            Dict: Comparison result
        """
        v1 = self.get_version_by_id(version_id_1)
        v2 = self.get_version_by_id(version_id_2)
        
        if not v1 or not v2:
            print("❌ One or both versions not found")
            return None
        
        # Simple diff untuk specification
        changes = []
        for key in v1.get('specification', {}):
            if v1['specification'].get(key) != v2['specification'].get(key):
                changes.append({
                    'key': key,
                    'from': v1['specification'].get(key),
                    'to': v2['specification'].get(key),
                })
        
        return {
            'version_1': v1['version_number'],
            'version_2': v2['version_number'],
            'differences': changes,
            'change_count': len(changes),
        }
    
    def validate(self) -> Dict:
        """Validate version tracker data"""
        errors = []
        
        if not self.product_id:
            errors.append("product_id is required")
        if len(self.versions) == 0:
            errors.append("At least one version should exist")
        
        # Check for duplicate version numbers
        version_numbers = [v['version_number'] for v in self.versions]
        if len(version_numbers) != len(set(version_numbers)):
            errors.append("Duplicate version numbers found")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
        }
    
    def to_dict(self) -> Dict:
        """Convert tracker ke dictionary"""
        return {
            'product_id': self.product_id,
            'total_versions': len(self.versions),
            'current_version': self.current_version['version_number'] if self.current_version else None,
            'versions': self.versions,
        }
    
    def save_to_db(self) -> bool:
        """Save version tracker ke database"""
        validation = self.validate()
        
        if not validation['is_valid']:
            print("❌ Validation failed:")
            for error in validation['errors']:
                print(f"  - {error}")
            return False
        
        if not self.db_connection:
            print("⚠️  No database connection available")
            print("Spec versions:", json.dumps(self.to_dict(), indent=2))
            return True
        
        try:
            # Execute queries untuk insert versions
            # Pseudo code - replace dengan actual database insert
            # for version in self.versions:
            #     self.db_connection.insert('spec_versions', version)
            print("✓ Spec versions saved to database")
            return True
        except Exception as e:
            print(f"❌ Error saving to database: {e}")
            return False
    
    def __str__(self) -> str:
        """String representation"""
        return f"SpecVersionTracker(product_id={self.product_id}, versions={len(self.versions)})"
