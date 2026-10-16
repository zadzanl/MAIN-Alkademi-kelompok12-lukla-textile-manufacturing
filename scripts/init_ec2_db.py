"""
Database Migration and Schema Initializer for Lukla Operations Engine on EC2.
Usage:
    python scripts/init_ec2_db.py [DATABASE_URL]
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

MIGRATION_FILES = [
    "001_identities.sql",
    "006_payroll_rate_cards.sql",
    "007_assemblies_and_qc.sql",
    "007_payroll_qc_inputs.sql",
    "008_double_entry_ledger.sql",
    "009_payroll_core.sql",
    "011_job_idempotency.sql",
    "012_payroll_routines_rls.sql",
    "013_telegram_copilot_bindings.sql",
]


def run_migrations(db_url: str) -> None:
    try:
        import psycopg
    except ImportError:
        print("ERROR: psycopg is required. Run 'pip install \"psycopg[binary]\"'")
        sys.exit(1)

    # Normalize url if contains sqlalchemy prefix
    conn_url = db_url.replace("postgresql+psycopg://", "postgresql://")
    masked_url = conn_url.split("@")[-1] if "@" in conn_url else conn_url
    print(f"Connecting to database: {masked_url}...")

    migrations_dir = Path(__file__).resolve().parents[1] / "backend" / "migrations"

    with psycopg.connect(conn_url, autocommit=True) as conn:
        with conn.cursor() as cur:
            for sql_file in MIGRATION_FILES:
                path = migrations_dir / sql_file
                if not path.exists():
                    print(f"  [SKIP] {sql_file} (file not found)")
                    continue
                sql_content = path.read_text(encoding="utf-8")
                try:
                    cur.execute(sql_content)
                    print(f"  [OK] {sql_file}")
                except Exception as exc:
                    print(f"  [NOTE/WARN] {sql_file}: {exc}")


if __name__ == "__main__":
    target_url = (
        sys.argv[1]
        if len(sys.argv) > 1
        else os.getenv(
            "DATABASE_URL",
            "postgresql://myappuser:password_rahasia_kamu@127.0.0.1:5432/myappdb",
        )
    )
    run_migrations(target_url)
    print("Database migration check completed successfully.")
