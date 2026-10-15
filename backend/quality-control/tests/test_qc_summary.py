"""The dashboard counts assemblies in their current state, once each."""

from src.models.qc import AssemblyStatus, QcSummary
from src.services.summary import summarize_statuses


def test_each_disposition_is_counted_once() -> None:
    summary = summarize_statuses(
        [
            AssemblyStatus.QC_PASS,
            AssemblyStatus.QC_PASS,
            AssemblyStatus.REWORK,
            AssemblyStatus.REJECT_SCRAP,
        ]
    )

    assert summary == QcSummary(pass_count=2, repair_count=1, reject_count=1)


def test_assemblies_without_a_disposition_are_counted_nowhere() -> None:
    summary = summarize_statuses(
        [AssemblyStatus.MENUNGGU_QC, AssemblyStatus.ASSEMBLING, AssemblyStatus.MENUNGGU_QC]
    )

    assert summary == QcSummary(pass_count=0, repair_count=0, reject_count=0)


def test_an_empty_queue_is_all_zero() -> None:
    assert summarize_statuses([]) == QcSummary(pass_count=0, repair_count=0, reject_count=0)
