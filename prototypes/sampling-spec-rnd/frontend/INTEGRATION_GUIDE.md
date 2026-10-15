# 🧵 Sampling & Spec R&D — Integration Guide

**Lukla Operations Engine - Frontend Modul**

---

## 📋 Overview

Modul **Sampling & Spec R&D** adalah frontend **production-ready** yang dibangun dengan:

- **Vite + React 18 + TypeScript**
- **Tailwind CSS** dengan **Apple Human Interface Guidelines (HIG)**
- **33 Backend Endpoints** terintegrasi penuh via FastAPI (port 8009)
- **SF Pro Font Stack**, Glassmorphism, Borderless Design

Modul ini siap untuk **sprint lanjutan** dan mudah di-extend oleh tim untuk proyek Lukla lebih lanjut.

---

## 🎨 Design System — Apple HIG

### Colors
```typescript
// Tailwind config Apple colors
apple-gray6      #F2F2F7  // Background utama
apple-gray5      #E5E5EA
apple-gray       #8E8E93  // Secondary text
apple-label      #000000  // Primary text
apple-secondary  #3C3C43  // Secondary label

accent-blue      #007AFF  // Apple blue (primary actions)
accent-green     #34C759  // Success, complete
accent-orange    #FF9500  // Warning
accent-red       #FF3B30  // Error, danger
accent-purple    #AF52DE  // Spec-related actions
```

### Typography
- **Font:** SF Pro Display / SF Pro Text (fallback: `-apple-system, BlinkMacSystemFont, Segoe UI`)
- **Headers:** font-semibold atau font-bold
- **Body:** font-normal atau font-medium
- **Labels:** text-xs uppercase tracking-wider

### Components
- **Rounded Corners:** `rounded-xl` (16px) atau `rounded-2xl` (20px)
- **Shadow:** Lembut — `shadow-sm`, `shadow-md` (BUKAN border tebal)
- **Glassmorphism:** `bg-white/85 backdrop-blur-xl`
- **Buttons:** Flat color (BUKAN gradient), hover dengan darker shade
- **Cards:** `bg-white` dengan `border-gray-100`, elevated dengan shadow

### Layout Principles
1. **White Space:** Generous spacing antar elemen (py-6, py-8, gap-6)
2. **Borderless:** Minimal border, gunakan shadow atau background color untuk separasi
3. **Touch Targets:** Min height 44-48px untuk mobile
4. **Hierarchy:** Bold headers, light body text untuk contrast

---

## 🗂 Struktur Folder

```
frontend/sampling-spec-rnd/
├── src/
│   ├── components/         # UI components (Button, Card, Input)
│   ├── pages/              # TimeStudyPage, SpecVersionPage
│   ├── services/           # api.ts (33 backend endpoints)
│   ├── styles/             # globals.css (Apple HIG utilities)
│   ├── types/              # TypeScript types
│   ├── App.tsx             # Root dengan navigation tabs
│   └── main.tsx            # Entry point
├── public/                 # Static assets
├── .env                    # Backend URL config
├── tailwind.config.js      # Apple HIG tokens
├── vite.config.ts          # Vite setup dengan path alias
├── package.json
└── README.md
```

---

## 🔌 Backend API Integration

**Base URL (dev):** path relatif `/api/sampling-spec-rnd` via Vite proxy → `http://localhost:8009`.
Diatur lewat `VITE_API_URL` (lihat `.env.example`).

### Endpoints Terintegrasi (33 total)

Semua path di bawah relatif terhadap `/api/sampling-spec-rnd`.

#### Health & Workflow (2)
```typescript
GET    /health
GET    /workflow/summary?tenant_id=...
```

#### Time Study (9)
```typescript
GET    /studies/all?tenant_id=...
POST   /studies/create?tenant_id=&process_id=&process_name=&operator_id=&target_sample_size=
POST   /studies/{id}/start
POST   /studies/{id}/pause
POST   /studies/{id}/resume
POST   /studies/{id}/complete
POST   /studies/{id}/add-sample?cycle_time_ms=&element_name=&is_abnormal=&notes=
GET    /studies/{id}/stats
GET    /studies/{id}/data
```

