# Product Requirements Document (PRD) & Technical Specification
**Project:** Lukla Operations Engine
**Platform:** Web App (Responsive Desktop & Tablet PWA)
**Design System:** Apple Human Interface Guidelines (HIG) Inspired

---

## 1. PRODUCT REQUIREMENTS DOCUMENT (PRD)

### 1.1 Ringkasan Produk
Lukla Operations Engine adalah sistem manajemen manufaktur *event-driven* berbasis *double-entry ledger* untuk fasilitas konveksi Lukla di Ciwidey. Sistem ini memecahkan tiga masalah utama: kontaminasi silang material multi-tenant, kompleksitas perhitungan *payroll* borongan dinamis (1-70+ operator), dan hilangnya jejak revisi sampel (R&D drift).

### 1.2 Core Features & 6 UI Views Utama
1. **Executive Operations Dashboard (View 01):** Pantauan lini aktif dan grafik output 30 menit.
2. **Sample & Time Study Tracker (View 02):** Perekaman versi spesifikasi produk dan stopwatch digital.
3. **Multi-Client Warehouse Grid (View 03):** Tabel inventaris dengan pemblokiran otomatis (*anti-cross contamination*) antar-klien.
4. **Floor Terminal (View 04):** Antarmuka tablet sentuh bagi mandor untuk input *tally* jahitan per 30 menit.
5. **QC Inspection Terminal (View 05):** Pemindai status akhir garmen (Pass, Repair, Reject) dan taksonomi cacat.
6. **Payroll & Costing Workspace (View 06):** Kalkulasi otomatis upah borongan, uang makan (10-15%), pembagian bonus QC 3-arah, dan biaya *overhead*.

### 1.3 Strict Constraints (Wajib)
*   **Immutable Ledger:** Transaksi tidak bisa di-UPDATE/DELETE. Harus melalui transaksi pembalik.
*   **Anti-Contamination Guardrail:** Sistem basis data *wajib* menolak (*abort*) transaksi pemotongan bahan jika `client_id` bahan tidak sama dengan `client_id` pesanan.
*   **Multi-Tenant Isolation:** Semua kueri klien eksternal wajib dibatasi `client_id`.

---