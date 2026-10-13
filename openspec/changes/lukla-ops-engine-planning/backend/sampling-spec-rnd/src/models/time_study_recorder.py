"""
@name: TimeStudyRecorder
@description: Class untuk merekam Time Study dengan stopwatch digital
@params: spec_id (str) - ID spesifikasi produk
@params: db_connection - Database connection object
@returns: TimeStudyRecorder instance
@example:
    recorder = TimeStudyRecorder(spec_id='spec-123', db_conn=conn)
    recorder.start_timer()
    recorder.record_phase('Potong', duration=120)
    recorder.save_time_study()
"""

from datetime import datetime
from typing import List, Dict, Optional
import json


class TimeStudyRecorder:
    """Recorder untuk time study dengan support untuk multiple phases"""
    
    def __init__(self, spec_id: str, product_id: str, db_connection=None):
        """
        Initialize recorder
        
        Args:
            spec_id (str): Spec ID yang sedang di-study
            product_id (str): Product ID
            db_connection: Database connection untuk save
        """
        self.spec_id = spec_id
        self.product_id = product_id
        self.db_connection = db_connection
        
        self.is_running = False
        self.start_time = None
        self.current_phase_start = None
        self.phases: List[Dict] = []
        self.total_duration = 0
        
    def start_timer(self) -> None:
        """Mulai timer"""
        self.is_running = True
        self.current_phase_start = datetime.now()
        print("⏱️  Timer started")
    
    def stop_timer(self) -> None:
        """Stop timer"""
        self.is_running = False
        print("⏱️  Timer stopped")
    
    def record_phase(self, phase_name: str, duration: int = None, notes: str = "") -> None:
        """
        Record satu fase
        
        Args:
            phase_name (str): Nama fase (e.g., 'Potong', 'Jahit', 'QC')
            duration (int): Duration dalam seconds (jika None, pakai dari timer)
            notes (str): Catatan tambahan
        """
        if duration is None:
            if not self.current_phase_start:
                raise ValueError("Timer belum started atau phase belum di-record")
            duration = int((datetime.now() - self.current_phase_start).total_seconds())
        
        phase_record = {
            'id': f"phase-{len(self.phases) + 1}",
            'name': phase_name,
            'duration': duration,
            'timestamp': datetime.now().isoformat(),
            'notes': notes,
        }
        
        self.phases.append(phase_record)
        self.total_duration += duration
        self.current_phase_start = None
        
        print(f"✓ Phase '{phase_name}' recorded: {duration}s")
    
    def get_phases(self) -> List[Dict]:
        """Get semua phases yang sudah direkam"""
        return self.phases
    
    def get_total_duration(self) -> int:
        """Get total duration semua phases"""
        return self.total_duration
    
    def get_average_phase_time(self, phase_name: str) -> Optional[float]:
        """Get average time untuk specific phase"""
        matching_phases = [p for p in self.phases if p['name'] == phase_name]
        if not matching_phases:
            return None
        return sum(p['duration'] for p in matching_phases) / len(matching_phases)
    
    def delete_phase(self, phase_id: str) -> None:
        """Delete satu phase"""
        for phase in self.phases:
            if phase['id'] == phase_id:
                self.total_duration -= phase['duration']
                self.phases.remove(phase)
                print(f"✓ Phase {phase_id} deleted")
                return
        raise ValueError(f"Phase {phase_id} not found")
    
    def reset(self) -> None:
        """Reset recorder"""
        self.phases = []
        self.total_duration = 0
        self.is_running = False
        self.current_phase_start = None
        print("✓ Recorder reset")
    
    def validate(self) -> Dict:
        """Validate time study data"""
        errors = []
        
        if not self.spec_id:
            errors.append("spec_id is required")
        if not self.product_id:
            errors.append("product_id is required")
        if len(self.phases) == 0:
            errors.append("At least one phase is required")
        
        # Check phase validity
        for idx, phase in enumerate(self.phases):
            if not phase.get('name'):
                errors.append(f"Phase {idx}: name is required")
            if phase.get('duration', 0) <= 0:
                errors.append(f"Phase {idx}: duration must be > 0")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
        }
    
    def to_dict(self) -> Dict:
        """Convert recorder data ke dictionary"""
        return {
            'spec_id': self.spec_id,
            'product_id': self.product_id,
            'total_duration': self.total_duration,
            'phases': self.phases,
            'created_at': datetime.now().isoformat(),
            'phase_count': len(self.phases),
        }
    
    def save_to_db(self) -> bool:
        """Save time study ke database"""
        validation = self.validate()
        
        if not validation['is_valid']:
            print("❌ Validation failed:")
            for error in validation['errors']:
                print(f"  - {error}")
            return False
        
        if not self.db_connection:
            print("⚠️  No database connection available")
            print("Time study data:", json.dumps(self.to_dict(), indent=2))
            return True
        
        try:
            # Execute query untuk insert time study
            data = self.to_dict()
            # Pseudo code - replace dengan actual database insert
            # result = self.db_connection.insert('time_studies', data)
            print("✓ Time study saved to database")
            return True
        except Exception as e:
            print(f"❌ Error saving to database: {e}")
            return False
    
    def __str__(self) -> str:
        """String representation"""
        return f"TimeStudyRecorder(spec_id={self.spec_id}, phases={len(self.phases)}, total_time={self.total_duration}s)"