#### Spec Version (12)
```typescript
GET    /specs/all?tenant_id=...
POST   /specs/create?tenant_id=&spec_id=&spec_name=&created_by=&version_number=
POST   /specs/{id}/record-change?change_type=&parameter_name=&old_value=&new_value=&changed_by=
POST   /specs/{id}/record-drift?parameter_name=&specification_limit=&measured_value=&severity=
POST   /specs/{id}/resolve-drift/{drift_id}?corrective_action=
POST   /specs/{id}/submit-review?reviewer_id=
POST   /specs/{id}/approve?approver_id=
POST   /specs/{id}/activate
GET    /specs/{id}/drift-report
GET    /specs/{id}/drift-analysis
GET    /specs/{id}/change-history
GET    /specs/{id}/data
```

#### Sample Versions (10)
```typescript
GET    /sample-versions/all?tenant_id=...
POST   /sample-versions/create?tenant_id=&article_id=&article_name=&client_id=&created_by=
GET    /sample-versions/article/{article_id}/history?tenant_id=...
GET    /sample-versions/{id}
POST   /sample-versions/{id}/new-revision?revised_by=&revision_note=
POST   /sample-versions/{id}/submit-approval?submitted_by=
POST   /sample-versions/{id}/approve?approved_by=&approval_note=
POST   /sample-versions/{id}/convert-to-order?order_id=&converted_by=
PUT    /sample-versions/{id}/components?updated_by=   (JSON body: { components })
PUT    /sample-versions/{id}/materials?updated_by=    (JSON body: { materials })
```

### API Service Layer

File: `src/services/api.ts`

Semua endpoint di-wrap dalam fungsi TypeScript dengan **standardized response**:

```typescript
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
}

// Example usage:
const res = await api.createStudy({ ... });
if (res.success && res.data) {
  // Handle data
} else {
  // Handle error: res.error
}
```

**Error Handling:** Semua network errors di-catch, backend errors di-forward dalam `res.error`.

### Mock vs Live (ops / ledger / payroll)

Endpoint sampling (studies/specs/sample-versions) **selalu** memakai backend live.
Tiga modul lain berjalan dalam **mode mock (in-memory)** selama service HTTP-nya
belum di-wire oleh tim backend:

| Modul | Client | Flag |
| :--- | :--- | :--- |
| Sewing floor & QC | `src/services/opsApi.ts` | `VITE_LEDGER_MODE` |
| Buku besar (double-entry) | `src/services/ledgerApi.ts` | `VITE_LEDGER_MODE` |
| Payroll & costing | `src/services/payrollApi.ts` | `VITE_LEDGER_MODE` |

Saat backend siap, cukup ubah `.env` (tanpa perubahan UI — bentuk request/response
sudah identik dengan kontrak `openspec/.../contracts/openapi.yaml`):

```env
VITE_LEDGER_MODE=live
VITE_LEDGER_API_URL=http://localhost:8000/api/v1
VITE_LEDGER_TOKEN=<signed JWT>
```

**Verifikasi "berhasil atau tidak":**
1. `npm test` → test `contract.test.ts` memastikan mock tetap sesuai kontrak.
2. Jalankan app; banner kuning **"Mode mock aktif"** (`components/MockModeBanner.tsx`)
   harus **hilang** di halaman Produksi/QC/Ledger/Payroll ketika mode `live`.
3. Buka DevTools → Network: request harus menuju `VITE_LEDGER_API_URL`, bukan mock.

---

## 🔐 Portal Auth (Login / Registrasi / Lupa Akses)

Halaman portal (`pages/PortalAuthView.tsx`) tampil sebagai **auth gate** sebelum dashboard:
selama belum ada sesi, `App.tsx` hanya merender halaman portal. Setelah login, dashboard lama
muncul seperti biasa.

**Alur:**
1. **Registrasi** — isi Nama, Email, Nomor karyawan, NIK/KTP (16 digit), Nomor HP, Departemen,
   Password + Konfirmasi, centang persetujuan. Akun masuk status **pending**.
2. **Verifikasi Admin IT** — login sebagai admin → chapter **Administrasi → Persetujuan Akses** →
   Setujui/Tolak. Hanya setelah disetujui akun bisa login.
