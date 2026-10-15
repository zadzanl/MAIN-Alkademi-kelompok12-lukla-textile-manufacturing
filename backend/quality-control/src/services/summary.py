"""The ``qc`` section of the operations dashboard."""

from collections.abc import Iterable

from src.models.qc import AssemblyStatus, QcSummary


def summarize_statuses(statuses: Iterable[AssemblyStatus]) -> QcSummary:
    """Count one status per assembly, in the state it is in now.

    The dashboard counts assemblies, not inspection rows: an assembly that was
    repaired and later passed is one pass, not one repair plus one pass. An
    assembly awaiting inspection or still assembling carries no disposition yet
    and is counted nowhere.
    """
    pass_count = 0
    repair_count = 0
    reject_count = 0

    for status in statuses:
        if status is AssemblyStatus.QC_PASS:
            pass_count += 1
        elif status is AssemblyStatus.REWORK:
            repair_count += 1
        elif status is AssemblyStatus.REJECT_SCRAP:
            reject_count += 1

    return QcSummary(
        pass_count=pass_count,
        repair_count=repair_count,
        reject_count=reject_count,
    )
