# 00 — Source Deconstruction & Traceability Register

**Change:** `lukla-ops-engine-planning`
**Date:** 2026-10-12
**Author:** Phase 0 executor (Assistant)
**Purpose:** Single source of truth for all later documents (BRD, feature map, PRD, RBAC matrix, data-flow, acceptance tests). Every later requirement must trace back to an entry in this register. Transcription errors here propagate everywhere — rigor level: high.

## Provenance rules

- Indonesian source text is transcribed **faithfully** (no translation in this file). Extraction annotations may be in English.
- Every extracted item is tagged with its source slide: `[slide XX]`.
- Slides 01 and 08 exist **only as chat attachments** (no photo on disk). Their source is the orchestrator's verified transcription, tagged `[slide 01 — chat attachment]` / `[slide 08 — chat attachment]`. Originals requested from user (non-blocking).
- Words that could not be read with confidence from angled/glared photos are marked `[illegible?]` — never guessed.
- Duplicate/re-photographed views of the same slide are merged; nothing is double-counted.
- **Extraction only — no interpretation.** Content absent from the slides is recorded as `UNRESOLVED - not in source`, never invented.

## Source inventory

| Photo file (`openspec/artifacts/slide-photos/`) | Slide | Content |
|---|---|---|
| `WhatsApp Image 2026-10-12 at 10.40.54.jpeg` | 00 | Cover |
| `WhatsApp Image 2026-10-12 at 10.40.54b.jpeg` | 02b | Arsitektur Solusi: Platform Sentral |
| `WhatsApp Image 2026-10-12 at 10.40.54c.jpeg` | 05 | Inspeksi QC & Bonus Pool 3 Arah |
| `WhatsApp Image 2026-10-12 at 10.40.55.jpeg` | 02 | Masalah Utama |
| `WhatsApp Image 2026-10-12 at 10.40.55b.jpeg` | 02c | Solusi: Platform Operasional Terpadu |
| `WhatsApp Image 2026-10-12 at 10.40.55c.jpeg` | 04b | Alur Data Terintegrasi |
| `WhatsApp Image 2026-10-12 at 10.40.56.jpeg` | 03 | Alur Operasional 6 Fase |
| `WhatsApp Image 2026-10-12 at 10.40.56b.jpeg` | 04 | Matriks RBAC — 8 Peran |
| `WhatsApp Image 2026-10-12 at 10.40.56c.jpeg` | 06 | Tracking Output 30 Menit & Line Dinamis |
| `WhatsApp Image 2026-10-12 at 10.40.56d.jpeg` | 07 | Mesin Payroll Fleksibel |
| `WhatsApp Image 2026-10-12 at 10.40.57.jpeg` | 09 | Closing: Tujuan Sistem & 4 Skenario Pengujian |
| *(chat attachment only)* | 01 | Konteks Bisnis & Skema Maklon |
| *(chat attachment only)* | 08 | Layar Tampilan Utama — 6 UI Views |

---

## Slide 00 — Cover

**Provenance:** photo `10.40.54.jpeg` — viewed 2026-10-12. Straight-on shot, legible.

### Transcription

- Title: **"Sistem Manajemen Produksi & Payroll Konveksi"** `[slide 00]`
- Subtitle: **"Lukla Manufacturing × Snøhund"** `[slide 00]`
- Supporting line: **"Lukla Operations Engine"** `[slide 00]`
- Footer/badge text (small print, partially readable): `[illegible?]` — event/presenter attribution not transcribed with confidence. `[slide 00]`

### Extraction

- **Entities:** Lukla Manufacturing (factory), Snøhund (internal brand). `[slide 00]`
- **Scope signal:** system covers *produksi* (production management) AND *payroll* for a *konveksi* (garment/convection) business. `[slide 00]`
- **FR IDs found:** none.
- **Business rules:** none.
- **Actors/roles:** none.
- **Numbers:** none.
- **UI elements:** none.

---

## Slide 01 — Konteks Bisnis & Skema Maklon

**Provenance:** `[slide 01 — chat attachment]` — no photo on disk; orchestrator's verified transcription is the source.

### Transcription (orchestrator-verified)

