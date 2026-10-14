"""Garment unit status, mirroring the frozen ``garment_units.status`` values."""

from enum import StrEnum


class GarmentUnitStatus(StrEnum):
    """A unit earns piece-rate credit only once it has passed quality inspection."""

    MENUNGGU_QC = "MENUNGGU_QC"
    QC_PASS = "QC_PASS"
    REWORK = "REWORK"
    REJECT_SCRAP = "REJECT_SCRAP"
    ASSEMBLED = "ASSEMBLED"
