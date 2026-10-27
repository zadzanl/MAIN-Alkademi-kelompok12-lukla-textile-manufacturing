"""seed.py — Deterministic demo fixtures and persistence for Sampling & Spec R&D.

Provides rich, realistic manufacturing R&D fixtures for:
  - SpecVersionTracker (Seam engineering parameters, SPI, tension, tolerances, and drifts)
  - Garment Sample Versions (v1 baseline and v2 optimized BOM, components, rate cards, and revision log for ART-ADIS-001)
  - Time Studies (Standard 5-operation sewing protocol with realistic cycle time samples)

Includes JSON snapshot persistence to disk so user edits survive process restarts on EC2.
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..models.spec_version_tracker import ChangeType, SpecChange, SpecDrift, SpecVersionTracker, VersionStatus
from ..models.time_study_recorder import StudyStatus, TimeSample, TimeStudyRecorder
from ..services.sampling_rnd_workflow import SamplingRnDWorkflow

DEFAULT_TENANT_ID = "tenant-001"
DATA_FILE_ENV = "SAMPLING_DATA_FILE"

_lock = threading.RLock()
_seeded = False


def _get_storage_path() -> Path:
    env_path = os.getenv(DATA_FILE_ENV)
    if env_path:
        return Path(env_path)
    # Default to data directory under prototypes/sampling-spec-rnd/backend/data
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_dir = base_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "sampling_rnd_state.json"


def build_default_specs(tenant_id: str = DEFAULT_TENANT_ID) -> list[SpecVersionTracker]:
    """Build default SpecVersionTracker fixtures."""
    now = datetime.now(timezone.utc)
    
    # 1. Flagship Adis Spec Version v2 (Active with seam drift benchmarks)
    spec_v2 = SpecVersionTracker(
        version_id="spec-adis-v2",
        tenant_id=tenant_id,
        spec_id="SPEC-ADIS-001",
        spec_name="Adis Technical Running Tee — Seam Assembly v2",
        version_number="2.0",
        created_at=now,
        updated_at=now,
        status=VersionStatus.ACTIVE,
        parameters={
            "kerapatan_setik_spi": 12.0,
            "lebar_kampuh_jahitan_mm": 10.0,
            "tegangan_benang_jarum_cn": 120.0,
            "panjang_langkah_setik_mm": 2.5,
            "kemiringan_obras_skew_pct": 2.0,
        },
        tolerances={
            "kerapatan_setik_spi": {"min": 11.5, "max": 12.5},
            "lebar_kampuh_jahitan_mm": {"min": 9.0, "max": 11.0},
            "tegangan_benang_jarum_cn": {"min": 110.0, "max": 130.0},
            "panjang_langkah_setik_mm": {"min": 2.3, "max": 2.7},
            "kemiringan_obras_skew_pct": {"min": 0.0, "max": 2.5},
        },
        materials=[
            "Dry-Fit Microfiber 140gsm",
            "Rib Cotton 2x2 Pre-shrunk",
            "Spun Polyester 40/2",
        ],
        process_steps=[
            "Potong Pola",
            "Jahit Kerah Rib & Kerung Leher",
            "Bahu Double Stitch (Mobilon Tape)",
            "Pasang Lengan & Obras 4-Thread",
            "Jahit Samping & Belahan Bawah",
            "Kelim Bawah Hemming",
        ],
        created_by="Budi Time-Study (IE)",
        approved_by="manager-001",
        approved_at=now,
        notes="Spesifikasi jahitan v2 hasil validasi digital stopwatch time study Adis Sample.",
        parent_version_id="spec-adis-v1",
        supersedes_version_id="spec-adis-v1",
    )

    # Changes log
    spec_v2.add_change(
        SpecChange(
            change_type=ChangeType.PARAMETER_UPDATE,
            parameter_name="kerapatan_setik_spi",
            old_value="10.0",
            new_value="12.0",
            changed_by="Budi Time-Study (IE)",
            reason="Peningkatan tensile strength jahitan dan elastisitas kain atletik",
            impact_assessment="Kuat tarik seam meningkat +20%, bebas puckering",
        )
    )
    spec_v2.add_change(
        SpecChange(
            change_type=ChangeType.PROCESS_CHANGE,
            parameter_name="proses_obras",
            old_value="3-Thread Overlock",
            new_value="4-Thread Safety Stitch",
            changed_by="Ahmad Designer (R&D)",
            reason="Mencegah jahitan lepas saat pergerakan intensif atlet lari",
            impact_assessment="Durabilitas jahitan terstandarisasi ISO 4915",
        )
    )

    # Benchmark drifts
    spec_v2.record_drift(
        SpecDrift(
            drift_id="drf-adis-001",
            timestamp=now,
            parameter_name="kerapatan_setik_spi",
            specification_limit=12.0,
            measured_value=10.5,
            deviation_percent=12.5,
            severity="medium",
            corrective_action="Kalibrasi feed dog dan tension dial mesin jahit #04",
            resolved=True,
            resolved_at=now,
        )
    )
    spec_v2.record_drift(
        SpecDrift(
            drift_id="drf-adis-002",
            timestamp=now,
            parameter_name="lebar_kampuh_jahitan_mm",
            specification_limit=10.0,
            measured_value=12.2,
            deviation_percent=22.0,
            severity="high",
            corrective_action="Setel ulang guide plate pembatas kampuh lini obras",
            resolved=False,
            resolved_at=None,
        )
    )
    spec_v2.record_drift(
        SpecDrift(
            drift_id="drf-adis-003",
            timestamp=now,
            parameter_name="kemiringan_obras_skew_pct",
            specification_limit=2.0,
            measured_value=2.8,
            deviation_percent=40.0,
            severity="critical",
            corrective_action="Periksa kelurusan feeding kain pada roll penarik",
            resolved=False,
            resolved_at=None,
        )
    )

    # 2. Adis Spec Baseline v1 (Superseded)
    spec_v1 = SpecVersionTracker(
        version_id="spec-adis-v1",
        tenant_id=tenant_id,
        spec_id="SPEC-ADIS-001",
        spec_name="Adis Technical Running Tee — Baseline v1",
        version_number="1.0",
        created_at=now,
        updated_at=now,
        status=VersionStatus.SUPERSEDED,
        parameters={
            "kerapatan_setik_spi": 10.0,
            "lebar_kampuh_jahitan_mm": 10.0,
            "tegangan_benang_jarum_cn": 110.0,
            "panjang_langkah_setik_mm": 2.8,
            "kemiringan_obras_skew_pct": 2.5,
        },
        tolerances={
            "kerapatan_setik_spi": {"min": 9.0, "max": 11.0},
            "lebar_kampuh_jahitan_mm": {"min": 8.5, "max": 11.5},
            "tegangan_benang_jarum_cn": {"min": 100.0, "max": 120.0},
        },
        materials=["Cotton Single Jersey 24s", "Rib Cotton 1x1"],
        process_steps=["Potong Pola", "Jahit Kerah", "Obras Lengan", "Kelim Bawah"],
        created_by="Ahmad Designer (R&D)",
        approved_by="manager-001",
        approved_at=now,
        notes="Baseline prototype awal. Terdeteksi puckering di kerung leher.",
        parent_version_id=None,
        supersedes_version_id=None,
    )

    # 3. Draft Spec for Bomber Jacket R&D
    spec_bomber = SpecVersionTracker(
        version_id="spec-bomber-v1",
        tenant_id=tenant_id,
        spec_id="SPEC-BOMB-001",
        spec_name="Jaket Bomber Maklon — R&D Sample",
        version_number="1.0.0",
        created_at=now,
        updated_at=now,
        status=VersionStatus.REVIEW,
        parameters={
            "kerapatan_setik_spi": 9.0,
            "lebar_kampuh_jahitan_mm": 12.0,
            "tegangan_benang_jarum_cn": 140.0,
        },
        tolerances={
            "kerapatan_setik_spi": {"min": 8.0, "max": 10.0},
            "lebar_kampuh_jahitan_mm": {"min": 11.0, "max": 13.0},
        },
        materials=["Poly-Oxford 600D", "Dacron 4oz Padding", "Zipper YKK Metal #5"],
        process_steps=["Cutting Pola", "Quilting Padding", "Pasang Ritsleting", "Obras Badan"],
        created_by="Ahmad Designer (R&D)",
        notes="Draft spesifikasi sampel jaket bomber anti-angin.",
    )

    return [spec_v2, spec_v1, spec_bomber]


def build_default_sample_versions(tenant_id: str = DEFAULT_TENANT_ID) -> list[dict[str, Any]]:
    """Build default Garment Sample Versions matching SampleVersionView."""
    now_iso = datetime.now(timezone.utc).isoformat()

    sv_v1: dict[str, Any] = {
        "version_id": "sv-adis-v1",
        "tenant_id": tenant_id,
        "article_id": "ART-ADIS-001",
        "article_name": "Adis Technical Running Tee (Adis Sample)",
        "client_id": "adis-sports",
        "version_number": 1,
        "version_label": "v1",
        "parent_version_id": None,
        "status": "approved",
        "created_by": "Ahmad Designer (R&D)",
        "created_at": now_iso,
        "updated_at": now_iso,
        "approved_by": "manager-001",
        "approved_at": now_iso,
        "converted_to_order_id": None,
        "notes": "Spesifikasi v1 awal: jahitan reguler SPI 10, kerah single needle standard, kampuh 10mm.",
        "components": [
            {
                "component_id": "comp-adis-v1-1",
                "part_name": "Kerah Rib & Kerung Leher",
                "description": "Single needle stitch (SPI 10), kampuh jahitan 8mm",
                "material_type": "Rib Cotton 2x2",
                "estimated_usage_m": 0.25,
                "unit": "m",
                "sewing_time_std_ms": 22000,
                "rate_card_idr": 450,
                "notes": "Sedikit kerutan (puckering) pada area kurva leher.",
            },
            {
                "component_id": "comp-adis-v1-2",
                "part_name": "Jahit Bahu Double Stitch",
                "description": "2-needle lockstitch (SPI 10), kampuh jahitan 10mm",
                "material_type": "Polyester Thread 40/2",
                "estimated_usage_m": 0.15,
                "unit": "m",
                "sewing_time_std_ms": 15000,
                "rate_card_idr": 320,
                "notes": "Bahu reguler.",
            },
            {
                "component_id": "comp-adis-v1-3",
                "part_name": "Pasang Lengan & Obras",
                "description": "3-thread standard overlock (SPI 10), kampuh 8mm",
                "material_type": "Cotton Single Jersey 24s",
                "estimated_usage_m": 0.40,
                "unit": "m",
                "sewing_time_std_ms": 28000,
                "rate_card_idr": 580,
                "notes": "Sering terjadi thread-break saat penarikan benang kecepatan tinggi.",
            },
            {
                "component_id": "comp-adis-v1-4",
                "part_name": "Jahit Samping & Belahan Bawah",
                "description": "Single needle lockstitch (SPI 10), kampuh jahitan 10mm",
                "material_type": "Cotton Single Jersey 24s",
                "estimated_usage_m": 0.35,
                "unit": "m",
                "sewing_time_std_ms": 26000,
                "rate_card_idr": 540,
                "notes": "Jalur jahit sisi samping.",
            },
            {
                "component_id": "comp-adis-v1-5",
                "part_name": "Kelim Bawah Hemming",
                "description": "2-needle bottom coverstitch (SPI 10), lipatan kelim 20mm",
                "material_type": "Cotton Single Jersey 24s",
                "estimated_usage_m": 0.20,
                "unit": "m",
                "sewing_time_std_ms": 18000,
                "rate_card_idr": 380,
                "notes": "Hasil kelim agak tebal.",
            },
        ],
        "materials": [
            {
                "material_code": "FAB-CSJ-24S",
                "material_name": "Cotton Single Jersey 24s",
                "estimated_usage": 1.15,
                "unit": "m",
                "unit_cost": 45000,
                "total_cost": 51750,
                "supplier_id": "SUP-TEX-01",
                "notes": "Kain badan utama",
            },
            {
                "material_code": "RIB-CTN-2X2",
                "material_name": "Rib Cotton 2x2",
                "estimated_usage": 0.25,
                "unit": "m",
                "unit_cost": 28000,
                "total_cost": 7000,
                "supplier_id": "SUP-TEX-02",
                "notes": "Bahan rib kerah leher",
            },
            {
                "material_code": "THRD-POLY-40",
                "material_name": "Benang Jahit Poly 40/2",
                "estimated_usage": 1.0,
                "unit": "pcs",
                "unit_cost": 6500,
                "total_cost": 6500,
                "supplier_id": "SUP-THR-01",
                "notes": "Benang jahit utama",
            },
        ],
        "revision_log": [
            {
                "action": "created",
                "by": "Ahmad Designer (R&D)",
                "at": now_iso,
                "note": "Initial prototype sample v1 untuk Adis Technical Tee.",
            },
            {
                "action": "approved",
                "by": "manager-001",
                "at": now_iso,
                "note": "Approved for sampling production review.",
            },
        ],
    }

    sv_v2: dict[str, Any] = {
        "version_id": "sv-adis-v2",
        "tenant_id": tenant_id,
        "article_id": "ART-ADIS-001",
        "article_name": "Adis Technical Running Tee (Adis Sample)",
        "client_id": "adis-sports",
        "version_number": 2,
        "version_label": "v2",
        "parent_version_id": "sv-adis-v1",
        "status": "approved",
        "created_by": "Budi Time-Study (IE)",
        "created_at": now_iso,
        "updated_at": now_iso,
        "approved_by": "manager-001",
        "approved_at": now_iso,
        "converted_to_order_id": None,
        "notes": (
            "v2 Optimasi: Hasil digital stopwatch time-study Adis Sample. Upgrade ke 4-thread safety overlock, "
            "SPI 12 (+20% tensile), pangkas waktu siklus total -11.5 detik per pcs."
        ),
        "components": [
            {
                "component_id": "comp-adis-v2-1",
                "part_name": "Kerah Rib & Kerung Leher",
                "description": "Single needle + taped neck reinforcement (SPI 12), kampuh 8mm",
                "material_type": "Rib Cotton 2x2 Pre-shrunk",
                "estimated_usage_m": 0.25,
                "unit": "m",
                "sewing_time_std_ms": 19500,
                "rate_card_idr": 410,
                "notes": "Hasil time-study: efisiensi +2.5s, bebas puckering.",
            },
            {
                "component_id": "comp-adis-v2-2",
                "part_name": "Jahit Bahu Double Stitch",
                "description": "2-needle lockstitch with clear mobilon tape (SPI 12), kampuh 10mm",
                "material_type": "Spun Polyester 40/2",
                "estimated_usage_m": 0.15,
                "unit": "m",
                "sewing_time_std_ms": 14000,
                "rate_card_idr": 300,
                "notes": "Bahu lebih kokoh menahan beban tas ransel.",
            },
            {
                "component_id": "comp-adis-v2-3",
                "part_name": "Pasang Lengan & Obras",
                "description": "4-thread safety stitch overlock (SPI 12), kampuh 7mm",
                "material_type": "Dry-Fit Microfiber 140gsm",
                "estimated_usage_m": 0.38,
                "unit": "m",
                "sewing_time_std_ms": 24500,
                "rate_card_idr": 510,
                "notes": "4-thread overlock jauh lebih rapi & waktu pengerjaan turun 3.5s.",
            },
            {
                "component_id": "comp-adis-v2-4",
                "part_name": "Jahit Samping & Belahan Bawah",
                "description": "4-thread overlock (SPI 12), kampuh jahitan 8mm",
                "material_type": "Dry-Fit Microfiber 140gsm",
                "estimated_usage_m": 0.35,
                "unit": "m",
                "sewing_time_std_ms": 23000,
                "rate_card_idr": 480,
                "notes": "Waktu siklus terpangkas 3.0s setelah relayout meja kerja.",
            },
            {
                "component_id": "comp-adis-v2-5",
                "part_name": "Kelim Bawah Hemming",
                "description": "3-needle bottom coverstitch (SPI 11), lipatan kelim 20mm",
                "material_type": "Dry-Fit Microfiber 140gsm",
                "estimated_usage_m": 0.20,
                "unit": "m",
                "sewing_time_std_ms": 16500,
                "rate_card_idr": 350,
                "notes": "Jahitan kelim elastis, tidak putus saat ditarik.",
            },
        ],
        "materials": [
            {
                "material_code": "FAB-DF-140",
                "material_name": "Dry-Fit Microfiber 140gsm Quick-Dry",
                "estimated_usage": 1.10,
                "unit": "m",
                "unit_cost": 52000,
                "total_cost": 57200,
                "supplier_id": "SUP-TEX-01",
                "notes": "Bahan kain utama v2 (upgrade anti-bakteri & quick dry)",
            },
            {
                "material_code": "RIB-CTN-2X2-PS",
                "material_name": "Rib Cotton 2x2 Pre-shrunk",
                "estimated_usage": 0.25,
                "unit": "m",
                "unit_cost": 31000,
                "total_cost": 7750,
                "supplier_id": "SUP-TEX-02",
                "notes": "Rib leher anti melar",
            },
            {
                "material_code": "THRD-SPUN-40",
                "material_name": "Benang Jahit Spun Poly 40/2 High-Tenacity",
                "estimated_usage": 1.0,
                "unit": "pcs",
                "unit_cost": 7200,
                "total_cost": 7200,
                "supplier_id": "SUP-THR-01",
                "notes": "Benang high tenacity tahan gesekan mesin high speed",
            },
            {
                "material_code": "MOB-TAPE-06",
                "material_name": "Clear Mobilon Elastic Tape 6mm",
                "estimated_usage": 0.40,
                "unit": "m",
                "unit_cost": 1500,
                "total_cost": 600,
                "supplier_id": "SUP-ACC-03",
                "notes": "Pita penstabil jahitan bahu anti melar",
            },
        ],
        "revision_log": [
            {
                "action": "created",
                "by": "Budi Time-Study (IE)",
                "at": now_iso,
                "note": "Revisi v2 dibuat dari v1 berdasarkan hasil time-study stopwatch digital Adis Sample.",
            },
            {
                "action": "revised",
                "by": "Budi Time-Study (IE)",
                "at": now_iso,
                "note": "Pembaruan rate card dan waktu standar per komponen jahitan.",
            },
            {
                "action": "approved",
                "by": "manager-001",
                "at": now_iso,
                "note": "Disetujui untuk dipromosikan ke Order Produksi Massal (Mass Order).",
            },
        ],
    }

    return [sv_v2, sv_v1]


def build_default_time_studies(tenant_id: str = DEFAULT_TENANT_ID) -> list[TimeStudyRecorder]:
    """Build default TimeStudyRecorder fixtures."""
    now = datetime.now(timezone.utc)

    # 1. Adis Sample Sewing Protocol (Completed Study)
    study_1 = TimeStudyRecorder(
        study_id="study-adis-001",
        tenant_id=tenant_id,
        process_id="PROC-ADIS-SEW",
        process_name="Adis Running Tee — Standard Seam Protocol",
        created_at=now,
        updated_at=now,
        started_at=now,
        completed_at=now,
        status=StudyStatus.COMPLETED,
        target_sample_size=30,
        operator_id="OPR-SITI-01",
        department_id="DEPT-SEW-01",
        shift="Shift Pagi",
        product_id="ART-ADIS-001",
        notes="Studi waktu resmi lini percontohan Adis Sample.",
        confidence_level=0.95,
        allowance_percent=15.0,
    )

    # Add representative time samples across the 5 seam steps
    samples_data = [
        ("Kerah Rib & Kerung Leher", 19200),
        ("Kerah Rib & Kerung Leher", 19500),
        ("Kerah Rib & Kerung Leher", 19800),
        ("Jahit Bahu Double Stitch", 13800),
        ("Jahit Bahu Double Stitch", 14200),
        ("Pasang Lengan & Obras", 24100),
        ("Pasang Lengan & Obras", 24800),
        ("Jahit Samping & Belahan Bawah", 22900),
        ("Jahit Samping & Belahan Bawah", 23200),
        ("Kelim Bawah Hemming", 16300),
        ("Kelim Bawah Hemming", 16700),
    ]

    for elem, ms in samples_data:
        sample = TimeSample(
            cycle_time_ms=float(ms),
            element_name=elem,
            operator_id="OPR-SITI-01",
            is_abnormal=False,
            notes="Ritme kerja normal",
        )
        study_1.samples.append(sample)

    study_1.total_cycles = len(study_1.samples)
    study_1._compute_statistics()

    # 2. Active in-progress study for cutting & preparation
    study_2 = TimeStudyRecorder(
        study_id="study-adis-cut",
        tenant_id=tenant_id,
        process_id="PROC-ADIS-CUT",
        process_name="Adis Running Tee — Pola Cutting & Bundling",
        created_at=now,
        updated_at=now,
        started_at=now,
        status=StudyStatus.IN_PROGRESS,
        target_sample_size=20,
        operator_id="OPR-AGUS-02",
        department_id="DEPT-CUT-01",
        shift="Shift Pagi",
        product_id="ART-ADIS-001",
        notes="Pengukuran efisiensi bundling meja potong otomatis.",
        confidence_level=0.95,
        allowance_percent=12.0,
    )

    for ms in [45000, 43200, 46100, 44000]:
        sample = TimeSample(
            cycle_time_ms=float(ms),
            element_name="Potong Kain & Bundling Tiket",
            operator_id="OPR-AGUS-02",
            is_abnormal=False,
            notes="Operator berpengalaman",
        )
        study_2.samples.append(sample)

    study_2.total_cycles = len(study_2.samples)
    study_2._compute_statistics()

    return [study_1, study_2]