"Konteks Bisnis & Skema Maklon. Lukla Manufacturing mengoperasikan fasilitas produksi konveksi di Ciwidey dengan kapasitas dinamis hingga ±70 mesin jahit. Fasilitas ini melayani brand internal Snøhund sekaligus klien maklon B2B secara paralel. Setiap order ditangani di bawah satu dari tiga skema kerja sama yang menentukan siapa menyediakan bahan baku."

Three scheme boxes:

1. **CMT (Cut, Make, Trim)** — klien menyediakan seluruh bahan baku; Lukla menyediakan jasa cutting, jahit, dan finishing. `[slide 01 — chat attachment]`
2. **Semi-CMT** — klien menyediakan bahan utama; Lukla menyediakan bahan pendukung dan aksesoris. `[slide 01 — chat attachment]`
3. **CMT + Bahan (Full Package)** — Lukla menyediakan seluruh bahan baku dan jasa produksi; digunakan juga untuk order internal brand Snøhund. `[slide 01 — chat attachment]`

### Extraction

- **Numbers:** ±70 mesin jahit (dynamic capacity, scale context — not a hard cap). `[slide 01 — chat attachment]`
- **Location:** Ciwidey. `[slide 01 — chat attachment]`
- **Business rules:**
  - Factory serves internal brand Snøhund AND B2B maklon clients in parallel. `[slide 01 — chat attachment]`
  - Every order runs under exactly one of three cooperation schemes, which determines who supplies raw material. `[slide 01 — chat attachment]`
- **Domain terms:** maklon, CMT, Semi-CMT, Full Package (CMT + Bahan), bahan baku, bahan pendukung/aksesoris, konveksi.
- **FR IDs found:** none.
- **Actors/roles:** klien maklon B2B (implied), brand internal Snøhund.
- **UI elements:** none.

---

## Slide 02 — Masalah Utama

**Provenance:** photo `10.40.55.jpeg` — viewed 2026-10-12. Slight angle; body text readable, some small badge text marginal.

### Transcription

- Title: **"Masalah Utama"** `[slide 02]`
- Three pain-point blocks:
  1. **Kontaminasi silang bahan antar klien** — bahan titipan milik klien berbeda tercampur di gudang/produksi; risiko pemakaian bahan klien A untuk order klien B. Badge: **FR-6.2**. `[slide 02]`
  2. **Payroll borongan manual** — perhitungan gaji borongan penjahit dilakukan manual; lambat dan rawan kesalahan. Badge: **FR-10**. `[slide 02]`
  3. **Penelusuran revisi sample sulit** — riwayat revisi versi sample tidak terlacak; spesifikasi versi yang disetujui sulit ditelusuri saat order massal. Badges: **FR-3.1**, **FR-4.1**. `[slide 02]`
- Fine print under blocks (small): `[illegible?]` in places — not transcribed where unreadable. `[slide 02]`

### Extraction

- **FR IDs found:** FR-6.2 `[slide 02]`, FR-10 `[slide 02]`, FR-3.1 `[slide 02]`, FR-4.1 `[slide 02]`.
- **Business rules:**
  - Cross-client material contamination is a named risk the system must prevent. `[slide 02]`
  - Manual piece-rate payroll is a named pain (slow, error-prone). `[slide 02]`
  - Sample revision traceability is a named pain. `[slide 02]`
- **Actors/roles:** none named explicitly.
- **Numbers:** none.
- **UI elements:** none.

---

## Slide 02b — Arsitektur Solusi: Platform Sentral

**Provenance:** photo `10.40.54b.jpeg` — viewed 2026-10-12. Diagram slide; box labels readable, connector labels small.

### Transcription

- Title: **"Arsitektur Solusi: Platform Sentral"** `[slide 02b]`
- Core statement: satu **platform sentral** melayani seluruh klien dengan arsitektur **multi-tenant** — **data terpisah per klien**. `[slide 02b]`
- Diagram boxes (as readable): platform sentral di tengah; klien/tenant di sekelilingnya; penekanan isolasi data antar klien. `[slide 02b]`
- Small connector/caption text: partially `[illegible?]`. `[slide 02b]`

### Extraction

- **Business rules:**
  - Single central platform; multi-tenant architecture. `[slide 02b]`
  - Tenant data isolation: data separated per client. `[slide 02b]`
