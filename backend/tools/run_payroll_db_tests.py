"""Run payroll invariants on one disposable loopback PostgreSQL database.

Ceiling: this checks the seven payroll foundation migrations, not the full API.
Add API tests to the subprocess command when their fixtures use the same isolated DB.
PostgreSQL CREATE/DROP DATABASE cannot run in a transaction; the unique generated
name and creation flag restrict cleanup to this invocation's database.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import uuid
from pathlib import Path

from psycopg import Error, connect, sql
from sqlalchemy.engine import URL, make_url

MIGRATIONS = (
    "001_identities.sql",
    "006_payroll_rate_cards.sql",
    "007_payroll_qc_inputs.sql",
    "008_double_entry_ledger.sql",
    "009_payroll_core.sql",
    "011_job_idempotency.sql",
    "012_payroll_routines_rls.sql",
)
ROOT = Path(__file__).resolve().parents[2]


def validate_urls(admin: URL, app: URL) -> None:
    for label, url in (("admin", admin), ("app", app)):
        if url.drivername != "postgresql+psycopg" or url.host != "127.0.0.1":
            raise ValueError(f"{label} URL must use postgresql+psycopg on 127.0.0.1")
        if not url.database or not url.username or url.query:
            raise ValueError(f"{label} URL needs a database and user, with no query overrides")
        if url.port is None:
            raise ValueError(f"{label} URL needs an explicit PostgreSQL port")
    if (admin.host, admin.port) != (app.host, app.port):
        raise ValueError("admin and app URLs must use the same loopback PostgreSQL instance")
    if admin.username == "lukla_app" or app.username != "lukla_app":
        raise ValueError("admin must not be lukla_app; app must be the restricted lukla_app role")


def connection_args(url: URL) -> dict[str, str | int]:
    args = url.translate_connect_args()
    names = {"database": "dbname", "username": "user"}
    return {
        names.get(key, key): value for key, value in args.items() if isinstance(value, (str, int))
    }


def run(admin: URL, app: URL) -> int:
    validate_urls(admin, app)
    with connect(**connection_args(admin)) as connection:
        role = connection.execute(
            "SELECT rolcanlogin, rolsuper, rolbypassrls, rolcreatedb, rolcreaterole "
            "FROM pg_roles WHERE rolname = 'lukla_app'"
        ).fetchone()
        if role is None or tuple(role) != (True, False, False, False, False):
            raise ValueError(
                "lukla_app must already exist with LOGIN and without SUPERUSER, "
                "BYPASSRLS, CREATEDB, or CREATEROLE; ask cluster admin to provision it"
            )
        if connection.execute("SELECT current_user").fetchone()[0] == "lukla_app":
            raise ValueError("migration connection must not use the application role")
    with connect(**connection_args(app)) as connection:
        if connection.execute("SELECT current_user").fetchone()[0] != "lukla_app":
            raise ValueError("application connection must authenticate as lukla_app")

    name = f"payroll_revision_{uuid.uuid4().hex}"
    admin_args = connection_args(admin)
    created = False
    try:
        with connect(**admin_args, autocommit=True) as connection:
            connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
            created = True
        test_admin = admin.set(database=name)
        for filename in MIGRATIONS:
            migration = ROOT / "backend" / "migrations" / filename
            if not migration.is_file():
                raise ValueError(f"Missing required migration: {filename}")
            try:
                with connect(**connection_args(test_admin)) as connection:
                    connection.execute(migration.read_text(encoding="utf-8"))
            except Error as error:
                raise ValueError(
                    f"migration {filename} failed (SQLSTATE {error.sqlstate}); "
                    "inspect the migration on the local server"
                ) from None
            print(f"Applied {filename}", flush=True)
        test_app = app.set(database=name)
        # Test module requires explicit URLs; never take these from the caller's environment.
        env = os.environ.copy()
        env["DATABASE_URL"] = test_admin.render_as_string(hide_password=False)
        env["LUKLA_APP_DATABASE_URL"] = test_app.render_as_string(hide_password=False)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "backend/tests/test_payroll_invariants.py",
                "-q",
            ],
            cwd=ROOT,
            env=env,
            check=False,
        )
        return result.returncode
    finally:
        if created:
            with connect(**admin_args, autocommit=True) as connection:
                connection.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(name)))
            print("Dropped owned disposable payroll test database", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--admin-url", required=True, help="loopback migration URL")
    parser.add_argument("--app-url", required=True, help="loopback restricted lukla_app URL")
    args = parser.parse_args()
    try:
        try:
            admin, app = make_url(args.admin_url), make_url(args.app_url)
        except ValueError:
            raise ValueError(
                "invalid URL syntax; use postgresql+psycopg://user@127.0.0.1:port/db"
            ) from None
        return run(admin, app)
    except (ValueError, Error, OSError) as error:
        # Database client errors may include connection details. Never echo credentials.
        message = (
            str(error)
            if isinstance(error, ValueError)
            else (
                f"{type(error).__name__}; check PostgreSQL connectivity, role permissions, "
                "and migration SQL"
            )
        )
        print(f"Payroll database setup failed: {message}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
