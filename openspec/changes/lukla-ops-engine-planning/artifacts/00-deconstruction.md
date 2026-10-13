# 00 — Source Deconstruction & Traceability Register

**Change:** `lukla-ops-engine-planning`
**Date:** 2026-10-12
**Author:** Phase 0 executor (Assistant)
**Revision:** 4 (2026-10-12) — Phase 0-R: slides 02, 02b, 05, 06 re-transcribed verbatim from the high-resolution PDF page renders (`pdf-image/`), closing review-2 criticals C-01..C-04; forced downstream corrections applied to the master FR inventory, UNRESOLVED list, and Contradictions section. (Revision 3: slide 07 re-anchored to the orchestrator's transcription of the legible chat attachment.)
**Purpose:** Single source of truth for all later documents (BRD, feature map, PRD, RBAC matrix, data-flow, acceptance tests). Every later requirement must trace back to an entry in this register. Transcription errors here propagate everywhere — rigor level: high.

## Provenance rules

- Indonesian source text is transcribed **faithfully** (no translation in this file). Extraction annotations may be in English.
- Every extracted item is tagged with its source slide: `[slide XX]`.
- **Slides 02c and 07 have NO photo on disk.** All 11 on-disk photos were re-viewed on 2026-10-12; none shows slide 02c or slide 07. Slide 02c has no chat attachment; its unsupported FR-2.1 ID remains `[assumption]`.
- Slide 07 is legible in a chat attachment; its FR-10.1–10.4 text is tagged `[slide 07 — chat attachment]`. Originals of slides 02c and 07 requested from user (not a blocker for transcribing slide 07).
- Slides 01 and 08 **ARE on disk** (revision-1 belief that they were chat-only was wrong). Their sections below are transcribed from the photos; the orchestrator's chat-attachment transcriptions are retained as cross-check notes only. Photos win on conflict (no conflicts found — the chat copies matched the photos).
- High-resolution PDF page renders of the deck (`pdf-image/Lukla Operations Engine — SRS Walkthrough - page-0001..0010.jpg`) exist on disk. Revision 4 uses them as the primary source for slides 02, 02b, 05, 06 — printed slide labels verified on each render (page-0003 = slide 02, page-0004 = slide 02b, page-0008 = slide 05, page-0009 = slide 06). The renders are more legible than the WhatsApp photos and win on conflict.
- Words that could not be read with confidence are marked `[illegible?]` — never guessed. (Revision 2: all 11 photos proved legible; no material `[illegible?]` spots remain.)
- Duplicate/re-photographed views of the same slide are merged; nothing is double-counted.
- **Extraction only — no interpretation.** Content absent from the slides is recorded as `UNRESOLVED - not in source`, never invented.

## Source inventory

Mapping method: slide number read from the label printed at the top-left of each slide in the photo. All 11 photos re-viewed 2026-10-12.

| Photo file (`openspec/artifacts/slide-photos/`) | Slide | Content |
|---|---|---|
| `WhatsApp Image 2026-10-12 at 10.40.54.jpeg` | 00 | Cover |
| `WhatsApp Image 2026-10-12 at 10.40.54b.jpeg` | 01 | Konteks Bisnis & Skema Maklon |
| `WhatsApp Image 2026-10-12 at 10.40.54c.jpeg` | 02 | Masalah Utama |
| `WhatsApp Image 2026-10-12 at 10.40.55.jpeg` | 02b | Arsitektur Solusi: Platform Sentral |
| `WhatsApp Image 2026-10-12 at 10.40.55b.jpeg` | 03 | Alur Operasional 6 Fase |
| `WhatsApp Image 2026-10-12 at 10.40.55c.jpeg` | 04 | Matriks RBAC: 8 Peran Pengguna |
| `WhatsApp Image 2026-10-12 at 10.40.56.jpeg` | 04b | Alur Data Terintegrasi |
| `WhatsApp Image 2026-10-12 at 10.40.56b.jpeg` | 05 | Inspeksi QC & Bonus Pool 3 Arah |
| `WhatsApp Image 2026-10-12 at 10.40.56c.jpeg` | 06 | Tracking Output 30 Menit & Line Dinamis |
| `WhatsApp Image 2026-10-12 at 10.40.56d.jpeg` | 08 | Layar Tampilan Utama — Minimum Required UI Views |
| `WhatsApp Image 2026-10-12 at 10.40.57.jpeg` | 09 | Closing: Tujuan Sistem & 4 Skenario Pengujian |
| *(no photo on disk)* | 02c | Solusi: Platform Operasional Terpadu — **unavailable** |
| *(no photo on disk; chat attachment only)* | 07 | Mesin Payroll Fleksibel — **chat attachment only** |

---

## Slide 00 — Cover

**Provenance:** photo `10.40.54.jpeg` — re-viewed 2026-10-12. Legible.

### Transcription

- Slide label: **"00 — COVER"** `[slide 00]`
- Title: **"Sistem Manajemen Produksi & Payroll Konveksi"** `[slide 00]`
- Subtitle: **"Lukla Manufacturing × Snøhund"** `[slide 00]`
- Supporting line: **"Lukla Operations Engine"** `[slide 00]`
- Footer left: **"Pitch Deck — Hackathon 2026"**; footer right: **"Confidential — Internal Use Only"** `[slide 00]`

### Extraction

- **Entities:** Lukla Manufacturing (factory), Snøhund (internal brand). `[slide 00]`
- **Scope signal:** system covers *produksi* (production management) AND *payroll* for a *konveksi* (garment/convection) business. `[slide 00]`
- **FR IDs found:** none.
- **Business rules:** none.
- **Actors/roles:** none.
- **Numbers:** none. (No capacity figures on this slide — "±70" appears on slides 01 and 06 only.)
- **UI elements:** none.

---

## Slide 01 — Konteks Bisnis & Skema Maklon

**Provenance:** photo `10.40.54b.jpeg` — re-viewed 2026-10-12. Legible. (Revision 1 believed this slide existed only as a chat attachment; the photo IS on disk. The orchestrator's chat-attachment transcription was cross-checked against the photo and matches; the photo is the primary source.)

### Transcription

- Slide label: **"01 — BUSINESS CONTEXT"**; title: **"Konteks Bisnis & Skema Maklon"** `[slide 01]`
- Lead paragraph: "Lukla Manufacturing mengoperasikan fasilitas produksi konveksi di Ciwidey dengan kapasitas dinamis hingga **±70 mesin jahit**. Fasilitas ini melayani brand internal Snøhund sekaligus klien maklon B2B secara paralel. Setiap order ditangani di bawah satu dari tiga skema kerja sama yang menentukan siapa menyediakan bahan baku." `[slide 01]`
- Three scheme boxes:
  1. **CMT (Cut, Make, Trim)** — "Klien menyediakan seluruh bahan baku. Lukla menyediakan jasa cutting, jahit, dan finishing." `[slide 01]`
  2. **Semi-CMT** — "Klien menyediakan bahan utama. Lukla menyediakan bahan pendukung dan aksesoris." `[slide 01]`
  3. **CMT + Bahan (Full Package)** — "Lukla menyediakan seluruh bahan baku dan jasa produksi. Digunakan juga untuk order internal brand Snøhund." `[slide 01]`

### Extraction

- **Numbers:** ±70 mesin jahit (dynamic capacity, scale context — not a hard cap). `[slide 01]`
- **Location:** Ciwidey. `[slide 01]`
- **Business rules:**
  - Factory serves internal brand Snøhund AND B2B maklon clients in parallel. `[slide 01]`
  - Every order runs under exactly one of three cooperation schemes, which determines who supplies raw material. `[slide 01]`
- **Domain terms:** maklon, CMT, Semi-CMT, Full Package (CMT + Bahan), bahan baku, bahan pendukung/aksesoris, konveksi.
- **FR IDs found:** none.
- **Actors/roles:** klien maklon B2B (implied), brand internal Snøhund.
- **UI elements:** none.

---

## Slide 02 — Masalah Utama

**Provenance:** PDF render `pdf-image/Lukla Operations Engine — SRS Walkthrough - page-0003.jpg` — viewed 2026-10-12 (Phase 0-R, revision 4). Printed slide label verified on the render. Fully legible; supersedes the rev-3 photo-based transcription, which review 2 found invented at detail level (critical C-01).

### Transcription (verbatim, revision 4)

- Slide label: **"02 — PROBLEM STATEMENT"**; title: **"Masalah Utama"**; subtitle: **"Tiga masalah kritis yang dihadapi Lukla Manufacturing saat ini"** `[slide 02]`
- Three pain-point cards:
  1. **Kontaminasi Silang** — "Bahan Klien A terpakai untuk Order Klien B. Stok kacau, kepercayaan klien hilang." Badges: **FR-6.2**, **FR-5**. `[slide 02]`
  2. **Payroll Kompleks & Headcount Dinamis** — "1–70+ penjahit aktif, payroll borongan mingguan + uang makan + bonus QC + overhead. Rentan salah hitung." Badges: **FR-10**, **FR-7**. `[slide 02]`
  3. **Sulit Melacak Revisi** — "Perubahan spesifikasi sampel ke produksi tidak terdokumentasi. Riwayat revisi hilang." Badges: **FR-3.1**, **FR-4.1**. `[slide 02]`
- Footer bar: **"Platform Operasional Terpadu — Lukla Manufacturing"** `[slide 02]`

### Extraction

- **FR IDs found:** FR-6.2 `[slide 02]`, FR-5 `[slide 02]`, FR-10 `[slide 02]`, FR-7 `[slide 02]`, FR-3.1 `[slide 02]`, FR-4.1 `[slide 02]`.
- **Business rules:**
  - Cross-client material contamination is a named pain the system must prevent: Client A material consumed by Client B's order; stated consequences are stock chaos and loss of client trust. `[slide 02]`
  - Payroll complexity under dynamic headcount is a named pain: 1–70+ active sewers; weekly piece-rate payroll plus uang makan plus QC bonus plus overhead; "rentan salah hitung" (prone to miscalculation). `[slide 02]`
  - Sample-to-production spec revision tracking is a named pain: undocumented changes, lost revision history. `[slide 02]`
- **Actors/roles:** none named explicitly.
- **Numbers:** 1–70+ penjahit aktif (headcount range as printed).
- **UI elements:** none.
- **Revision-4 correction notes (critical C-01):** rev 3 mislabeled this slide "MAIN PROBLEM" (actual: "PROBLEM STATEMENT") and invented card titles/bodies (e.g. "Payroll Borongan Manual" / "dilakukan manual" — the actual card is "Payroll Kompleks & Headcount Dinamis"). Rev 3 also dropped the second badge on cards 1 and 2 (FR-5 and FR-7 respectively).

---

## Slide 02b — Arsitektur Solusi

**Provenance:** PDF render `pdf-image/Lukla Operations Engine — SRS Walkthrough - page-0004.jpg` — viewed 2026-10-12 (Phase 0-R, revision 4). Printed slide label verified on the render. Fully legible; supersedes the rev-3 photo-based transcription (critical C-02).

### Transcription (verbatim, revision 4)

- Slide label: **"02b — SOLUTION ARCHITECTURE"**; title: **"Arsitektur Solusi"**; subtitle: **"Satu platform terpusat, data setiap klien terisolasi penuh"** `[slide 02b]`
- Central box: **"Platform Sentral"** — "Multi-tenant • Data terpisah per klien" `[slide 02b]`
- Four tenant boxes beneath the platform box:
  1. **Klien A** — "Data terpisah" `[slide 02b]`
  2. **Klien B** — "Data terpisah" `[slide 02b]`
  3. **Klien C** — "Data terpisah" `[slide 02b]`
  4. **Snøhund** — "Brand internal" `[slide 02b]`
- Footer bar: **"Platform Operasional Terpadu — Lukla Manufacturing"** `[slide 02b]`

### Extraction

- **Business rules:**
  - Single central platform, multi-tenant, with per-client data separation as the headline property ("data setiap klien terisolasi penuh"). `[slide 02b]`
  - Tenant roster as drawn: three external clients (Klien A/B/C), each "Data terpisah", plus Snøhund labeled "Brand internal" — Snøhund is its own tenant box, distinct from Klien A/B/C. `[slide 02b]`
- **FR IDs found:** none badged on this slide.
- **Actors/roles:** klien (tenants); Snøhund as internal brand tenant.
- **Numbers:** none.
- **UI elements:** none (architecture diagram only).
- **Revision-4 correction notes (critical C-02):** rev 3 invented a "Data Terisolasi" edge label, a three-module decomposition of the platform (Modul Produksi/Gudang/Payroll), and drew Snøhund as "Klien A (Brand Snøhund)". None of that appears on the slide; the actual diagram is one central platform box over four tenant boxes as transcribed above.

---

## Slide 02c — Solusi: Platform Operasional Terpadu — **NOT ON DISK**

**Provenance:** **none.** No photo of slide 02c exists in `openspec/artifacts/slide-photos/` (verified by full re-view of all 11 photos on 2026-10-12) and no chat attachment exists. The deck numbering (02b → 03) and revision-1's register imply the slide exists in the deck, but its content cannot be verified.

### Status

- Revision-1's transcription of this slide (three solution pillars: Multi-tenant FR-1.1, RBAC FR-2.1, Audit trail FR-3.1) was sourced to photo `10.40.55b.jpeg`, which actually shows **slide 03**. That transcription is **unverifiable** and is NOT carried as slide content.
- What remains verifiable from on-disk sources:
  - **FR-1.1** badge appears in Fase 1 of `[slide 03]`; the multi-tenant/data-isolation concept is stated on `[slide 02b]`.
  - **FR-3.1** badges appear on `[slide 02]` and `[slide 03]` (Fase 2).
  - The **RBAC** concept is fully documented by the 8-role matrix on `[slide 04]` — but the **FR-2.1** badge itself appears on no on-disk slide. FR-2.1 as an ID is carried as `[assumption]`.
- Original slide 02c requested from user. Later documents must not cite `[slide 02c]` for any requirement until the original is supplied.

---

## Slide 03 — Alur Operasional 6 Fase

**Provenance:** photo `10.40.55b.jpeg` — re-viewed 2026-10-12. Legible.

### Transcription

- Slide label: **"03 — OPERATIONAL FLOW"**; title: **"Alur Operasional 6 Fase"** `[slide 03]`
- Six phases in sequence, with FR badges:
  1. **Onboarding Klien & Order** — "Registrasi klien, skema maklon, penerimaan order." Badges: **FR-1.1**, **FR-1.4**. `[slide 03]`
  2. **Sample & Time Study** — "Pembuatan sample, revisi berversi, time study per komponen." Badges: **FR-3.1**, **FR-4.1**. `[slide 03]`
  3. **Gudang** — "Penerimaan bahan dan titipan klien, stok multi-klien." Badge: **FR-5**. `[slide 03]`
  4. **Cutting** — "Pemotongan bahan massal." Badge: **FR-6**. `[slide 03]`
  5. **Produksi** — "Tracking output per 30 menit, alokasi line dinamis." Badges: **FR-7.1**, **FR-7.3**. `[slide 03]`
  6. **QC & Payroll** — "Inspeksi QC, bonus pool, payroll borongan." Badges: **FR-8.1**, **FR-9.1**, **FR-10.1**. `[slide 03]`

### Extraction

- **FR IDs found:** FR-1.1 `[slide 03]`, FR-1.4 `[slide 03]`, FR-3.1 `[slide 03]`, FR-4.1 `[slide 03]`, FR-5 `[slide 03]`, FR-6 `[slide 03]`, FR-7.1 `[slide 03]`, FR-7.3 `[slide 03]`, FR-8.1 `[slide 03]`, FR-9.1 `[slide 03]`, FR-10.1 `[slide 03]`.
- **Business rules:**
  - Operational flow is exactly 6 sequential phases: Onboarding/Order → Sample & Time Study → Gudang → Cutting → Produksi → QC & Payroll. `[slide 03]`
  - Order onboarding captures the maklon scheme per order. `[slide 03]`
- **Correction note (rev 2):** revision 1 claimed an FR-6.2 guardrail badge on Fase 4. No FR-6.2 badge is visible on this slide — only bare **FR-6**. FR-6.2 appears on `[slide 02]` and is exercised on `[slide 09]`.
- **Actors/roles:** none named on this slide.
- **Numbers:** 6 fase.
- **UI elements:** none.

---

## Slide 04 — Matriks RBAC: 8 Peran Pengguna

**Provenance:** photo `10.40.55c.jpeg` — re-viewed 2026-10-12. Fully legible, including all IZIN/PEMBATASAN cells. (Revision 1 marked most cells `[illegible?]` and transcribed a different role list; both were wrong. The orchestrator's chat-attachment copy was cross-checked against the photo and matches verbatim; the photo is the primary source.)

### Transcription

- Slide label: **"04 — RBAC MATRIX"**; title: **"Matriks RBAC: 8 Peran Pengguna"** `[slide 04]`
- Intro line: "Kontrol akses berbasis peran untuk seluruh pengguna pabrik dan klien." `[slide 04]`
- Table columns: **PERAN | IZIN | PEMBATASAN**. Eight role rows: `[slide 04]`

| # | Peran | IZIN | PEMBATASAN |
|---|---|---|---|
| 1 | **Owner/Eksekutif** (Internal) | Analitik tinggi & konfigurasi sistem; Ubah rate card | Tidak dapat mengubah histori transaksi yang dikunci |
| 2 | **Tim Sample/Adis** (Sample) | Catat pemakaian bahan sample; Input time study per komponen; Setujui versi sample | Tidak dapat menyetujui pesanan massal tanpa konfirmasi |
| 3 | **Gudang/Warehouse** (Stok) | Terima bahan + titipan klien; Keluarkan bahan ke cutting; Stok opname | Dilarang mengeluarkan bahan jika ID Klien/Pesanan tidak cocok |
| 4 | **Kepala Produksi/Mandor** (Line) | Atur line + alokasi penjahit; Tentukan rate card komponen; Catat output 30 menit | Tidak dapat mengubah formula penggajian atau hasil QC final |
| 5 | **Penjahit/Tailor** (Operator) | Lihat tugas komponen; Laporkan hasil kerja (diverifikasi mandor) | Tidak dapat mengedit catatan output yang sudah diverifikasi |
| 6 | **QC Inspector** (Quality) | Periksa barang jadi; Set status lolos/reject/repair; Catat jenis cacat | Tidak dapat mengubah harga borongan atau data order klien |
| 7 | **Finance & Payroll** (Finance) | Buat/setujui PO bahan; Terbitkan invoice; Hitung gaji mingguan & bulanan | Tidak dapat mengubah fisik stok di gudang |
| 8 | **Klien Maklon/Ext** (B2B Portal) | Pantau status pesanan; Lihat progres real-time; Lihat stok bahan titipan sendiri | Terbatas hanya pada data client_id milik sendiri |

`[slide 04]` for the entire table.

### Extraction

- **Actors/roles (8, confirmed):** Owner/Eksekutif; Tim Sample/Adis; Gudang/Warehouse; Kepala Produksi/Mandor; Penjahit/Tailor; QC Inspector; Finance & Payroll; Klien Maklon/Ext. `[slide 04]`
- **Business rules:**
  - RBAC matrix has exactly 8 roles with explicit IZIN (permissions) and PEMBATASAN (restrictions) columns. `[slide 04]`
  - Locked-history rule: not even the Owner can change locked transaction history. `[slide 04]`
  - Warehouse issuance guardrail: material may not be issued when ID Klien/Pesanan does not match — this is the RBAC-side statement of the cross-client contamination control (see FR-6.2 ambiguity note). `[slide 04]`
  - Output records become immutable once verified: penjahit cannot edit verified output; mandor verifies penjahit reports. `[slide 04]`
  - Separation of duties: Finance cannot change physical stock; Gudang cannot issue mismatched material; QC cannot change borongan prices or client order data; Kepala Produksi/Mandor cannot change payroll formulas or final QC results. `[slide 04]`
  - Client portal isolation: external clients see only their own `client_id` data. `[slide 04]`
  - Payroll cadence signal: Finance "Hitung gaji mingguan & bulanan" (weekly AND monthly payroll computation). `[slide 04]`
  - Rate card governance: Owner can "Ubah rate card"; Kepala Produksi/Mandor can "Tentukan rate card komponen". `[slide 04]`
- **FR IDs found:** none badged on this slide (the matrix operationalizes the RBAC concept; the FR-2.1 badge itself appears on no on-disk slide — see slide 02c section).
- **Numbers:** 8 peran.
- **UI elements:** none.
- **Terminology variance:** QC row uses status wording "lolos/reject/repair"; `[slide 05]` badges use "Pass/Repair/Reject" (English; revision 4); `[slide 08]` view 05 uses "lolos/repair/scrap". Recorded in Contradictions/ambiguities — not resolved here.

---

## Slide 04b — Alur Data Terintegrasi

**Provenance:** photo `10.40.56.jpeg` — re-viewed 2026-10-12. Legible.

### Transcription

- Slide label: **"04b — DATA FLOW"**; title: **"Alur Data Terintegrasi"** `[slide 04b]`
- Intro line: "Data mengalir dari order hingga payroll tanpa input manual berulang." `[slide 04b]`
- Six-stage flow with per-stage captions: `[slide 04b]`
  1. **Order** — "Order dikonfirmasi"
  2. **Gudang** — "Bahan dikeluarkan"
  3. **Cutting** — "Pemotongan selesai"
  4. **Produksi** — "Output terverifikasi"
  5. **QC** — "Lolos QC"
  6. **Payroll** — "Gaji dihitung"
- Edge label **"Menunggu QC"** is printed on the arrow between the **QC** and **Payroll** boxes (position as observed on the slide). `[slide 04b]`

### Extraction

- **Business rules:**
  - Single integrated data flow: Order → Gudang → Cutting → Produksi → QC → Payroll. `[slide 04b]`
  - No repeated manual input across the chain ("tanpa input manual berulang"). `[slide 04b]`
  - Payroll consumes verified production/QC data ("Output terverifikasi" → "Lolos QC" → "Gaji dihitung"). `[slide 04b]`
  - Status `Menunggu QC` exists in the flow; its printed position (QC→Payroll edge) differs from slide 06's semantics (assembly output enters `Menunggu QC`, i.e. before QC). Recorded in Contradictions/ambiguities — not resolved.
- **FR IDs found:** none badged (diagram supports the FR-5/FR-6/FR-7/FR-8/FR-10 chain).
- **Actors/roles:** none.
- **Numbers:** none.
- **UI elements:** none.
- **Negative finding (rev 2):** the terms "WIP" and "barang jadi" do NOT appear on this slide. ("Barang jadi" appears on `[slide 04]`, QC Inspector row; "WIP" appears on no on-disk slide.)

---

## Slide 05 — Inspeksi QC & Bonus Pool 3 Arah

**Provenance:** PDF render `pdf-image/Lukla Operations Engine — SRS Walkthrough - page-0008.jpg` — viewed 2026-10-12 (Phase 0-R, revision 4). Printed slide label verified on the render. Fully legible; supersedes the rev-3 photo-based transcription (critical C-03).

### Transcription (verbatim, revision 4)

- Slide label: **"05 — QUALITY CONTROL"**; title: **"Inspeksi QC & Bonus Pool 3 Arah"**; subtitle: **"Setiap unit diverifikasi — bonus dibagi ke 3 peran kunci"** `[slide 05]`
- Four feature cards:
  1. **FR-8.1 — Inspeksi QC** — "Setiap unit jadi diperiksa QC. Status menentukan rute tindakan selanjutnya." Status badges printed on the card: **Pass** (green), **Repair** (yellow), **Reject** (red). `[slide 05]`
  2. **FR-8.2 — Repair tanpa Gaji Ganda** — "Unit Repair kembali ke penjahit yang sama. Tidak ada kredit ganda." `[slide 05]`
  3. **FR-9.1 — Bonus Pool per Unit** — "Setiap unit Pass QC menambah bonus pool." `[slide 05]`
  4. **FR-9.2 — Dibagi 3 Arah** — "Mandor 1, Mandor 2, Kepala Operasional. Dibayarkan bersama payroll mingguan." `[slide 05]`
- Right side panel: **"÷ 3"** — "Mandor 1 • Mandor 2 • Kepala Ops" — "Bonus pool dibagi rata ke 3 peran" `[slide 05]`
- Footer bar: **"Platform Operasional Terpadu — Lukla Manufacturing"** `[slide 05]`

### Extraction

- **FR IDs found:** FR-8.1 `[slide 05]`, FR-8.2 `[slide 05]`, FR-9.1 `[slide 05]`, FR-9.2 `[slide 05]`.
- **Business rules:**
  - FR-8.1: every finished unit is QC-inspected; the status determines the next action route. Status set as printed: Pass / Repair / Reject. `[slide 05]`
  - FR-8.2: a Repair unit returns to the same sewer; no double piece-rate credit is earned on rework. `[slide 05]`
  - FR-9.1: every QC-Pass unit adds to the bonus pool. `[slide 05]`
  - FR-9.2: the pool is split 3 ways — Mandor 1, Mandor 2, Kepala Operasional — and is paid together with the weekly payroll. `[slide 05]`
- **Actors/roles:** QC (implied), Mandor 1, Mandor 2, Kepala Operasional.
- **Numbers:** ÷3.
- **UI elements:** status badges Pass / Repair / Reject.
- **Revision-4 correction notes (critical C-03):** rev 3 mislabeled the slide "QC & BONUS" (actual: "QUALITY CONTROL"); rendered the status set as "lolos/repair/scrap" (actual badges: Pass/Repair/Reject — see Contradictions for the cross-slide wording variance); replaced the real FR-8.2 card ("Repair tanpa Gaji Ganda") with an invented "Kategori Defect" card (defect-category selection appears on `[slide 08]` view 05, not on this slide); and omitted the FR-8.1 routing sentence, the "Dibayarkan bersama payroll mingguan" clause in FR-9.2, the ÷3 side panel, and the footer.

---

## Slide 06 — Tracking Output 30 Menit & Line Dinamis

**Provenance:** PDF render `pdf-image/Lukla Operations Engine — SRS Walkthrough - page-0009.jpg` — viewed 2026-10-12 (Phase 0-R, revision 4). Printed slide label verified on the render. Fully legible; supersedes the rev-3 photo-based transcription (critical C-04).

### Transcription (verbatim, revision 4)

- Slide label: **"06 — PRODUCTION TRACKING"**; title: **"Tracking Output 30 Menit & Line Dinamis"**; subtitle: **"Visibilitas real-time atas produktivitas setiap penjahit"** `[slide 06]`
- Four feature cards:
  1. **FR-7.1 — Alokasi Kapasitas Dinamis** — "Line diatur ulang berdasarkan jumlah penjahit aktif per hari. Tidak ada slot kaku." `[slide 06]`
  2. **FR-7.2 — Rate Card per Artikel & Klien** — "Ongkos jahit per komponen berbeda per artikel. Rate card dikelola Owner." `[slide 06]`
  3. **FR-7.3 — Output 30 Menit** — "Mandor input hasil jahit per penjahit/komponen setiap 30 menit via terminal touch-friendly." `[slide 06]`
  4. **FR-7.4 — Assembly → Menunggu QC** — "Unit selesai masuk antrian QC. Upah diakui setelah verifikasi QC." `[slide 06]`
- Three stat cards: **"±70"** — "Mesin jahit aktif" — "tanpa slot kaku"; **"30 mnt"** — "Interval tracking"; **"Real-time"** — "Monitoring lantai" `[slide 06]`
- Footer bar: **"Platform Operasional Terpadu — Lukla Manufacturing"** `[slide 06]`

### Extraction

- **FR IDs found:** FR-7.1 `[slide 06]`, FR-7.2 `[slide 06]`, FR-7.3 `[slide 06]`, FR-7.4 `[slide 06]`.
- **Business rules:**
  - FR-7.1: lines are rearranged based on the number of active sewers per day; no rigid slots ("Tidak ada slot kaku"). `[slide 06]`
  - FR-7.2: per-component sewing price (ongkos jahit) differs per article; the rate card is managed by the Owner. `[slide 06]`
  - FR-7.3: the mandor inputs sewing output per penjahit/komponen every 30 minutes via a touch-friendly terminal. `[slide 06]`
  - FR-7.4: finished units enter the QC queue (`Menunggu QC`); wages are recognized only after QC verification. `[slide 06]`
  - Scale context: ±70 active sewing machines, "tanpa slot kaku" — consistent with FR-7.1 and with `[slide 02]`'s "1–70+ penjahit aktif"; NOT a system cap. `[slide 06]`
- **Actors/roles:** mandor (inputs output), Owner (manages rate card), penjahit (referenced).
- **Numbers:** ±70 mesin; 30 menit interval.
- **UI elements:** touch-friendly input terminal (named in the FR-7.3 card text).
- **Revision-4 correction notes (critical C-04):** rev 3 mislabeled the slide "OUTPUT TRACKING" (actual: "PRODUCTION TRACKING"); recast FR-7.3 as cutting output ("jumlah potong") — the actual card is sewing output ("hasil jahit") per penjahit/komponen; invented a bottom bar ("Kapasitas ±70 mesin — Output dicatat per 30 menit — Status: Menunggu QC") in place of the actual three stat cards; and falsely claimed "tanpa slot kaku" appears on no on-disk slide — it appears twice on this slide (FR-7.1 body and the ±70 stat card). Source-conflict note: review 2 (working from the WhatsApp photo) believed FR-7.3/FR-7.4 were printed as ONE combined card; the PDF render shows two distinct cards, and the render is the more legible source — treated as resolved in favor of the render.

---

## Slide 07 — Mesin Payroll Fleksibel — **CHAT ATTACHMENT ONLY**

**Provenance:** `[slide 07 — chat attachment]` — fully legible chat attachment, transcribed verbatim by the orchestrator. No photo of slide 07 exists in `openspec/artifacts/slide-photos/` (verified by full re-view of all 11 photos on 2026-10-12); the original on-disk photo has been requested from the user. Revision 1 incorrectly sourced this slide to photo `10.40.56d.jpeg`, which actually shows **slide 08** (Layar Tampilan Utama).

### Transcription

- Header: `07 — PAYROLL ENGINE`. Title: "Mesin Payroll Fleksibel". Subtitle: "Empat komponen perhitungan biaya operasional — borongan, uang makan, pool bonus QC, dan overhead." `[slide 07 — chat attachment]`
- **FR-10.1 — Setiap Sabtu** (PERIODE PENGHITUNGAN): "Upah borongan penjahit dihitung setiap hari Sabtu berdasarkan akumulasi output komponen terverifikasi dikalikan rate jahit per artikel. Tidak ada batasan jumlah penjahit yang dapat diproses. Output diverifikasi mandor sebelum masuk perhitungan." `[slide 07 — chat attachment]`
- **FR-10.2 — 10–15%** (DARI TOTAL ONGKOS JAHIT): "Persentase diinput manual per periode produksi. Fleksibel mengikuti kebijakan operasional tanpa perubahan kode sistem. Dihitung dari total dana ongkos jahit yang dihasilkan dalam satu periode." `[slide 07 — chat attachment]`
- **FR-10.3 — ÷ 3** (2 MANDOR + 1 KEPALA OPERASIONAL): "Setiap produk yang lolos QC dari seluruh klien/order membentuk pool bonus berdasarkan rate per pcs. Total pool dibagi rata kepada 3 orang penerima — 2 Mandor dan 1 Kepala Operasional. Pool akumulatif lintas order dan lintas klien." `[slide 07 — chat attachment]`
- **FR-10.4 — Bulanan / Σ Unit** (OVERHEAD PER UNIT PRODUK): "Catatan bulanan untuk tagihan listrik, air, internet, dan operasional pabrik Lukla Manufacturing. Biaya overhead per unit dihitung dengan membagi total biaya operasional bulanan dengan total seluruh unit produk yang diproduksi di bulan tersebut." `[slide 07 — chat attachment]`

### What IS verifiable from on-disk sources

- **FR-10** badge (payroll as a whole) on `[slide 02]`; **FR-10.1** badge in Fase 6 of `[slide 03]`.
- Slide 08 view 06 (Workspace Payroll & Bonus) names all four payroll elements: "gaji borongan mingguan penjahit", "pembagian bonus QC 3-arah", "penghitungan uang makan", "rekap alokasi overhead operasional pabrik". `[slide 08]`
- The ÷3 bonus split to 2 mandor + 1 kepala operasional: `[slide 05]` (FR-9.2), `[slide 09]` (scenario 3, with 3000 units).
- Weekly AND monthly payroll cadence: "Hitung gaji mingguan & bulanan" `[slide 04]` (Finance & Payroll role).
- The Saturday calculation day, the 10–15% percentage, the total ongkos jahit base, and the overhead ÷ monthly total-units formula appear on **no** on-disk photo; they are directly sourced from `[slide 07 — chat attachment]`.

---

## Slide 08 — Layar Tampilan Utama (Minimum Required UI Views)

**Provenance:** photo `10.40.56d.jpeg` — re-viewed 2026-10-12. Legible. (Revision 1 treated this slide as chat-attachment-only and sourced it from the wrong photo; the photo IS on disk and is the primary source. The chat-attachment transcription is demoted to a cross-check note: it matches the photo, and the one phrase it marked `[illegible?]` is confirmed by the photo as "ID Klien".)

### Transcription

- Slide label: **"08 — UI VIEWS"**; title: **"Layar Tampilan Utama"**; subtitle: **"Minimum Required UI Views"** `[slide 08]`
- Intro line: "Enam tampilan utama yang wajib ada pada sistem Lukla Operations Engine." `[slide 08]`
- Six views:
  1. **(01) Dashboard Utama Operasional** — "Overview kondisi pabrik real-time: line aktif, jumlah penjahit bertugas, progres order per klien, dan grafik kecepatan produksi interval 30 menit." `[slide 08]`
  2. **(02) Sample & Time Study Tracker** — "Pengelolaan revisi versi sample (v1, v2, dst), stopwatch digital untuk time study per komponen, dan tabel pencatatan waktu pengerjaan." `[slide 08]`
  3. **(03) Gudang Multi-Klien & Stok** — "Grid inventaris multi-tenant dengan filter per klien, form penerimaan bahan titipan, dan peringatan ketidakcocokan ID Klien." `[slide 08]`
  4. **(04) Terminal Input 30 Menit** — "Antarmuka input sederhana berukuran besar. Mandor menginput output pcs per penjahit setiap 30 menit di area pabrik." `[slide 08]`
  5. **(05) Terminal Inspeksi QC** — "Pencatatan status pemeriksaan produk (lolos, repair, scrap), pemilihan kategori defect, dan pengalihan status barang ke rute tindakan yang sesuai." `[slide 08]`
  6. **(06) Workspace Payroll & Bonus** — "Penghitungan gaji borongan mingguan penjahit, kalkulasi pembagian bonus QC 3-arah, penghitungan uang makan, dan rekap alokasi overhead operasional pabrik." `[slide 08]`

### Extraction

- **UI elements (6 minimum required views, confirmed):** Dashboard Utama Operasional; Sample & Time Study Tracker; Gudang Multi-Klien & Stok; Terminal Input 30 Menit; Terminal Inspeksi QC; Workspace Payroll & Bonus. `[slide 08]`
- **Business rules:**
  - Dashboard shows real-time factory state incl. 30-minute production-speed graph. `[slide 08]`
  - Sample tracker uses explicit versioning (v1, v2, …) and per-component time study with digital stopwatch. `[slide 08]`
  - Warehouse grid is multi-tenant with per-client filter, consignment-material receiving form, and a client-ID mismatch warning (corroborates the `[slide 04]` warehouse restriction and the FR-6.2 guardrail). `[slide 08]`
  - View 04 describes mandor input of output pcs **per penjahit** per 30 minutes — consistent with slide 06 FR-7.3's "per penjahit/komponen" (revision-4 verbatim transcription; see Contradictions/ambiguities).
  - View 06 confirms the four payroll computation areas (weekly borongan, 3-way QC bonus, uang makan, overhead allocation) exist as system functionality. `[slide 08]`
- **FR IDs found:** none badged (views map to FR-5, FR-7.x, FR-8.x, FR-9.x, FR-10.x).
- **Actors/roles:** mandor (view 04), QC (view 05), finance/payroll (view 06).
- **Numbers:** 6 views; 30 menit interval.

---

## Slide 09 — Closing: Tujuan Sistem & 4 Skenario Pengujian

**Provenance:** photo `10.40.57.jpeg` — re-viewed 2026-10-12. Legible.

### Transcription

- Slide label: **"09 — CLOSING"**; title: **"Tujuan Sistem & Skenario Pengujian"** `[slide 09]`
- **Tujuan Sistem:** "Platform operasi terpadu multi-tenant untuk produksi dan payroll konveksi Lukla Manufacturing." `[slide 09]`
- **4 Skenario Pengujian (acceptance test scenarios):**
  1. **Penolakan Kontaminasi Silang** — "Sistem menolak pengeluaran bahan milik Klien A untuk order Klien B." `[slide 09]`
  2. **Payroll Headcount Dinamis** — "Penambahan +5 penjahit di tengah minggu berjalan. Perhitungan payroll tetap benar." `[slide 09]`
  3. **Bonus Pool QC 3000 Unit** — "Output 3000 unit lolos QC. Bonus pool dihitung dan dibagi 3: 2 mandor + 1 kepala operasional." `[slide 09]`
  4. **Revisi Sample v1 → v2 ke Order Massal** — "Sample direvisi dari v1 ke v2, lalu menjadi order massal skema Semi-CMT. Riwayat spesifikasi v2 terlacak." `[slide 09]`
- Footer: **"Lukla Operations Engine — Hackathon 2026"** `[slide 09]`

### Extraction

- **Business rules:**
  - The 4 scenarios are acceptance tests (incl. a negative path), not feature descriptions. `[slide 09]`
  - Cross-client contamination must be **rejected** by the system (exercises FR-6.2). `[slide 09]`
  - Payroll must remain correct under mid-week headcount change (+5 penjahit) (exercises FR-7.1 dynamic allocation and FR-10.x payroll). `[slide 09]`
  - Bonus pool scenario uses exactly 3000 units and ÷3 split (exercises FR-9.1/FR-9.2). `[slide 09]`
  - Sample revision v1→v2 must carry traceable spec history into a Semi-CMT mass order (exercises FR-3.1, FR-4.1). `[slide 09]`
- **FR IDs found:** none badged (scenarios exercise FR-6.2, FR-7.1, FR-9.x, FR-10.x, FR-3.1, FR-4.1).
- **Actors/roles:** none new.
- **Numbers:** +5 penjahit; 3000 unit; ÷3; v1→v2.
- **UI elements:** none.

---

## Master FR inventory

| FR ID | Slide source(s) | One-line meaning (as stated on slides) |
|---|---|---|
| FR-1.1 | `[slide 03]` (badge); concept `[slide 02b]` | Multi-tenant platform; data isolated per client |
| FR-1.4 | `[slide 03]` | Client/order onboarding element (badge seen in Fase 1; definition text shown nowhere — see UNRESOLVED) |
| FR-2.1 | `[assumption]`; concept `[slide 04]` | Role-based access control (8-role matrix on slide 04) |
| FR-3.1 | `[slide 02]`, `[slide 03]` | Audit trail / traceable history (incl. sample revisions) |
| FR-4.1 | `[slide 02]`, `[slide 03]` | Sample revision tracking / versioning (v1, v2, …) |
| FR-5 | `[slide 03]`; badge `[slide 02]` | Gudang (warehouse) phase — multi-client stock, consignment receiving (named only; detail not specified) |
| FR-6 | `[slide 03]` | Cutting phase (named only; detail not specified) |
| FR-6.2 | `[slide 02]`, `[slide 09]`; enforcement corroborated `[slide 04]`, `[slide 08]` | Cross-client contamination guardrail — reject Client A material for Client B order |
| FR-7.1 | `[slide 06]`; badge `[slide 03]` | Alokasi Kapasitas Dinamis — lines rearranged by active sewer count per day; "Tidak ada slot kaku" |
| FR-7.2 | `[slide 06]` | Rate Card per Artikel & Klien — per-component ongkos jahit differs per article; rate card managed by Owner |
| FR-7.3 | `[slide 06]`; badge `[slide 03]` | Output 30 Menit — mandor inputs sewing output per penjahit/komponen every 30 min via touch-friendly terminal |
| FR-7.4 | `[slide 06]` | Assembly → Menunggu QC — finished units enter QC queue; wages recognized only after QC verification |
| FR-8.1 | `[slide 05]`; badge `[slide 03]` | QC inspection of every finished unit; status Pass / Repair / Reject determines next action route |
| FR-8.2 | `[slide 05]` | Repair tanpa Gaji Ganda — Repair unit returns to the same sewer; no double piece-rate credit |
| FR-9.1 | `[slide 05]`; badge `[slide 03]` | QC bonus pool derived from QC-passed output |
| FR-9.2 | `[slide 05]` | Bonus pool split 3 ways: 2 mandor + 1 kepala operasional |
| FR-10.1 | `[slide 07 — chat attachment]`; badge `[slide 03]`; weekly borongan named `[slide 08]` | Every Saturday: verified component output × rate jahit per artikel; mandor verification, no sewer-count limit |
| FR-10.2 | `[slide 07 — chat attachment]`; uang makan named `[slide 08]` | 10–15% of total ongkos jahit generated in one production period; percentage manually entered per period |
| FR-10.3 | `[slide 07 — chat attachment]`; split corroborated `[slide 05]`, `[slide 09]` | Pool from QC-passed products across clients/orders at rate per pcs; ÷3 to 2 mandor + 1 kepala operasional |
| FR-10.4 | `[slide 07 — chat attachment]`; overhead rekap named `[slide 08]` | Monthly electricity/water/internet/factory operations total ÷ all units produced that month |

**Deck-level references (no sub-ID):** FR-5, FR-7, and FR-10 are badged as whole IDs on `[slide 02]` (pain-point cards); FR-10.1 also appears as a badge in Fase 6 of `[slide 03]`.

## Skipped FR numbers — referenced-but-not-defined in source

The following IDs are **not shown on any slide**. They are recorded here as *referenced-but-not-defined in source* (numbering gaps in the deck), **NOT** as gaps to fill:

- **FR-1.2, FR-1.3** — never shown (FR-1.1 and FR-1.4 appear; intermediate numbers absent).
- **FR-2.2+** — only FR-2.1 referenced (and FR-2.1 itself only via the unverified 02c transcription — see slide 02c section).
- **FR-3.2+** — only FR-3.1 shown.
- **FR-4.2+** — only FR-4.1 shown.
- **FR-5.x sub-IDs** — only bare FR-5 shown.
- **FR-6.1, FR-6.3+** — only FR-6 and FR-6.2 shown.
- **FR-8.3+, FR-9.3+** — not shown.
- **FR-10.5+** — not shown (and must not be invented: no BPJS/tax/overtime content).

## UNRESOLVED - not in source

Everything the deck names but never specifies:

1. **Slide 02c entire content** — no photo on disk, no chat attachment. FR-1.1/FR-3.1 survive via badges on `[slide 03]`/`[slide 02]`; the FR-2.1 ID and the "three pillars" framing do not. **UNRESOLVED - slide not on disk; original requested from user.**
2. **Slide 07 original on-disk photo** — no photo on disk; all four FR-10.x boxes are transcribed from `[slide 07 — chat attachment]`, not assumptions. **UNRESOLVED - original photo requested from user; source wording available in chat.**
3. **FR-5 (Gudang) detail** — named in the 6-phase flow `[slide 03]` and data flow `[slide 04b]`; view 03 `[slide 08]` shows a multi-client inventory grid + consignment receiving form + ID-mismatch warning; the Gudang/Warehouse RBAC row `[slide 04]` lists receive/issue/stok-opname permissions. No slide specifies inventory transactions, stock adjustment rules, or stok opname procedure. **UNRESOLVED - not in source.**
4. **FR-6 (Cutting) detail** — named as a phase `[slide 03]` and flow stage `[slide 04b]`; the contamination guardrail FR-6.2 `[slide 02]` is specified. No slide specifies cutting batches, markers, wastage rules, or cutting output recording (revision-4 correction: FR-7.3 `[slide 06]` records **sewing** output, not cutting — rev 3's "jumlah potong" reading was wrong). **UNRESOLVED - not in source.**
5. **FR-1.4 exact wording** — badge observed in Fase 1 of `[slide 03]` but its definition text appears nowhere. **UNRESOLVED - not in source.**
6. **Bonus pool ÷3 configurability** — split is fixed at ÷3 (2 mandor + 1 kepala operasional) on `[slide 05]` and `[slide 09]`; whether recipient count is configurable is never stated. **UNRESOLVED - not in source (open question, do not decide).**
7. **Uang makan base definition** — FR-10.2 `[slide 07 — chat attachment]` specifies total ongkos jahit per production period but does not define its computation vs. ongkos potong (ongkos potong appears on no slide at all). **UNRESOLVED - not in source.**
8. **Illegible-spot registry** — revision 2: all 11 on-disk photos proved legible, including slide 00's footer ("Pitch Deck — Hackathon 2026" / "Confidential — Internal Use Only") and all slide 04 RBAC cells. **No material `[illegible?]` spots remain.**

## Contradictions / ambiguities

- **FR-6.2 module/behavior tension (recorded, NOT resolved):** FR-6.2 is numbered under FR-6 (Cutting phase, `[slide 03]`) and badged on the contamination pain point `[slide 02]`, but its behavior — rejecting issuance of Client A material for a Client B order (`[slide 09]` scenario 1) — is operationally a **warehouse / material-issuance** control: the Gudang/Warehouse RBAC row states "Dilarang mengeluarkan bahan jika ID Klien/Pesanan tidak cocok" `[slide 04]`, the warehouse UI view carries the "peringatan ketidakcocokan ID Klien" `[slide 08]`, and slide 02's contamination card ("Bahan Klien A terpakai untuk Order Klien B") names no owning module `[slide 02]`. Whether FR-6.2 belongs to a warehouse module, the cutting module, or both is **not decided by the source** — later documents must record this ambiguity and must NOT invent module ownership.
- **Output recording granularity (RESOLVED in revision 4):** earlier revisions read slide 06 as recording output **per komponen** only, conflicting with slide 08 view 04's **per penjahit**. The revision-4 verbatim transcription of slide 06 FR-7.3 reads "per penjahit/komponen" — both granularities are named on slide 06, so no conflict remains.
- **QC status wording variance (recorded, NOT resolved):** the source uses three wordings — slide 04's QC row: "lolos/reject/repair"; slide 05's badges: "Pass/Repair/Reject" (English; revision 4); slide 08 view 05: "lolos/repair/scrap". Treated as terminology variance in the source, not three different status sets.
- **`Menunggu QC` position variance (recorded, NOT resolved):** slide 06 (FR-7.4) has assembly output entering status `Menunggu QC` (i.e. before QC); on slide 04b the label is printed on the QC→Payroll edge. Position vs. semantics differ in the source.
- **Ambiguity (not contradiction):** FR-9.2 (slide 05) and FR-10.3 `[slide 07 — chat attachment]` describe the same ÷3 bonus split under two IDs — treated as one rule referenced from two features, not two rules.
- **Ambiguity:** "±70 mesin jahit" appears as scale context on `[slide 01]` and `[slide 06]`; FR-7.1's dynamic capacity allocation confirms it is NOT a system cap. No contradiction.
- Otherwise: **none found.**
