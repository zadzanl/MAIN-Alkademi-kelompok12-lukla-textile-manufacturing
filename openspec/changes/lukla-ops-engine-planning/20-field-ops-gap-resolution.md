# 20 — Field Operations Gap Resolution: Sample & Spec R&D Module

**Change:** `lukla-ops-engine-planning`
**Date:** 2026-10-14
**Author:** Gap analysis & resolution pass
**Revision:** 1.0
**Status:** RESOLVED — contracts updated, pending Phase B implementation

---

## Konteks

Analisis alur kerja lapangan industri garmen dan tekstil mengidentifikasi tiga gap operasional kritis pada modul **Sample & Time Study (View 02)** yang tidak tercakup oleh kontrak API awal (69 operation IDs). Meskipun infrastruktur inti (versioning, anti-kontaminasi, immutable ledger) sudah solid, Tim Sample/Adis di lapangan tidak akan bisa menggunakan sistem secara efektif tanpa ketiga kapabilitas ini.

Gap ini ditemukan dengan membandingkan endpoint yang ada terhadap alur kerja fisik nyata: dari penerimaan Tech Pack hingga konversi ke order produksi massal.

---

## Gap 1 — BOM per Revisi Tidak Terstruktur

### Masalah

`spec_json` di tabel `sample_revisions` menyimpan seluruh spesifikasi sebagai JSONB blob. Tim Sample tidak bisa menambah/menghapus item material individual tanpa mengirim ulang seluruh blob. Frontend tidak bisa merender tabel BOM yang bisa di-edit baris per baris (standar kerja lapangan).

Di industri, setiap revisi punya BOM yang berbeda. v1 bisa memakai kain A estimasi 1.8m, v2 ganti ke kain B 2.1m karena desain berubah. Perbedaan ini harus terekam dan bisa dibandingkan antar revisi.

### Solusi yang Diterapkan

**Database** — tabel baru `sample_bom_items`:
- Kolom kunci: `sku`, `material_description`, `quantity`, `unit`, `category`, `supplier_ref`, `sort_order`
- Category enum: `MAIN_FABRIC | LINING | INTERLINING | TRIM | ACCESSORY | THREAD | OTHER`
- Constraint: `unique(sample_revision_id, sku)` — satu SKU tidak bisa duplikat dalam satu revisi
- Trigger: locked revision menolak insert/update/delete

**API** — 5 endpoint baru (tag: `samples-rates`, view: `VIEW-02`):

| Operation | Method | Path |
|---|---|---|
| `listBomItems` | GET | `/samples/{id}/revisions/{revId}/bom` |
| `addBomItem` | POST | `/samples/{id}/revisions/{revId}/bom` |
| `updateBomItem` | PUT | `/samples/{id}/revisions/{revId}/bom/{itemId}` |
| `removeBomItem` | DELETE | `/samples/{id}/revisions/{revId}/bom/{itemId}` |
| `getSmvSummary` | GET | `/samples/{id}/revisions/{revId}/smv-summary` |

**Endpoint `getSmvSummary`** adalah endpoint agregasi yang menggabungkan data BOM (komponen) dengan data time study untuk menghasilkan tabel SMV per komponen dan total SMV artikel. Field `completionStatus` per komponen (`COMPLETE | MISSING | PARTIAL`) memungkinkan Tim Sample mengetahui komponen mana yang belum diukur sebelum sample di-approve.

**Invariant kritis:** BOM item hanya bisa dihapus (hard delete) saat revision masih `DRAFT` atau `SUBMITTED`. Setelah locked, riwayat material tidak bisa diubah.

---

## Gap 2 — Model Stopwatch Tidak Mencerminkan Time Study Industri

### Masalah

`POST /time-studies` menerima `durationMs` sebagai input langsung — pengguna harus menghitung durasi sendiri lalu menginput angka. Ini bukan cara kerja lapangan.

