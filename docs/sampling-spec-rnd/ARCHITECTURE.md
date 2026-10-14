# Sampling & Spec R&D — Prototype Architecture & Integration

Dokumentasi ini merangkum struktur teknis, rancangan komponen, pola integrasi, dan arsitektur data dari modul prototype **Sampling & Spec R&D**.

---

## 🏗️ Ringkasan Komponen

Modul prototype ini mengimplementasikan dua fungsi utama manufaktur:
1. **Time Study Recording:** Perekaman sampel durasi kerja penjahit/operator, deteksi pencilan (outliers), dan perhitungan rata-rata standar waktu siklus.
2. **Specification Version Tracking:** Pencatatan versi spesifikasi produk (desain pola, ukuran, toleransi), pelacakan riwayat revisi, dan deteksi parameter drift antar versi sample.

---

## 📂 Struktur Modul Prototype

```text
prototypes/sampling-spec-rnd/
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── routes.py                # REST endpoints (FastAPI)
│   │   │   └── __init__.py
│   │   ├── models/
│   │   │   ├── spec_version_tracker.py  # Data models untuk versi spesifikasi
│   │   │   ├── time_study_recorder.py   # Data models untuk sample waktu
│   │   │   └── __init__.py
│   │   ├── services/
│   │   │   ├── sampling_rnd_workflow.py # Logika alur kerja sampling
│   │   │   └── __init__.py
│   │   └── utils/
│   │       ├── spec_version_patterns.py # Algoritma analisis drift spesifikasi
│   │       ├── time_study_patterns.py   # Algoritma analisis statistik sampel
│   │       └── __init__.py
│   ├── run_backend.bat                  # Script startup Windows
│   ├── requirements.txt                 # Dependencies Python
│   ├── README.md                        # Dokumentasi teknis backend
│   └── INTEGRATION_ANALYSIS.md          # Analisis integrasi API
│
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── Button.tsx               # Apple design style buttons
    │   │   ├── Card.tsx                 # Glasmorphism card container
    │   │   ├── Input.tsx                # Accessible touch-friendly inputs
    │   │   ├── SamplingCard.tsx         # Card sampling display
    │   │   ├── SpecVersionTracker.jsx   # UI pelacakan revisi spesifikasi
    │   │   └── index.ts
    │   ├── pages/
    │   │   └── TimeStudyPage.tsx        # Stopwatch & batch sample collection
    │   ├── services/
    │   │   └── api.ts                   # Typed API service client
    │   ├── utils/
    │   │   └── time-study-patterns.js   # Client-side statistical helpers
    │   ├── hooks/
    │   │   ├── useLocalStorage.ts       # Caching offline
    │   │   └── usePerformance.ts        # Debounce & tablet rendering guard
    │   └── styles/
    │       ├── design-system.ts         # Token warna, spacing, radius Apple
    │       └── globals.css              # Glassmorphic utilities
    ├── run_frontend.bat                 # Script startup Windows
    ├── vite.config.ts                   # Konfigurasi Vite & proxy backend
    └── package.json                     # Dependencies frontend
```

---

## 🔌 API & Alur Integrasi

- **Base URL:** `/api/sampling-spec-rnd`
- **Proxy Dev Server:** Vite development server pada port `3009` meneruskan panggilan `/api/*` langsung ke server backend di `http://localhost:8009`.
- **Endpoints Utama:**
  - `GET /health` dan `GET /api/sampling-spec-rnd/health`: Health status.
  - `POST /api/sampling-spec-rnd/time-studies`: Inisialisasi sesi time study baru.
  - `POST /api/sampling-spec-rnd/time-studies/{id}/samples`: Mencatat satu observasi sampel durasi.
  - `GET /api/sampling-spec-rnd/time-studies/{id}/stats`: Mengambil statistik (mean, std dev, outliers).
  - `POST /api/sampling-spec-rnd/spec-versions`: Membuat draft spesifikasi baru.
  - `POST /api/sampling-spec-rnd/spec-versions/{id}/drift`: Menghitung deviasi parameter terhadap baseline.

---

## 🎨 Pedoman Desain Antarmuka (Apple Design System)

1. **Touch Targets:** Minimal 48×48px untuk kemudahan interaksi di lingkungan pabrik dengan sarung tangan kerja.
2. **Visual Hierarchy:** Penggunaan latar semi-transparan (`backdrop-blur-md`), sudut melengkung halus (`rounded-2xl`), dan kontras teks tinggi standar WCAG AA+.
3. **Optimasi Tablet:** Event input didebounce untuk menjamin fluiditas render 60 FPS di perangkat tablet industri.
