"""
@name: Sampling & Spec R&D Workflow Example
@description: Complete example implementation untuk SAMPLING & SPEC R&D module
@example: Full workflow dari time study recording sampai R&D drift detection
"""

from components.time_study_recorder import TimeStudyRecorder
from components.spec_version_tracker import SpecVersionTracker, VersionStatus
from snippets.time_study_patterns import (
    calculate_average_phase_time,
    calculate_quality_score,
    compare_spec_versions,
    detect_rnd_drift,
    generate_time_study_report,
)
from snippets.spec_version_patterns import (
    check_spec_compliance,
    detect_spec_drift,
    diff_versions,
    generate_change_report,
)


class SamplingRnDWorkflow:
    """
    Complete workflow untuk SAMPLING & SPEC R&D dengan integration
    antara time study dan spec versioning
    """
    
    def __init__(self, product_id: str, db_connection=None):
        """
        Initialize workflow
        
        Args:
            product_id (str): Product ID
            db_connection: Database connection
        """
        self.product_id = product_id
        self.db_connection = db_connection
        
        # Initialize components
        self.time_study_recorder = TimeStudyRecorder(
            spec_id="",
            product_id=product_id,
            db_connection=db_connection
        )
        self.spec_tracker = SpecVersionTracker(
            product_id=product_id,
            db_connection=db_connection
        )
        
        self.time_studies = []
        self.current_spec_id = None
    
    # ===========================
    # PHASE 1: Initial Spec Creation
    # ===========================
    def create_initial_spec(
        self,
        version_number: str,
        description: str,
        specification: dict,
        created_by: str = "rd-team"
    ) -> dict:
        """
        Create spesifikasi awal produk
        
        Args:
            version_number (str): Version number (e.g., '1.0')
            description (str): Deskripsi
            specification (dict): Spec details
            created_by (str): Pembuat
        
        Returns:
            dict: Created version
        """
        print(f"\n📋 Creating initial spec version {version_number}...")
        
        version = self.spec_tracker.create_version(
            version_number=version_number,
            description=description,
            specification=specification,
            created_by=created_by,
            status=VersionStatus.DRAFT
        )
        
        self.current_spec_id = version['id']
        print(f"✓ Spec version created: {version['id']}")
        
        return version
    
    # ===========================
    # PHASE 2: Time Study Recording
    # ===========================
    def record_time_study_session(
        self,
        spec_version_id: str,
        operator_name: str,
        phases_data: list
    ) -> dict:
        """
        Record satu sesi time study
        
        Args:
            spec_version_id (str): Spec version yang dipelajari
            operator_name (str): Nama operator
            phases_data (list): List of {name, duration, notes}
        
        Returns:
            dict: Recorded time study
        """
        print(f"\n⏱️  Recording time study for spec {spec_version_id}...")
        
        # Create new time study recorder untuk session ini
        recorder = TimeStudyRecorder(
            spec_id=spec_version_id,
            product_id=self.product_id,
            db_connection=self.db_connection
        )
        
        # Record semua phases
        for phase_data in phases_data:
            recorder.record_phase(
                phase_name=phase_data['name'],
                duration=phase_data['duration'],
                notes=phase_data.get('notes', '')
            )
        
        # Prepare time study record
        time_study = {
            **recorder.to_dict(),
            'operator': operator_name,
            'date': __import__('datetime').datetime.now().strftime('%Y-%m-%d'),
            'quality_score': 100,  # Will be updated after QC
            'status': 'completed',
        }
        
        self.time_studies.append(time_study)
        print(f"✓ Time study recorded: {recorder.get_total_duration()}s total")
        
        return time_study
    
    # ===========================
    # PHASE 3: Analysis & Quality Check
    # ===========================
    def analyze_time_studies(
        self,
        spec_version_id: str
    ) -> dict:
        """
        Analyze semua time studies untuk specific spec version
        
        Args:
            spec_version_id (str): Spec version ID
        
        Returns:
            dict: Analysis result
        """
        print(f"\n📊 Analyzing time studies for {spec_version_id}...")
        
        # Filter time studies untuk spec ini
        spec_studies = [ts for ts in self.time_studies if ts['spec_id'] == spec_version_id]
        
        if not spec_studies:
            print("⚠️  No time studies found for this spec")
            return {}
        
        # Generate report
        report = generate_time_study_report(spec_studies, spec_version_id)
        
        # Print summary
        print(f"  Total recordings: {report['summary']['total_recordings']}")
        print(f"  Average total time: {report['summary']['average_total_time']}s")
        
        for phase_analysis in report['phase_analysis']:
            print(f"  - {phase_analysis['phase_name']}: {phase_analysis['average']}s (σ={phase_analysis['std_dev']})")
        
        return report
    
    # ===========================
    # PHASE 4: Spec Iteration
    # ===========================
    def create_improved_spec(
        self,
        previous_version_id: str,
        new_version_number: str,
        changes: dict,
        change_reason: str,
        created_by: str = "rd-team"
    ) -> dict:
        """
        Create improved spec version berdasarkan hasil time study
        
        Args:
            previous_version_id (str): Previous spec ID
            new_version_number (str): New version number
            changes (dict): Changed specification
            change_reason (str): Alasan perubahan
            created_by (str): Pembuat
        
        Returns:
            dict: New version
        """
        print(f"\n🔄 Creating improved spec version {new_version_number}...")
        
        # Get previous spec
        prev_version = self.spec_tracker.get_version_by_id(previous_version_id)
        if not prev_version:
            raise ValueError(f"Previous version {previous_version_id} not found")
        
        # Merge with changes
        new_spec = {**prev_version['specification'], **changes}
        
        # Create new version
        version = self.spec_tracker.create_version(
            version_number=new_version_number,
            description=f"Improvement from {prev_version['version_number']}",
            specification=new_spec,
            created_by=created_by,
            changes=change_reason,
            status=VersionStatus.DRAFT
        )
        
        self.current_spec_id = version['id']
        print(f"✓ Improved spec created: {version['id']}")
        
        return version
    
    # ===========================
    # PHASE 5: R&D Drift Detection
    # ===========================
    def check_for_rnd_drift(
        self,
        baseline_spec_id: str,
        current_spec_id: str
    ) -> dict:
        """
        Deteksi jika ada drift (R&D deviation) antar spec versions
        
        Args:
            baseline_spec_id (str): Baseline/approved spec
            current_spec_id (str): Current spec to check
        
        Returns:
            dict: Drift analysis
        """
        print(f"\n🔍 Checking for R&D drift...")
        
        # Get baseline dan current time studies
        baseline_studies = [ts for ts in self.time_studies if ts['spec_id'] == baseline_spec_id]
        current_studies = [ts for ts in self.time_studies if ts['spec_id'] == current_spec_id]
        
        if not baseline_studies or not current_studies:
            print("⚠️  Insufficient time study data")
            return {}
        
        # Detect drift
        drift_result = detect_rnd_drift(
            baseline_studies,
            current_studies,
            threshold=15.0
        )
        
        # Report results
        if drift_result['drift_detected']:
            print("⚠️  R&D DRIFT DETECTED!")
            for phase_name, analysis in drift_result['analysis'].items():
                if analysis['has_drift']:
                    print(f"  - {phase_name}: {analysis['drift_percent']}% {analysis['direction']}")
        else:
            print("✓ No significant R&D drift detected")
        
        return drift_result
    
    # ===========================
    # PHASE 6: Spec Approval
    # ===========================
    def approve_spec(
        self,
        spec_version_id: str,
        approver: str,
        approval_notes: str = ""
    ) -> bool:
        """
        Approve spec version setelah R&D okayed
        
        Args:
            spec_version_id (str): Spec to approve
            approver (str): Approver name
            approval_notes (str): Notes
        
        Returns:
            bool: Success
        """
        print(f"\n✅ Approving spec {spec_version_id}...")
        
        success = self.spec_tracker.update_version_status(
            version_id=spec_version_id,
            new_status=VersionStatus.APPROVED,
            reason=approval_notes
        )
        
        if success:
            print(f"✓ Spec approved by {approver}")
        
        return success
    
    # ===========================
    # PHASE 7: Generate Documentation
    # ===========================
    def generate_workflow_summary(self) -> str:
        """
        Generate summary dokumentasi workflow
        
        Returns:
            str: Summary report
        """
        print(f"\n📄 Generating workflow summary...")
        
        lines = [
            "=" * 50,
            "SAMPLING & SPEC R&D WORKFLOW SUMMARY",
            "=" * 50,
            f"Product ID: {self.product_id}",
            f"Total Versions: {len(self.spec_tracker.versions)}",
            f"Total Time Studies: {len(self.time_studies)}",
            "",
            "VERSIONS:",
        ]
        
        for version in self.spec_tracker.versions:
            lines.append(f"  - {version['version_number']}: {version['description']}")
            lines.append(f"    Status: {version['status']}")
        
        lines.extend([
            "",
            "TIME STUDIES:",
            f"  Total studies: {len(self.time_studies)}",
        ])
        
        # Group by spec
        for spec_id in set(ts['spec_id'] for ts in self.time_studies):
            spec_studies = [ts for ts in self.time_studies if ts['spec_id'] == spec_id]
            lines.append(f"  - {spec_id}: {len(spec_studies)} recordings")
        
        lines.append("=" * 50)
        
        return "\n".join(lines)