- **FR IDs found:** none visible on this slide (multi-tenant concept here supports FR-1.1 defined on slide 02c — recorded as observation, not a new FR).
- **Actors/roles:** klien (tenants).
- **Numbers:** none.
- **UI elements:** none (architecture diagram only).

---

## Slide 02c — Solusi: Platform Operasional Terpadu

**Provenance:** photo `10.40.55b.jpeg` — viewed 2026-10-12. Legible.

### Transcription

- Title: **"Solusi: Platform Operasional Terpadu"** `[slide 02c]`
- Three solution pillars (with FR badges):
  1. **Multi-tenant** — satu platform, banyak klien, data terisolasi per klien. Badge: **FR-1.1**. `[slide 02c]`
  2. **RBAC** — kontrol akses berbasis peran untuk seluruh pengguna pabrik dan klien. Badge: **FR-2.1**. `[slide 02c]`
  3. **Audit trail** — jejak audit atas aksi/riwayat data. Badge: **FR-3.1**. `[slide 02c]`

### Extraction

- **FR IDs found:** FR-1.1 `[slide 02c]`, FR-2.1 `[slide 02c]`, FR-3.1 `[slide 02c]`.
- **Business rules:**
  - FR-1.1: multi-tenant platform with per-client data isolation. `[slide 02c]`
  - FR-2.1: role-based access control. `[slide 02c]`
  - FR-3.1: audit trail over actions/history. `[slide 02c]`
- **Actors/roles:** "pengguna pabrik dan klien" (factory users and clients) — generic.
- **Numbers:** none.
- **UI elements:** none.

---

## Slide 03 — Alur Operasional 6 Fase

**Provenance:** photo `10.40.56.jpeg` — viewed 2026-10-12. Flow diagram; phase labels readable, per-phase FR badges mostly readable.

### Transcription

- Title: **"Alur Operasional 6 Fase"** `[slide 03]`
- Six phases in sequence, with FR ranges mapped to phases:
  1. **Fase 1 — Onboarding Klien & Order** — registrasi klien, skema maklon (CMT / Semi-CMT / Full Package), penerimaan order. FR badges: **FR-1.x** (FR-1.1, FR-1.4 observed). `[slide 03]`
  2. **Fase 2 — Sample & Time Study** — pembuatan sample, revisi berversi (v1, v2, …), time study per komponen. FR badges: **FR-3.1, FR-4.1**. `[slide 03]`
  3. **Fase 3 — Gudang** — penerimaan bahan (termasuk bahan titipan klien), stok multi-klien. FR badge: **FR-5**. `[slide 03]`
  4. **Fase 4 — Cutting** — pemotongan bahan massal. FR badge: **FR-6** (dengan guardrail **FR-6.2** kontaminasi silang). `[slide 03]`
  5. **Fase 5 — Produksi** — tracking output per 30 menit, alokasi line dinamis. FR badges: **FR-7.x**. `[slide 03]`
  6. **Fase 6 — QC & Payroll** — inspeksi QC, bonus pool, payroll borongan. FR badges: **FR-8.x, FR-9.x, FR-10.x**. `[slide 03]`
- Some per-phase sub-bullets are small print: `[illegible?]` where unreadable. `[slide 03]`

### Extraction

- **FR IDs found:** FR-1.1 `[slide 03]`, FR-1.4 `[slide 03]`, FR-3.1 `[slide 03]`, FR-4.1 `[slide 03]`, FR-5 `[slide 03]`, FR-6 `[slide 03]`, FR-6.2 `[slide 03]`, FR-7.x range `[slide 03]`, FR-8.x range `[slide 03]`, FR-9.x range `[slide 03]`, FR-10.x range `[slide 03]`.
- **Business rules:**
  - Operational flow is exactly 6 sequential phases: Onboarding/Order → Sample & Time Study → Gudang → Cutting → Produksi → QC & Payroll. `[slide 03]`
  - Order onboarding captures the maklon scheme per order. `[slide 03]`
- **Actors/roles:** none named on this slide.
- **Numbers:** 6 fase; sample versions v1, v2.
- **UI elements:** none.

---

## Slide 04 — Matriks RBAC: 8 Peran Pengguna

**Provenance:** photo `10.40.56b.jpeg` — viewed 2026-10-12. Dense table; role names and column headers readable; some IZIN/PEMBATASAN cell text small and partially readable — uncertain cells marked.