3. **Login** — identitas bisa berupa **Nomor karyawan, NIK/KTP, email, atau Nomor HP** + password.
4. **Lupa akses** — masukkan identitas → kode OTP dikirim ke email (mode dev: tercetak di log
   backend) → masukkan OTP + password baru.
5. **Ganti password** — Settings → kartu **Keamanan** (sesi dicabut, lalu login ulang).

**Endpoint** (prefix `/api/auth`, `services/authApi.ts`):
```
POST /register  POST /login  POST /logout  GET /me
POST /change-password  POST /forgot-password  POST /reset-password
GET  /admin/registrations  POST /admin/registrations/{id}/approve|reject
```

**Akun admin default:** `admin@luka.local` / `Admin#12345` (ubah via `.env` backend:
`SEED_ADMIN_EMAIL`, `SEED_ADMIN_PASSWORD`).

**Layer terkait:** `services/authRules.ts` (validasi murni, diuji `tests/auth.test.ts`),
`services/authSession.ts` (token opaque di memori + `sessionStorage`), `services/identity.ts`
(`actor()` membaca pengguna aktif).

**"Did it work?" check:**
1. `curl http://localhost:8009/api/auth/health` → `{"status":"healthy","module":"portal-auth",...}`.
2. Buka `http://localhost:3009` → halaman portal muncul (bukan dashboard).
3. Registrasi → login gagal (pending) → setujui sebagai admin → login berhasil → dashboard muncul.

---

## 🚀 Development Workflow

### Prerequisites
- Node.js 18+
- Backend running di port 8009

### Setup
```bash
cd frontend/sampling-spec-rnd
npm install
```

### Environment Variables
File `.env` (lihat `.env.example`):
```env
# Path relatif agar lewat Vite proxy (JANGAN pakai http://localhost:...)
VITE_API_URL=/api/sampling-spec-rnd
VITE_AUTH_URL=/api/auth
```

### Development
```bash
npm run dev         # Start dev server (port 3009)
npm run build       # Production build
npm run preview     # Preview production build
npm run type-check  # TypeScript validation
npm run lint        # ESLint (0 warnings allowed)
npm test            # Unit + contract tests (node --test)
```

### Testing Backend Connection
1. Start backend: `cd backend/sampling-spec-rnd && python src/main.py`
2. Start frontend: `npm run dev`
3. Open browser: `http://localhost:3009`
4. Check status indicator di navbar (hijau = connected)

---

## 🧪 Manual Testing Checklist

### Time Study Flow
- [ ] Buat studi baru dengan nama proses
- [ ] Klik "▶ Mulai" — status berubah jadi "Berjalan"
- [ ] Input cycle time (ms) → klik "+ Tambah Sampel"
- [ ] Counter berubah (0/30 → 1/30)
- [ ] Progress bar bertambah
- [ ] Rata-rata cycle time update otomatis
- [ ] Klik "⏸ Jeda" — status jadi "Dijeda"
- [ ] Klik "▶ Lanjutkan" — kembali "Berjalan"
- [ ] Klik "✓ Selesai" — status jadi "Selesai"
- [ ] Stats panel muncul setelah completed
- [ ] List studi menampilkan semua studi dengan progress bar mini

### Spec Version Flow
- [ ] Buat spec baru dengan nama
- [ ] Tab "Catat Perubahan" → input parameter, old/new value → simpan
- [ ] Tab "Catat Drift" → input parameter, limit, measured → catat
- [ ] Drift card muncul dengan severity badge
- [ ] Klik "Submit Review" → status jadi "Review"
- [ ] Klik "✓ Setujui" → status jadi "Disetujui"
- [ ] Klik "⚡ Aktifkan" → status jadi "Aktif"
- [ ] Tab "Riwayat Perubahan" menampilkan semua changes
- [ ] Tab "Analisis Drift" menampilkan risk score & trend

### Dashboard
- [ ] Summary cards menampilkan angka dari backend
- [ ] Backend status indicator update setiap 30 detik
- [ ] Panduan cepat readable dan clear

---

## 🔧 Extending untuk Modul Lain

### Tambah Modul Baru (contoh: Payroll)

