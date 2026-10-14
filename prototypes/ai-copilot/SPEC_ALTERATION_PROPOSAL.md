# Spec Alteration Proposal: Lukla Operational Copilot Extension

## Executive Context & Wagile Discipline

The Lukla Operations Engine repository operates under a strict **Wagile** governance model ([PRD §A / §B](file:///C:/Projects/hackathon-MAIN-alkademi/openspec/changes/lukla-ops-engine-planning/PRD%20-%20Lukla%20Operations%20Engine%20-%20v2.0%20-%20Wagile.md#L16-L20)):
- **Bagian A (Kontrak Ruang Lingkup)** is frozen upon stakeholder sign-off.
- **Bagian B (Product Backlog)** is a living backlog that evolves across Sprints.

Extending the system to incorporate a ChatGPT-like foundational model chatbot must **never** undermine the core architectural invariants:
1. **Immutable Double-Entry Ledger (`NFR-02`)**: No transaction may ever be posted without balanced debits/credits, tenant isolation, and an `Idempotency-Key`.
2. **Multi-Tenant Custodial Stock Boundary**: Consignment fabrics (CMT/Semi-CMT) owned by Maklon Client A must never be visible to or consumed by Client B.
3. **Zero Autonomous LLM State Mutations**: The AI Copilot is strictly a **Read-Only Intelligence & Navigation Assistant**. All write operations remain human-driven through audited UI workflows reached via **Action Shortcuts**.

---

## 1. Alterations to BRD (`BRD - Lukla Operations Engine - v2.2.1 - FINAL.md`)

When elevating this feature from prototype to production, the BRD will be amended as follows:

### A. Add Section 3.3 — Arsitektur Ekstensi: Operational Intelligence Copilot
```markdown
### 3.3 Arsitektur Ekstensi: Operational Intelligence Copilot (Fenced Gateway)

Sistem menyediakan antarmuka asisten percakapan cerdas berbasis Large Language Model (LLM) 
untuk meningkatkan kecepatan akses informasi bagi pemilik pabrik, mandor, dan klien maklon.

* **Ruang Lingkup Fungsional Copilot:**
  1. *Query Semantik Read-Only:* Menjawab pertanyaan seputar status order, saldo bahan baku maklon, 
     kecepatan jalur jahit (throughput), dan ringkasan cacat QC secara interaktif.
  2. *Action Shortcuts (Pintasan Aksi):* Ketika pengguna mengutarakan niat untuk melakukan mutasi data 
     (misal: mencatat hasil cutting, input defect, atau approve payroll), sistem menyajikan hyperlink 
     terarah menuju formulir UI terkait dengan parameter yang terisi otomatis (pre-filled).

* **Batasan Mutlak (Non-Negotiable Boundaries):**
  1. *Dilarang Melakukan Mutasi Otonom:* AI tidak diberikan izin memanggil endpoint mutasi (POST/PUT/DELETE) 
     secara langsung. Semua mutasi wajib melalui interaksi manusia di formulir web terverifikasi.
  2. *Passthrough Konteks Keamanan:* AI Gateway wajib meneruskan Bearer Token pengguna; RLS dan 
     RBAC 8-peran berlaku penuh tanpa ada bypass master-key.
```

### B. Add Non-Functional Requirements in Section 8
- **NFR-AI-01 (Zero Autonomous Mutation):** Model AI tidak memiliki hak eksekusi langsung ke endpoint mutasi buku besar, stok, atau upah.
- **NFR-AI-02 (Multi-Tenant Isolation Passthrough):** Tool query wajib mewarisi `tenant_id` dan `legal_owner_id` dari JWT penanya; tidak ada token ambien atau akses data lintas klien.
- **NFR-AI-03 (Provider Portability):** Antarmuka LLM harus modular (mendukung LLM lokal seperti Ollama/Qwen serta LLM komersial seperti OpenAI/Anthropic).

---

## 2. Alterations to PRD (`PRD - Lukla Operations Engine - v2.0 - Wagile.md`)

### A. Bagian A — Kontrak Ruang Lingkup (A.8 Batasan Sistemik Tambahan)
Add an explicit boundary note under A.8:
> **A.8.4 Batasan Ekstensi Asisten AI:** Fitur AI Copilot beroperasi secara independen di luar domain engine inti sebagai gateway pembaca (read-only facade). Fitur ini berstatus *opt-in* di balik feature flag `AI_COPILOT_ENABLED` dan tidak mengubah struktur skema database PostgreSQL yang telah disetujui.

### B. Bagian B — Backlog Dinamis (Sprint Backlog / Epic Tambahan)
Register a new Epic in Bagian B:
```markdown
### EPIC-AI: Lukla Operational Copilot & MCP Gateway (Fenced Extension)

* **US-AI-01 (Mandor Floor pacer):** Sebagai Kepala Produksi/Mandor, saya ingin menanyakan bottleneck 
  lintasan jahit via chat, agar saya dapat merealokasi penjahit tanpa membuka laporan tabular manual.
* **US-AI-02 (Maklon Self-Service):** Sebagai Klien Maklon, saya ingin menanyakan sisa kain titipan 
  dan progres pesanan saya, agar saya mendapatkan kepastian jadwal kirim secara instan 24/7.
* **US-AI-03 (Executive BI Summary):** Sebagai Owner/Finance, saya ingin meminta rekap estimasi 
  beban upah borongan mingguan via chat sebelum menyetujui payroll hari Sabtu.
* **US-AI-04 (Action Shortcuts Navigation):** Sebagai Pengguna, ketika saya meminta Copilot untuk 
  melakukan suatu pencatatan data, Copilot memberikan kartu pintasan aksi (action hyperlink) 
  ke layar formulir resmi dengan ID pesanan yang relevan.
```

---

## 3. Alterations to Overall Plan Draft (`Overall Plan Draft.md`)

In the system technical architecture:
1. Position the **Copilot Gateway / MCP Server** alongside `17-semantic-search-module.md` in Phase B.
2. Maintain strict decoupling: if the Copilot gateway fails or is disabled (`AI_COPILOT_ENABLED=false`), the manufacturing execution system, payroll engine, and double-entry ledger continue to operate with 100% functionality.