### Transcription

- Title: **"Matriks RBAC — 8 Peran Pengguna"** `[slide 04]`
- Table columns: **Peran | IZIN | PEMBATASAN**. `[slide 04]`
- Eight roles (rows), as readable:
  1. **Owner** — IZIN: akses penuh seluruh modul `[illegible? — full cell text not confirmed]`; PEMBATASAN: riwayat terkunci / tidak dapat mengubah histori (locked history) `[illegible? — wording partially readable]`. `[slide 04]`
  2. **Kepala Operasional** — IZIN: persetujuan order, monitoring operasional `[illegible?]`; PEMBATASAN: `[illegible?]`. `[slide 04]`
  3. **Kepala Produksi** — IZIN: pengelolaan produksi/line `[illegible?]`; PEMBATASAN: `[illegible?]`. `[slide 04]`
  4. **Mandor** — IZIN: input output 30 menit per penjahit `[illegible?]`; PEMBATASAN: `[illegible?]`. `[slide 04]`
  5. **Penjahit** — IZIN: melihat output/target sendiri `[illegible?]`; PEMBATASAN: tidak dapat menginput untuk penjahit lain `[illegible?]`. `[slide 04]`
  6. **Staff Gudang** — IZIN: penerimaan/pengeluaran bahan, stok `[illegible?]`; PEMBATASAN: `[illegible?]`. `[slide 04]`
  7. **QC / Inspektor** — IZIN: pencatatan hasil inspeksi (lolos/repair/scrap), kategori defect `[illegible?]`; PEMBATASAN: `[illegible?]`. `[slide 04]`
  8. **Klien B2B (Portal)** — IZIN: melihat progres order sendiri via portal `[illegible?]`; PEMBATASAN: hanya data klien sendiri (isolasi tenant) `[illegible?]`. `[slide 04]`

> **Legibility warning:** the RBAC table cell text is the smallest print in the deck. Role names, column headers (IZIN/PEMBATASAN), and the 8-role count are confirmed readable. Individual cell contents above are best-effort readings and are marked `[illegible?]`; the cell-level permission/restriction wording MUST be re-verified against a sharper source before `04-rbac-matrix.md` is finalized. This is flagged as an extraction risk, not filled by invention.

### Extraction

- **Actors/roles (8, confirmed):** Owner, Kepala Operasional, Kepala Produksi, Mandor, Penjahit, Staff Gudang, QC/Inspektor, Klien B2B (Portal). `[slide 04]`
- **Business rules:**
  - RBAC matrix has exactly 8 roles with explicit IZIN (permissions) and PEMBATASAN (restrictions) columns. `[slide 04]`
  - Owner has a locked-history restriction (wording partially legible). `[slide 04]`
- **FR IDs found:** none badged on this slide (supports FR-2.1).
- **Numbers:** 8 peran.
- **UI elements:** none.

---

## Slide 04b — Alur Data Terintegrasi

**Provenance:** photo `10.40.55c.jpeg` — viewed 2026-10-12. Flow diagram; stage labels readable, some edge labels small.

### Transcription

- Title: **"Alur Data Terintegrasi"** `[slide 04b]`
- Integrated data flow across stages: **Order → Gudang → Cutting → Produksi → QC → Payroll**. `[slide 04b]`
- Status/transition labels observed on the flow (as readable): **"Menunggu QC"** (status between Produksi and QC); other edge labels partially `[illegible?]`. `[slide 04b]`
- Flow shows data from upstream stages feeding Payroll (output terverifikasi → perhitungan gaji). `[slide 04b]`

### Extraction

- **Business rules:**
  - Single integrated data flow: Order → Gudang → Cutting → Produksi → QC → Payroll. `[slide 04b]`
  - Status `Menunggu QC` exists as a transition state between production output and QC inspection. `[slide 04b]`
  - Payroll consumes verified production/QC data (no separate manual input implied). `[slide 04b]`
- **FR IDs found:** none badged (diagram supports FR-5/FR-6/FR-7/FR-8/FR-10 chain).
- **Actors/roles:** none.
- **Numbers:** none.
- **UI elements:** none.

---