1. **Buat folder modul:**
```bash
frontend/
├── sampling-spec-rnd/    # Existing
└── payroll/              # New
    ├── src/
    │   ├── components/
    │   ├── pages/
    │   ├── services/api.ts
    │   └── App.tsx
    ├── tailwind.config.js  # Copy dari sampling-spec-rnd
    ├── package.json
    └── vite.config.ts
```

2. **Copy design system:**
```bash
cp sampling-spec-rnd/tailwind.config.js payroll/
cp sampling-spec-rnd/src/styles/globals.css payroll/src/styles/
```

3. **Reuse components:**
```typescript
// Import shared components
import { Button, Card, Input } from '@/components';
```

4. **API service pattern:**
```typescript
// payroll/src/services/api.ts
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8010';

export async function getPayrollData(id: string): Promise<ApiResponse<PayrollData>> {
  try {
    const res = await fetch(`${API_BASE}/payroll/${id}`);
    const json = await res.json();
    return { success: res.ok, data: res.ok ? json : undefined, error: res.ok ? undefined : json.detail };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}
```

5. **Konsisten dengan Apple HIG:**
- Background: `bg-apple-gray6`
- Cards: `bg-white rounded-2xl shadow-sm`
- Buttons: Apple accent colors (`accent-blue`, `accent-green`, dll)
- Font: SF Pro stack dari globals.css
- Spacing: py-8, gap-6 (generous)

---

## 📦 Production Build

### Build untuk production:
```bash
npm run build
# Output: dist/
```

### Serve via Nginx (example):
```nginx
server {
  listen 80;
  server_name sampling.lukla.com;
  root /var/www/sampling-spec-rnd/dist;
  
  location / {
    try_files $uri $uri/ /index.html;
  }
  
  # Proxy backend
  location /api/ {
    proxy_pass http://localhost:8009/;
  }
}
```

### Environment Variables (production):
```env
VITE_API_URL=https://api.lukla.com/api/sampling-spec-rnd
```

---

## 🛠 Troubleshooting

### Frontend tidak connect ke backend
1. Cek backend running: `curl http://localhost:8009/health`
2. Cek CORS settings di backend `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3009"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
3. Cek `.env` frontend sesuai port backend

### TypeScript errors
```bash
npm run type-check  # Validate semua types
```

### Build errors
```bash
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Styling tidak sesuai
1. Cek `tailwind.config.js` ada Apple colors
2. Cek `globals.css` di-import di `App.tsx`
3. Restart dev server setelah ubah config

---

## 📚 Dependencies Reference

```json
{
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "vite": "^4.4.0",
  "typescript": "^5.1.0",
  "tailwindcss": "^3.3.0"
}
```

**Zero external dependencies** untuk business logic — murni React + Fetch API.

---

## 🎯 Next Steps untuk Tim

### Sprint 2: Executive Operations Dashboard
1. Copy folder structure dari `sampling-spec-rnd`
2. Reuse `components/`, `tailwind.config.js`, `globals.css`
3. Buat `pages/DashboardPage.tsx` dengan grafik per 30 menit
4. Integrate dengan backend `/dashboard/` endpoints
5. Tambahkan real-time updates via polling atau WebSocket

### Sprint 3: Workspace Payroll
1. Sama seperti Sprint 2, copy structure
2. Focus: tabel payroll dengan sorting/filtering
3. Apple HIG table: borderless dengan `divide-y divide-gray-100`
4. Reuse Button, Card, Input components

### Sprint 4: Floor Terminal (Tablet)
1. Responsive design: larger touch targets (min-h-12)
2. Optimize untuk tablet landscape (1024x768)
3. Offline-first: localStorage fallback jika backend down
4. Large fonts untuk readability di lantai produksi

---

## 📞 Support

**Dokumentasi Backend:** `backend/sampling-spec-rnd/MODULES_REFERENCE.md`

**Design Guideline:** `openspec/changes/lukla-ops-engine-planning/artifacts/design_guideline.md`

**PRD:** `openspec/changes/lukla-ops-engine-planning/artifacts/lukla_PRD_V.1.0.md`

---

**Built with ❤️ for Lukla Operations Engine**