# ===========================
# USAGE EXAMPLE
# ===========================
def main():
    """
    Complete workflow example
    """
    print("🚀 Starting Sampling & Spec R&D Workflow Demo\n")
    
    # Initialize workflow
    workflow = SamplingRnDWorkflow(product_id="shirt-001")
    
    # STEP 1: Create initial spec
    initial_spec = workflow.create_initial_spec(
        version_number="1.0",
        description="Initial specification: Cotton shirt with standard padding",
        specification={
            'material': 'Cotton 100%',
            'size': 'M',
            'padding_mm': 5,
            'stitch_size_mm': 2,
            'color': 'White',
        }
    )
    
    # STEP 2: Record time studies untuk spec v1.0
    print("\n📝 Recording time studies...\n")
    
    for i in range(3):
        workflow.record_time_study_session(
            spec_version_id=initial_spec['id'],
            operator_name=f"Operator-{i+1}",
            phases_data=[
                {'name': 'Potong', 'duration': 120, 'notes': 'Normal'},
                {'name': 'Jahit', 'duration': 180, 'notes': 'Smooth'},
                {'name': 'QC', 'duration': 60, 'notes': 'Pass'},
            ]
        )
    
    # STEP 3: Analyze time studies
    analysis_v1 = workflow.analyze_time_studies(initial_spec['id'])
    
    # STEP 4: Create improved spec based on analysis
    improved_spec = workflow.create_improved_spec(
        previous_version_id=initial_spec['id'],
        new_version_number="1.1",
        changes={'padding_mm': 4},  # Reduce padding untuk lebih cepat
        change_reason="Reduce padding to improve efficiency"
    )
    
    # STEP 5: Record time studies untuk spec v1.1
    print("\n📝 Recording time studies for v1.1...\n")
    
    for i in range(3):
        workflow.record_time_study_session(
            spec_version_id=improved_spec['id'],
            operator_name=f"Operator-{i+1}",
            phases_data=[
                {'name': 'Potong', 'duration': 115, 'notes': 'Faster'},
                {'name': 'Jahit', 'duration': 160, 'notes': 'Improved'},
                {'name': 'QC', 'duration': 55, 'notes': 'Pass'},
            ]
        )
    
    # STEP 6: Analyze v1.1 dan compare
    analysis_v1_1 = workflow.analyze_time_studies(improved_spec['id'])
    
    # STEP 7: Check for R&D drift
    drift_check = workflow.check_for_rnd_drift(
        baseline_spec_id=initial_spec['id'],
        current_spec_id=improved_spec['id']
    )
    
    # STEP 8: Approve improved spec
    workflow.approve_spec(
        spec_version_id=improved_spec['id'],
        approver="QC-Manager",
        approval_notes="Time study shows 10% efficiency improvement"
    )
    
    # STEP 9: Generate summary
    summary = workflow.generate_workflow_summary()
    print(summary)


if __name__ == "__main__":
    main()