## Slide 05 — Inspeksi QC & Bonus Pool 3 Arah

**Provenance:** photo `10.40.54c.jpeg` — viewed 2026-10-12. Legible; formula block readable.

### Transcription

- Title: **"Inspeksi QC & Bonus Pool 3 Arah"** `[slide 05]`
- QC inspection block:
  - Pencatatan status pemeriksaan produk: **lolos / repair / scrap**. Badge: **FR-8.1**. `[slide 05]`
  - Pemilihan **kategori defect** (cacat) saat status repair/scrap. Badge: **FR-8.2**. `[slide 05]`
  - Pengalihan status barang ke rute tindakan yang sesuai (routing per status). `[slide 05]`
- Bonus pool block:
  - **Bonus pool QC** dihitung dari output yang lolos QC. Badge: **FR-9.1**. `[slide 05]`
  - Pembagian bonus **3 arah — dibagi 3 (÷3)**: **2 mandor + 1 kepala operasional**. Badge: **FR-9.2**. `[slide 05]`

### Extraction

- **FR IDs found:** FR-8.1 `[slide 05]`, FR-8.2 `[slide 05]`, FR-9.1 `[slide 05]`, FR-9.2 `[slide 05]`.
- **Business rules:**
  - FR-8.1: QC result status is one of lolos / repair / scrap. `[slide 05]`
  - FR-8.2: defect category is selectable for failed items. `[slide 05]`
  - FR-9.1: a QC bonus pool is derived from QC-passed output. `[slide 05]`
  - FR-9.2: bonus pool split exactly 3 ways — 2 mandor + 1 kepala operasional (÷3 fixed on slide). `[slide 05]`
- **Actors/roles:** QC/inspektor (implied), mandor ×2, kepala operasional ×1.
- **Numbers:** ÷3; 2 mandor; 1 kepala operasional.
- **UI elements:** status selection (lolos/repair/scrap), defect category picker, routing action.

---

## Slide 06 — Tracking Output 30 Menit & Line Dinamis

**Provenance:** photo `10.40.56c.jpeg` — viewed 2026-10-12. Legible; example numbers readable.

### Transcription

- Title: **"Tracking Output 30 Menit"** (subtitle: line dinamis) `[slide 06]`
- Feature bullets with FR badges:
  - **FR-7.1** — mandor menginput output (pcs) per penjahit **setiap 30 menit** di area pabrik (terminal input sederhana). `[slide 06]`
  - **FR-7.2** — pencatatan output terhubung ke penjahit dan line produksi. `[slide 06]`
  - **FR-7.3** — **line dinamis "tanpa slot kaku"** — jumlah penjahit/line dapat berubah; sistem menyesuaikan tanpa konfigurasi slot tetap. `[slide 06]`
  - **FR-7.4** — akumulasi output terverifikasi sebagai dasar payroll borongan. `[slide 06]`
- Example/callout: skenario penambahan **+5 penjahit** di tengah periode berjalan. `[slide 06]`
- Referensi kapasitas: **±70 mesin jahit** (konteks skala, bukan batas sistem — konsisten dengan "tanpa slot kaku"). `[slide 06]`

### Extraction

- **FR IDs found:** FR-7.1 `[slide 06]`, FR-7.2 `[slide 06]`, FR-7.3 `[slide 06]`, FR-7.4 `[slide 06]`.
- **Business rules:**
  - Output is captured per sewer per 30-minute interval by the mandor. `[slide 06]`
  - Lines are dynamic — "tanpa slot kaku" (no rigid slots); headcount can change mid-period. `[slide 06]`
  - Verified 30-min outputs feed piece-rate payroll. `[slide 06]`
- **Actors/roles:** mandor (input), penjahit (subject of output).
- **Numbers:** 30 menit; +5 penjahit; ±70 mesin jahit.
- **UI elements:** large, simple, touch-friendly input terminal (cross-ref slide 08 view 04).

---

## Slide 07 — Mesin Payroll Fleksibel

**Provenance:** photo `10.40.56d.jpeg` — viewed 2026-10-12. Legible; formula blocks readable.

### Transcription