Di industri, satu komponen diukur **3–10 kali** (observasi berulang) oleh orang yang berdiri di sebelah penjahit dengan stopwatch. Hasilnya dirata-rata dengan mempertimbangkan **rating factor** (apakah penjahit yang diukur lebih cepat atau lebih lambat dari operator standar) dan **allowance** (waktu istirahat, personal, fatigue — umumnya 10–20%). Proses ini menghasilkan **SMV (Standard Minute Value)**, bukan sekadar rata-rata waktu mentah.

Tanpa model ini, fitur stopwatch digital hanya menjadi timer, bukan alat time study profesional.

### Solusi yang Diterapkan

**Database** — 2 tabel baru + 1 tabel diupdate:

- `time_study_sessions`: satu sesi per `(tenant_id, sample_revision_id, component_code)` yang OPEN pada satu waktu. Status: `OPEN | FINALIZED | ABANDONED`.
- `time_study_observations`: setiap tekan STOP menghasilkan satu baris. Field: `observed_duration_ms`, `rating_factor` (50–150, default 100), `exclude_flag`, `sequence_no`.
- `time_studies`: ditambah kolom `session_id uuid NULL` — diisi saat record diturunkan dari sesi finalized, null untuk direct-entry legacy.

**API** — 6 endpoint baru (tag: `samples-rates`, view: `VIEW-02`):

| Operation | Method | Path |
|---|---|---|
| `createTimeStudySession` | POST | `/time-study-sessions` |
| `addTimeStudyObservation` | POST | `/time-study-sessions/{id}/observations` |
| `excludeObservation` | POST | `/time-study-sessions/{id}/observations/{obsId}/exclude` |
| `finalizeTimeStudySession` | POST | `/time-study-sessions/{id}/finalize` |
| `abandonTimeStudySession` | POST | `/time-study-sessions/{id}/abandon` |
| `listTimeStudySessions` | GET | `/samples/{id}/revisions/{revId}/time-study-sessions` |

**Alur kerja lapangan yang kini didukung:**
```
1. Tim Sample buka komponen "Jahit Kerah" → tap createTimeStudySession
2. Penjahit mulai → tap addObservation saat selesai (durasi terekam)
3. Ulangi 5–8 kali
4. Jika ada outlier (penjahit tersandung) → excludeObservation dengan alasan
5. tap finalizeSession → sistem hitung SMV = mean(basicTime) × (1 + allowanceFraction)
6. SMV tersimpan di time_studies, session FINALIZED, tidak bisa diubah
```

**Formula SMV yang diimplementasikan:**
```
basicTime[i] = observedDuration[i] × (ratingFactor[i] / 100)
meanBasicTime = mean(basicTime[] where excludeFlag = false)
SMV = meanBasicTime × (1 + allowanceFraction)
```

**Invariant kritis:**
- Minimal 3 observasi non-excluded sebelum bisa di-finalize (untuk validitas statistik)
- Hanya satu OPEN session per (revision, component) — mencegah pengukuran ganda yang tidak disengaja
- Session ABANDONED tidak menghasilkan time study record, tapi observasinya tetap ada di audit

---

## Gap 3 — Tidak Ada Dokumentasi Konteks Revisi

### Masalah

Setiap `createSampleRevision` tidak punya cara untuk menyimpan **mengapa** revisi dibuat. Tanpa ini, riwayat versioning tidak berguna — ada 5 versi tapi tidak ada yang tahu apa yang berubah antara v2 dan v3.

Selain itu, Tech Pack (dokumen desain dari klien) tidak bisa dilampirkan secara struktural ke revisi tertentu. File upload umum ada, tapi tidak ada hubungan antara file dan revisi.

Di industri, ini setara dengan kehilangan folder fitting — semua fisik sample tersimpan tapi catatannya hilang.

### Solusi yang Diterapkan

**Database** — 2 tabel baru:

- `sample_revision_notes`: append-only, 4 tipe: `FITTING_NOTE | CHANGE_REASON | CLIENT_FEEDBACK | INTERNAL_MEMO`
- `sample_revision_attachments`: link `file_object_id` ke revisi, 5 tipe: `TECH_PACK | SKETCH | PHOTO | MEASUREMENT_SHEET | OTHER`

