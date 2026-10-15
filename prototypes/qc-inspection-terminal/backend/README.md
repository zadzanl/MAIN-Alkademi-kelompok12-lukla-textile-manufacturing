# QC Inspection Terminal Backend (prototype)

In-memory FastAPI prototype. **Tidak** membaca/menulis PostgreSQL apapun.
Semua data berasal dari fixture berlabel `FIXTURE` (lihat
`src/utils/seed_fixtures.py`).

## Tujuan

Mendemonstrasikan alur minimum **QC Inspection Terminal**:
1. Petugas mencari nomor serial unit garmen.
2. Petugas mencatat hasil `PASS`, `REPAIR`, atau `REJECT`.
3. Riwayat setiap unit dapat ditelusuri (append-only).
4. State transisi dijaga: unit `MENUNGGU_QC` ≠ `PASS`.
5. `REPAIR` dan `REJECT` TIDAK otomatis memicu kredit upah / bonus / potongan.

## Batasan yang SANGAT PENTING

- **Bukan production data.** Serial seperti `U-501` adalah fixture.
- **Tidak menyentuh** `openspec/changes/lukla-ops-engine-planning/**`.
- **Tidak menyentuh** `prototypes/sampling-spec-rnd/**` atau prototype tim lain.
- Kontrak target `contracts/openapi.yaml` hanya dipakai sebagai **acuan semantik**,
  endpoint di-prototype ini mirror operation ID-nya dengan beberapa perluasan
  berlabel `prototype-only`.

## Cara Menjalankan

```powershell
cd prototypes\qc-inspection-terminal\backend
.\run_backend.bat
# atau:
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8010
```

Backend akan listen di `http://127.0.0.1:8010`.
API root: `http://127.0.0.1:8010/api/qc-inspection-terminal`

## Cara Menjalankan Tes

```powershell
cd prototypes\qc-inspection-terminal\backend
powershell -ExecutionPolicy Bypass -File .\test_endpoints.ps1
```

Backend HARUS sudah jalan sebelum tes.

## Referensi Kontrak (tidak boleh diedit)

- `openspec/changes/lukla-ops-engine-planning/specs/quality-control-and-inspection/spec.md`
- `openspec/changes/lukla-ops-engine-planning/contracts/openapi.yaml` (line 356 `POST /qc-inspections`)
- `openspec/changes/lukla-ops-engine-planning/11-database-schema-spec.md` §3 (tabel QC)
- `openspec/changes/lukla-ops-engine-planning/19-business-defaults-register.md` (semua OQ-1..9 status `UNRESOLVED / PRODUCTION_BLOCKED`)
- `openspec/changes/lukla-ops-engine-planning/04-rbac-matrix.md` (role QC Inspector)