- Title: **"Mesin Payroll Fleksibel"** `[slide 07]`
- Four payroll formulas with FR badges:
  - **FR-10.1** — gaji **borongan mingguan** penjahit dihitung dari akumulasi **output 30 menit terverifikasi**; periode payroll mingguan berakhir **Sabtu (Saturday)**. `[slide 07]`
  - **FR-10.2** — **uang makan** = **10–15%** dari **ongkos jahit**; persentase diinput **manual per periode**. `[slide 07]`
  - **FR-10.3** — pembagian **bonus pool QC ÷3** → **2 mandor + 1 kepala operasional** (konsisten dengan slide 05 / FR-9.2). `[slide 07]`
  - **FR-10.4** — alokasi **overhead operasional pabrik bulanan ÷ total unit** yang diproduksi pada periode tersebut. `[slide 07]`
- Tidak ada konten BPJS / pajak / lembur pada slide ini. `[slide 07]`

### Extraction

- **FR IDs found:** FR-10.1 `[slide 07]`, FR-10.2 `[slide 07]`, FR-10.3 `[slide 07]`, FR-10.4 `[slide 07]`.
- **Business rules (exact formulas):**
  - FR-10.1: weekly piece-rate wage from verified 30-min outputs; weekly period ends Saturday. `[slide 07]`
  - FR-10.2: meal allowance = 10–15% of ongkos jahit; percentage set manually per period. `[slide 07]`
  - FR-10.3: QC bonus pool ÷3 → 2 mandor + 1 kepala operasional. `[slide 07]`
  - FR-10.4: monthly factory overhead ÷ total units produced in the period. `[slide 07]`
- **Actors/roles:** penjahit (payee), mandor ×2 + kepala operasional ×1 (bonus recipients).
- **Numbers:** 10–15%; ÷3; weekly (Sabtu); monthly overhead.
- **UI elements:** payroll workspace (cross-ref slide 08 view 06).

---

## Slide 08 — Layar Tampilan Utama (Minimum Required UI Views)

**Provenance:** `[slide 08 — chat attachment]` — no photo on disk; orchestrator's verified transcription is the source. One phrase was partially obscured on the original attachment and is marked `[illegible?]` per the orchestrator.

### Transcription (orchestrator-verified)

"Layar Tampilan Utama — Minimum Required UI Views. Enam tampilan utama yang wajib ada pada sistem Lukla Operations Engine."

1. **(01) Dashboard Utama Operasional** — overview kondisi pabrik real-time: line aktif, jumlah penjahit bertugas, progres order per klien, grafik kecepatan produksi interval 30 menit. `[slide 08 — chat attachment]`
2. **(02) Sample & Time Study Tracker** — pengelolaan revisi versi sample dengan versioning v1, v2, dst; stopwatch digital untuk time study per komponen; tabel pencatatan waktu pengerjaan. `[slide 08 — chat attachment]`
3. **(03) Gudang Multi-Klien & Stok** — grid inventaris multi-tenant dengan filter per klien; form penerimaan bahan titipan; peringatan ketidakcocokan `[illegible?]` (partially obscured). `[slide 08 — chat attachment]`
4. **(04) Terminal Input 30 Menit** — antarmuka sederhana berukuran besar, touch-friendly; mandor menginput output pcs per penjahit setiap 30 menit di area pabrik. `[slide 08 — chat attachment]`
5. **(05) Terminal Inspeksi QC** — pencatatan status pemeriksaan produk (lolos, repair, scrap); pemilihan kategori defect; pengalihan status barang ke rute tindakan yang sesuai. `[slide 08 — chat attachment]`
6. **(06) Workspace Payroll & Bonus** — penghitungan gaji borongan mingguan penjahit; kalkulasi pembagian bonus QC 3-arah; penghitungan uang makan; rekap alokasi overhead operasional pabrik. `[slide 08 — chat attachment]`

### Extraction

- **UI elements (6 minimum required views, confirmed):** Dashboard Utama Operasional; Sample & Time Study Tracker; Gudang Multi-Klien & Stok; Terminal Input 30 Menit; Terminal Inspeksi QC; Workspace Payroll & Bonus. `[slide 08 — chat attachment]`
- **Business rules:**
  - Dashboard shows real-time factory state incl. 30-minute production-speed graph. `[slide 08 — chat attachment]`
  - Sample tracker uses explicit versioning (v1, v2, …) and per-component time study with digital stopwatch. `[slide 08 — chat attachment]`
  - Warehouse grid is multi-tenant with per-client filter and consignment-material receiving form; mismatch warning present (wording partially obscured). `[slide 08 — chat attachment]`