**Schema update** — `RevisionRequest` ditambah field `changeReason` (opsional, max 1000 char) sebagai shortcut inline untuk `CHANGE_REASON` note — memudahkan pengisian saat create revision tanpa perlu dua request terpisah.

**API** — 5 endpoint baru (tag: `samples-rates`, view: `VIEW-02`):

| Operation | Method | Path |
|---|---|---|
| `listRevisionNotes` | GET | `/samples/{id}/revisions/{revId}/notes` |
| `addRevisionNote` | POST | `/samples/{id}/revisions/{revId}/notes` |
| `listRevisionAttachments` | GET | `/samples/{id}/revisions/{revId}/attachments` |
| `attachFileToRevision` | POST | `/samples/{id}/revisions/{revId}/attachments` |
| `detachFileFromRevision` | DELETE | `/samples/{id}/revisions/{revId}/attachments/{attachId}` |

**Invariant kritis:**
- Notes adalah append-only — tidak bisa diedit atau dihapus (audit trail)
- Locked revision **masih bisa** menerima notes baru — karena feedback post-approval adalah kejadian bisnis yang valid
- Locked revision **tidak bisa** menerima attachment baru yang di-detach (tapi attach baru masih diizinkan untuk dokumentasi tambahan)
- `MaklonClient` hanya bisa melihat dan menulis `CLIENT_FEEDBACK` — tidak bisa akses `INTERNAL_MEMO`
- `detachFileFromRevision` hanya menghapus link, bukan file aslinya

---

## Ringkasan Perubahan Artefak

| Artefak | Jenis Perubahan |
|---|---|
| `11-database-schema-spec.md` | +5 tabel baru, 1 tabel diupdate (time_studies + session_id) |
| `contracts/openapi.yaml` | +16 paths baru, +15 schemas baru, +1 parameter (RevisionId), RevisionRequest diupdate |

**Total operation IDs setelah patch: 85** (sebelumnya 69)

---

## Mapping ke Skenario Pengujian Slide 09

Skenario 4 dari slide 09: *"Sample direvisi dari v1 ke v2, lalu menjadi order massal skema Semi-CMT. Riwayat spesifikasi v2 terlacak."*

Dengan gap-fix ini, skenario tersebut sekarang fully traceable:

```
v1 dibuat → BOM v1 diisi → Time study v1 diukur (stopwatch sessions) → 
Fitting notes v1 dicatat → Tech Pack v1 dilampirkan →

Feedback klien masuk (CLIENT_FEEDBACK note) →

v2 di-clone dari v1 → changeReason diisi "Kerah diperlebar 1.5cm" →
BOM v2 diupdate (kain berubah) → Time study v2 diukur ulang →
SMV Summary v2 digenerate → v2 di-approve dengan evidence file →
v2 di-lock → convertSampleToOrder ke order Semi-CMT

Seluruh history v1 tetap immutable dan dapat di-query kapanpun.
```

---

## Catatan Implementasi untuk Phase B

1. **BOM vs spec_json**: Field `spec_json` di `sample_revisions` tidak dihapus — masih digunakan untuk data spesifikasi jahitan (komponen seam type, stitch notes). BOM adalah entitas terpisah yang mewakili material, bukan operasi jahit.

2. **SMV formula**: Method `MEDIAN` adalah alternatif untuk lingkungan di mana distribusi waktu sangat skewed (satu penjahit sangat berbeda dari yang lain). Implementasinya sama tapi menggunakan median dari basicTime[] alih-alih mean.

3. **Rating factor 100**: Untuk factory Lukla yang tidak memakai industrial engineering formal, rating factor 100 (default) pada semua observasi menghasilkan SMV = mean observasi × (1 + allowance) — cukup praktis tanpa pelatihan IE khusus.

4. **Migrasi**: Tabel baru ini masuk setelah M003 (samples/revisions) dalam urutan migrasi yang sudah ditetapkan di `11-database-schema-spec.md` section 9. Tidak ada migrasi data untuk records lama — `session_id` nullable secara retroaktif.
