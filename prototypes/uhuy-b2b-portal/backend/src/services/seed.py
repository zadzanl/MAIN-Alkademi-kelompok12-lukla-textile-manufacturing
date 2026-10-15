"""seed.py — Deterministic demo fixtures for the UHUY B2B external portal.

Seeds one internal admin plus two active demo clients (A and B) with orders and
consigned stock, so the portal can be explored immediately and the client_id
isolation boundary is demonstrable (client A must never see client B rows).

Runs once per process. Known ceiling: in-memory fixtures only, reset on restart.
"""

from __future__ import annotations

import os

from .portal_store import PortalStore, get_store

DEMO_ADMIN_EMAIL = os.getenv("SEED_ADMIN_EMAIL", "admin@uhuy.local")
DEMO_ADMIN_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "Admin#12345")

DEMO_CLIENT_A_EMAIL = "klien.a@uhuy.local"
DEMO_CLIENT_A_PASSWORD = "Klien#12345"
DEMO_CLIENT_A_ID = "CL-A"
DEMO_CLIENT_A_ORDER = "ORD-A-1001"

DEMO_CLIENT_B_EMAIL = "klien.b@uhuy.local"
DEMO_CLIENT_B_PASSWORD = "Klien#12345"
DEMO_CLIENT_B_ID = "CL-B"
DEMO_CLIENT_B_ORDER = "ORD-B-2001"

_seeded = False


def seed_demo(store: PortalStore | None = None) -> None:
    global _seeded
    if _seeded:
        return
    target = store or get_store()

    target.seed_admin(DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD)

    target.seed_client(
        client_id=DEMO_CLIENT_A_ID,
        company_name="Nusantara Apparel",
        contact_name="Rina Wijaya",
        email=DEMO_CLIENT_A_EMAIL,
        phone="081100000001",
        password=DEMO_CLIENT_A_PASSWORD,
    )
    target.seed_client(
        client_id=DEMO_CLIENT_B_ID,
        company_name="Bumi Tekstil",
        contact_name="Andi Pratama",
        email=DEMO_CLIENT_B_EMAIL,
        phone="081100000002",
        password=DEMO_CLIENT_B_PASSWORD,
    )

    target.seed_order(
        client_id=DEMO_CLIENT_A_ID,
        order_id=DEMO_CLIENT_A_ORDER,
        article_name="Kaos Polo Nusantara",
        quantity=500,
        scheme="Semi-CMT",
        status="sewing",
        progress=60,
        current_phase="Produksi Jahit",
        target_date="2026-11-05",
        timeline=[
            {"phase": "Order dikonfirmasi", "status": "done", "at": "2026-10-05"},
            {"phase": "Bahan diterima", "status": "done", "at": "2026-10-08"},
            {"phase": "Cutting", "status": "done", "at": "2026-10-11"},
            {"phase": "Produksi Jahit", "status": "active", "at": "2026-10-13"},
            {"phase": "Inspeksi QC", "status": "pending", "at": ""},
        ],
    )
    target.seed_order(
        client_id=DEMO_CLIENT_A_ID,
        order_id="ORD-A-1002",
        article_name="Jaket Bomber",
        quantity=200,
        scheme="CMT",
        status="qc",
        progress=85,
        current_phase="Inspeksi QC",
        target_date="2026-10-28",
        timeline=[
            {"phase": "Order dikonfirmasi", "status": "done", "at": "2026-09-30"},
            {"phase": "Cutting", "status": "done", "at": "2026-10-09"},
            {"phase": "Produksi Jahit", "status": "done", "at": "2026-10-12"},
            {"phase": "Inspeksi QC", "status": "active", "at": "2026-10-14"},
        ],
    )
    target.seed_order(
        client_id=DEMO_CLIENT_A_ID,
        order_id="ORD-A-1000",
        article_name="Kaos Basic",
        quantity=1000,
        scheme="Full Package",
        status="completed",
        progress=100,
        current_phase="Selesai",
        target_date="2026-10-01",
        timeline=[
            {"phase": "Order dikonfirmasi", "status": "done", "at": "2026-09-01"},
            {"phase": "Produksi Jahit", "status": "done", "at": "2026-09-20"},
            {"phase": "Inspeksi QC", "status": "done", "at": "2026-09-28"},
            {"phase": "Selesai", "status": "done", "at": "2026-10-01"},
        ],
    )
    target.seed_order(
        client_id=DEMO_CLIENT_B_ID,
        order_id=DEMO_CLIENT_B_ORDER,
        article_name="Kemeja Formal",
        quantity=800,
        scheme="CMT",
        status="cutting",
        progress=25,
        current_phase="Cutting",
        target_date="2026-11-15",
        timeline=[
            {"phase": "Order dikonfirmasi", "status": "done", "at": "2026-10-06"},
            {"phase": "Bahan diterima", "status": "done", "at": "2026-10-10"},
            {"phase": "Cutting", "status": "active", "at": "2026-10-14"},
            {"phase": "Produksi Jahit", "status": "pending", "at": ""},
        ],
    )
    target.seed_order(
        client_id=DEMO_CLIENT_B_ID,
        order_id="ORD-B-2002",
        article_name="Seragam Sekolah",
        quantity=1200,
        scheme="Semi-CMT",
        status="confirmed",
        progress=10,
        current_phase="Order dikonfirmasi",
        target_date="2026-12-01",
        timeline=[
            {"phase": "Order dikonfirmasi", "status": "active", "at": "2026-10-13"},
            {"phase": "Bahan diterima", "status": "pending", "at": ""},
        ],
    )

    target.seed_stock(
        client_id=DEMO_CLIENT_A_ID,
        material_code="FAB-CC30",
        material_name="Kain Cotton Combed 30s",
        unit="kg",
        quantity_available=320,
        received_at="2026-10-01",
    )
    target.seed_stock(
        client_id=DEMO_CLIENT_A_ID,
        material_code="THR-POLY",
        material_name="Benang Polyester",
        unit="roll",
        quantity_available=45,
        received_at="2026-10-03",
    )
    target.seed_stock(
        client_id=DEMO_CLIENT_B_ID,
        material_code="FAB-DRL",
        material_name="Kain Drill",
        unit="m",
        quantity_available=500,
        received_at="2026-10-02",
    )
    target.seed_stock(
        client_id=DEMO_CLIENT_B_ID,
        material_code="FAB-OXF",
        material_name="Kain Oxford",
        unit="m",
        quantity_available=260,
        received_at="2026-10-05",
    )

    _seeded = True