- **FR IDs found:** none badged (views map to FR-7.x, FR-8.x, FR-9.x, FR-10.x, FR-5).
- **Actors/roles:** mandor (view 04), QC (view 05), payroll/admin (view 06).
- **Numbers:** 6 views; 30 menit interval.

---

## Slide 09 — Closing: Tujuan Sistem & 4 Skenario Pengujian

**Provenance:** photo `10.40.57.jpeg` — viewed 2026-10-12. Legible; scenario blocks readable.

### Transcription

- Title: **"Tujuan Sistem & Skenario Pengujian"** (closing slide) `[slide 09]`
- Tujuan sistem (system goals): platform operasional terpadu multi-tenant untuk produksi & payroll konveksi Lukla Manufacturing `[slide 09]` (summary restatement of deck goals; fine print partially `[illegible?]`).
- **4 Skenario Pengujian (acceptance test scenarios):**
  1. **Penolakan kontaminasi silang** — sistem **menolak** pengeluaran/pemakaian bahan milik Klien A untuk order Klien B (negative path). `[slide 09]`
  2. **Payroll headcount dinamis** — penambahan **+5 penjahit** di tengah minggu berjalan; perhitungan payroll tetap benar. `[slide 09]`
  3. **Bonus pool QC 3000 unit** — output **3000 unit** lolos QC; bonus pool dihitung dan **dibagi 3** (2 mandor + 1 kepala operasional). `[slide 09]`
  4. **Revisi sample v1 → v2 ke order massal Semi-CMT** — sample direvisi dari v1 ke v2, lalu menjadi order massal skema **Semi-CMT** dengan riwayat spesifikasi v2 terlacak. `[slide 09]`

### Extraction

- **Business rules:**
  - The 4 scenarios are acceptance tests (incl. a negative path), not feature descriptions. `[slide 09]`
  - Cross-client contamination must be **rejected** by the system (enforces FR-6.2). `[slide 09]`
  - Payroll must remain correct under mid-week headcount change (+5 penjahit) (exercises FR-7.3, FR-10.1). `[slide 09]`
  - Bonus pool scenario uses exactly 3000 units and ÷3 split (exercises FR-9.1/FR-9.2/FR-10.3). `[slide 09]`
  - Sample revision v1→v2 must carry traceable spec history into a Semi-CMT mass order (exercises FR-3.1, FR-4.1). `[slide 09]`
- **FR IDs found:** none badged (scenarios exercise FR-6.2, FR-7.3, FR-9.x, FR-10.x, FR-3.1, FR-4.1).
- **Actors/roles:** none new.
- **Numbers:** +5 penjahit; 3000 unit; ÷3; v1→v2.
- **UI elements:** none.

---

## Master FR inventory

| FR ID | Slide source(s) | One-line meaning (as stated on slides) |
|---|---|---|
| FR-1.1 | `[slide 02c]`, `[slide 03]` | Multi-tenant platform; data isolated per client |
| FR-1.4 | `[slide 03]` | Client/order onboarding element (badge seen in Fase 1; exact wording not fully legible — see UNRESOLVED) |
| FR-2.1 | `[slide 02c]` | Role-based access control (8 roles per slide 04) |
| FR-3.1 | `[slide 02]`, `[slide 02c]`, `[slide 03]` | Audit trail / traceable history (incl. sample revisions) |
| FR-4.1 | `[slide 02]`, `[slide 03]` | Sample revision tracking / versioning (v1, v2, …) |
| FR-5 | `[slide 03]` | Gudang (warehouse) phase — multi-client stock, consignment receiving (named only; detail not specified) |
| FR-6 | `[slide 03]` | Cutting phase (named only; detail not specified) |
| FR-6.2 | `[slide 02]`, `[slide 03]`, `[slide 09]` | Cross-client contamination guardrail — reject Client A material for Client B order |
| FR-7.1 | `[slide 06]` | Mandor inputs per-sewer output (pcs) every 30 minutes |
| FR-7.2 | `[slide 06]` | Output linked to penjahit and production line |
| FR-7.3 | `[slide 06]` | Dynamic line allocation — "tanpa slot kaku" (no rigid slots) |
| FR-7.4 | `[slide 06]` | Verified output accumulation feeds piece-rate payroll |
| FR-8.1 | `[slide 05]` | QC inspection status: lolos / repair / scrap |
| FR-8.2 | `[slide 05]` | Defect category selection for failed items |
| FR-9.1 | `[slide 05]` | QC bonus pool derived from QC-passed output |
| FR-9.2 | `[slide 05]` | Bonus pool split 3 ways: 2 mandor + 1 kepala operasional |
| FR-10.1 | `[slide 07]` | Weekly borongan wage from verified 30-min outputs; period ends Saturday |
| FR-10.2 | `[slide 07]` | Uang makan = 10–15% of ongkos jahit; % manual per period |
| FR-10.3 | `[slide 07]` | QC bonus pool ÷3 → 2 mandor + 1 kepala operasional |
| FR-10.4 | `[slide 07]` | Monthly factory overhead ÷ total units produced |

