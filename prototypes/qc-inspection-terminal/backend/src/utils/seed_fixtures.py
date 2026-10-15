"""FIXTURE DATA — NON-PRODUCTION.

Mock garment units untuk pengembangan & smoke-test prototype. JANGAN
diperlakukan sebagai data produksi. Saat migrasi enterprise M007 dijalankan,
data ini harus diganti hasil query ke `garment_assemblies` dan `assembly_components`
dari PostgreSQL dengan RLS aktif.

Setiap unit diberi `source_label="FIXTURE"` yang ikut keluar di response,
memudahkan inspeksi source-of-truth saat debugging.
"""

from __future__ import annotations

from ..models.qc_inspection import GarmentUnit, GarmentStatus, OperatorRef


FIXTURE_UNITS: list[GarmentUnit] = [
    GarmentUnit(
        serial_code="U-501",
        order_id="SO-2026-001",
        article_code="PARKA-A",
        client_code="client-A",
        operators=[
            OperatorRef("op-s1", "Penjahit 1", "SLEEVE"),
            OperatorRef("op-s2", "Penjahit 2", "BODY"),
        ],
        status=GarmentStatus.MENUNGGU_QC,
    ),
    GarmentUnit(
        serial_code="U-502",
        order_id="SO-2026-001",
        article_code="PARKA-A",
        client_code="client-A",
        operators=[
            OperatorRef("op-s1", "Penjahit 1", "ZIPPER"),
        ],
        status=GarmentStatus.MENUNGGU_QC,
    ),
    GarmentUnit(
        serial_code="U-503",
        order_id="SO-2026-001",
        article_code="PARKA-A",
        client_code="client-A",
        operators=[
            OperatorRef("op-s3", "Penjahit 3", "COLLAR"),
        ],
        status=GarmentStatus.MENUNGGU_QC,
    ),
    GarmentUnit(
        serial_code="R-101",
        order_id="SO-2026-001",
        article_code="PARKA-A",
        client_code="client-A",
        operators=[
            OperatorRef("op-s1", "Penjahit 1", "SLEEVE"),
        ],
        status=GarmentStatus.REWORK,
    ),
    GarmentUnit(
        serial_code="U-700",
        order_id="SO-2026-002",
        article_code="TOTE-C",
        client_code="client-B",
        operators=[
            OperatorRef("op-s4", "Penjahit 4", "BODY"),
        ],
        status=GarmentStatus.MENUNGGU_QC,
    ),
]


def get_fixtures() -> list[GarmentUnit]:
    return list(FIXTURE_UNITS)
