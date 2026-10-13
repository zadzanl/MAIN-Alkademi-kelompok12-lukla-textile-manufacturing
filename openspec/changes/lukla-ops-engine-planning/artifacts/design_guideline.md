## 2. DESIGN GUIDELINES (Apple Design Language)

Antarmuka harus terasa premium, intuitif, dan responsif. Karena target utamanya adalah tablet industri di lantai pabrik, kita akan mengadopsi prinsip **Apple Human Interface Guidelines (HIG)** dengan penyesuaian fungsionalitas pabrik.

### 2.1 Tipografi & Keterbacaan
*   **Font Family:** San Francisco Pro (SF Pro Display untuk *Heading*, SF Pro Text untuk *Body*).
*   **Hierarki:** Gunakan *font-weight* (Bold, Semibold, Regular) untuk membedakan hierarki informasi, bukan hanya ukuran.
*   **Keterbacaan:** Kontras tinggi pada teks angka (terutama di Floor Terminal dan Payroll).

### 2.2 Warna & Material (Glassmorphism)
*   **Background:** Bersih. Gunakan warna abu-abu sangat terang (misal: `#F2F2F7` khas iOS) untuk latar belakang utama, dan Putih Murni (`#FFFFFF`) untuk *card* konten.
*   **Material:** Gunakan efek *translucency* (blur/acrylic) ringan pada *header/navbar* dan *modal popup* agar terasa memiliki kedalaman (depth).
*   **Semantic Colors (Gunakan Sistem Warna Apple):**
    *   **Success (Lolos/Pass):** Apple Green (`#34C759`)
    *   **Warning (Repair/Pending):** Apple Orange (`#FF9500`) atau Yellow (`#FFCC00`)
    *   **Danger (Reject/Scrap):** Apple Red (`#FF3B30`)
    *   **Primary Action:** Apple Blue (`#007AFF`)

### 2.3 Komponen & Interaksi (Touch-First)
*   **Corner Radius:** Gunakan sudut membulat (12px hingga 16px) pada semua *card*, *modal*, dan *button* (khas squircle Apple).
*   **Shadows:** Gunakan *drop shadow* yang sangat halus dan menyebar luas untuk memisahkan lapisan UI, bukan bayangan tajam.
*   **Touch Targets (CRITICAL untuk Floor Terminal):** Sesuai standar NFR BRD, area sentuh (*button*, *stepper* +/-) minimal berukuran **48x48 piksel** agar mudah ditekan mandor yang mungkin memakai sarung tangan atau bekerja cepat.
*   **Feedback:** Berikan haptic feedback (jika didukung perangkat) atau animasi *micro-interaction* (seperti efek *scale-down* ringan saat tombol ditekan).

---
## 3. STRUKTUR FRONTEND (React / Next.js)

Kita akan menggunakan **Next.js (App Router)** dengan **Tailwind CSS** dan komponen berbasis **Radix UI/shadcn** yang dikustomisasi dengan tema Apple (SF Pro, rounded, soft shadows).

```text
/src
 ├── /app                   # Next.js App Router (Halaman Utama)
 │    ├── /dashboard        # View 01: Executive Dashboard
 │    ├── /sample-tracker   # View 02: Time Study
 │    ├── /warehouse        # View 03: Inventory Grid
 │    ├── /floor            # View 04: 30-Min Terminal (Tablet UI Focus)
 │    ├── /qc               # View 05: QC Scanner (Tablet UI Focus)
 │    └── /payroll          # View 06: Workspace & Costing
 ├── /components
 │    ├── /ui               # Reusable Apple-styled UI (Buttons, Cards, Modals)
 │    ├── /layout           # Sidebar, Navbar (Glassmorphic)
 │    └── /domain           # Domain specific components (cth: TallyCounter, QCScanner)
 ├── /hooks                 # Custom React Hooks (usePayroll, useSupabase, useTally)
 ├── /lib
 │    ├── supabase.ts       # Supabase Client Initialization
 │    └── utils.ts          # Helper (Currency formatter, Date formatter)
 ├── /store                 # Global State (Zustand) untuk caching data offline sementara
 └── /styles
      └── globals.css       # Tailwind config & Font SF Pro imports


      /supabase
 ├── /migrations            # Skema Database & Triggers
 │    ├── 01_schema_rbac.sql         # 8 Role Enum & User Profiles
 │    ├── 02_schema_ledger.sql       # Chart of Accounts, Journal Entries (Append-only)
 │    ├── 03_schema_inventory.sql    # Multi-tenant Stock Lots (Client_ID, Order_ID)
 │    ├── 04_rls_policies.sql        # Row Level Security untuk isolasi Client B2B
 │    └── 05_trigger_guardrail.sql   # PL/pgSQL function: validate_material_dispatch()
 ├── /functions             # Edge Functions (Deno/Node.js)
 │    ├── calculate-payroll          # Algoritma Upah, Uang Makan, Bonus QC
 │    └── allocate-overhead          # Skrip bulanan pembagian biaya utilitas
 └── /tests                 # DB Logic Tests (pgTAP)