**Deck-level reference (no sub-ID):** FR-10 referenced as a whole on `[slide 02]` (payroll pain point).

## Skipped FR numbers — referenced-but-not-defined in source

The following IDs are **not shown on any slide**. They are recorded here as *referenced-but-not-defined in source* (numbering gaps in the deck), **NOT** as gaps to fill:

- **FR-1.2, FR-1.3** — never shown (FR-1.1 and FR-1.4 appear; intermediate numbers absent).
- **FR-2.2+** — only FR-2.1 shown.
- **FR-3.2+** — only FR-3.1 shown.
- **FR-4.2+** — only FR-4.1 shown.
- **FR-5.x sub-IDs** — only bare FR-5 shown.
- **FR-6.1, FR-6.3+** — only FR-6 and FR-6.2 shown.
- **FR-8.3+, FR-9.3+** — not shown.
- **FR-10.5+** — not shown (and must not be invented: no BPJS/tax/overtime content).

## UNRESOLVED - not in source

Everything the deck names but never specifies:

1. **FR-5 (Gudang) detail** — named in the 6-phase flow `[slide 03]` and data flow `[slide 04b]`, and view 03 `[slide 08 — chat attachment]` shows a multi-client inventory grid + consignment receiving form + mismatch warning. No slide specifies inventory transactions, stock adjustment rules, or stok opname behavior. **UNRESOLVED - not in source.**
2. **FR-6 (Cutting) detail** — named as a phase `[slide 03]` and flow stage `[slide 04b]`; only the contamination guardrail FR-6.2 `[slide 02]` is specified. No slide specifies cutting batches, markers, or wastage rules. **UNRESOLVED - not in source.**
3. **FR-1.4 exact wording** — badge observed in Fase 1 of `[slide 03]` but its definition text is not fully legible on the photo and appears nowhere else. **UNRESOLVED - not in source (partially legible badge).**
4. **RBAC cell-level wording (slide 04)** — 8 roles and IZIN/PEMBATASAN columns confirmed; individual cell text only partially legible (see slide 04 section). **UNRESOLVED - pending sharper source.**
5. **Bonus pool ÷3 configurability** — split is fixed at ÷3 (2 mandor + 1 kepala operasional) on `[slide 05]`/`[slide 07]`; whether recipient count is configurable is never stated. **UNRESOLVED - not in source (open question, do not decide).**
6. **Uang makan base definition** — FR-10.2 states 10–15% of "ongkos jahit"; the deck never defines ongkos jahit computation vs. ongkos potong. **UNRESOLVED - not in source.**
7. **Slide 00 footer attribution** and small-print captions on slides 02/02b/03/04b/09 marked `[illegible?]`. **UNRESOLVED - illegible in source photos.**

## Contradictions / ambiguities

- **Ambiguity (not contradiction):** FR-9.2 (slide 05) and FR-10.3 (slide 07) describe the same ÷3 bonus split under two IDs — treated as one rule referenced from two features, not two rules.
- **Ambiguity:** "±70 mesin jahit" appears as scale context `[slide 01 — chat attachment]`, `[slide 06]`; slide 06's "tanpa slot kaku" confirms it is NOT a system cap. No contradiction.
- Otherwise: **none found.**
