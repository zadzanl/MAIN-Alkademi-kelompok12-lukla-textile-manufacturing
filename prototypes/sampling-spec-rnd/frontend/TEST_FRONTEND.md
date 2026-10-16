# 🧪 Panduan Test Frontend - Sampling & Spec R&D

## Prerequisites

Pastikan kedua service running:

**Terminal 1 - Backend:**
```bash
cd backend/sampling-spec-rnd
.\venv\Scripts\activate
uvicorn src.main:app --reload --port 8009
```

**Terminal 2 - Frontend:**
```bash
cd frontend/sampling-spec-rnd
npm run dev
```

**Buka browser:** http://localhost:3009

---

## BAGIAN 1 — Connection Status

### Test 1.1: Backend Connected
**Langkah:**
1. Buka http://localhost:3009
2. Lihat pojok kanan atas

**Expected:**
```
🟢 Backend Connected   ← hijau, backend running
```

**Jika backend mati:**
```
🟡 Local Storage Mode  ← kuning, mode offline
```

---

## BAGIAN 2 — Create Study

### Test 2.1: Buat study baru (happy path)
**Langkah:**
1. Lihat card "Create New Study"
2. Ketik nama proses di input: `Jahit Baju`
3. Klik tombol **"Create Study"**

**Expected:**
- Tombol menampilkan spinner saat loading
- Study baru muncul di list "Active Studies"
- Input field kembali kosong setelah berhasil
- Backend log: `POST /api/sampling-spec-rnd/studies/create 200 OK`

---

### Test 2.2: Input kosong (validasi)
**Langkah:**
1. Kosongkan input field
2. Klik **"Create Study"**

**Expected:**
- Tidak ada aksi / tidak ada study dibuat
- Tidak ada error message (input kosong langsung di-ignore)

---

### Test 2.3: Buat beberapa study sekaligus
**Langkah:**
1. Buat study `Potong Kain`
2. Buat study `Pasang Kancing`
3. Buat study `Quality Check`

**Expected:**
- Semua muncul di "All Studies" list di bawah
- Counter: `All Studies (3)`

---

## BAGIAN 3 — SamplingCard & Study Actions

### Test 3.1: Tampilan SamplingCard
**Langkah:**
1. Setelah buat study, lihat card yang muncul di "Active Studies"

**Expected card menampilkan:**
- Nama proses (mis. "Jahit Baju")
- Study ID (UUID format)
- Badge status: `draft` (abu-abu)
- Progress bar: `0 / 30`
- Stats: Mean Time `0.00ms`, Std Dev `0.00ms`
- Tombol **"Start Study"**

---

### Test 3.2: Start Study
**Langkah:**
1. Di SamplingCard, klik **"Start Study"**

**Expected:**
- Badge status berubah: `draft` → `in progress` (biru)
- Tombol berubah dari "Start Study" → muncul **"Pause"** + **"Complete"**
- Muncul card baru "Add Sample" di bawah

---

### Test 3.3: Pause Study
**Langkah:**
1. Dari status `in progress`, klik **"Pause"**

**Expected:**
- Badge: `in progress` → `paused` (orange)
- Tombol berubah: "Pause"+"Complete" → **"Resume"** + **"Complete"**
- Card "Add Sample" hilang (tidak bisa input saat paused)

---

### Test 3.4: Resume Study
**Langkah:**
1. Dari status `paused`, klik **"Resume"**

**Expected:**
- Badge: `paused` → `in progress` (biru)
- Card "Add Sample" muncul kembali

---

## BAGIAN 4 — Add Sample

### Test 4.1: Tambah sample (normal)
**Langkah:**
1. Pastikan study dalam status `in progress`
2. Di card "Add Sample", input: `3500`
3. Klik **"Add Sample"**

**Expected:**
- Input kembali kosong
- Progress bar di SamplingCard bertambah: `1 / 30`
- Mean Time terupdate: `3500.00ms`
- Backend log: `POST /api/sampling-spec-rnd/studies/{id}/add-sample 200 OK`

---

### Test 4.2: Tambah beberapa sample
**Langkah:**
1. Tambah sample berturut-turut: `3200`, `3800`, `3400`, `3600`

**Expected setelah 5 sample:**
- Progress: `5 / 30`
- Mean Time: `3500.00ms` (rata-rata dari semua)
- Std Dev mulai muncul nilainya

---

### Test 4.3: Input kosong / bukan angka
**Langkah:**
1. Kosongkan input cycle time
2. Klik **"Add Sample"**

**Expected:**
- Tidak ada aksi (dikosongkan karena validasi `!cycleTime.trim()`)

---

### Test 4.4: Tidak bisa add sample saat bukan in_progress
**Langkah:**
1. Pause study
2. Perhatikan card "Add Sample"

**Expected:**
- Card "Add Sample" **hilang** saat status bukan `in_progress`
- Tidak ada cara untuk input sample saat paused

---

## BAGIAN 5 — Complete Study

### Test 5.1: Complete study
**Langkah:**
1. Dari status `in progress`, klik **"Complete"**

**Expected:**
- Badge berubah: `in progress` → `completed` (hijau)
- Card "Add Sample" hilang
- Tombol aksi hilang (tidak ada action lagi)
- Di list "All Studies", status berubah ke `completed`
- Study tidak lagi muncul di "Active Studies"

---

### Test 5.2: Complete dari status paused
**Langkah:**
1. Pause study
2. Klik **"Complete"** (masih tersedia saat paused)

**Expected:**
- Study langsung berubah ke `completed`

---

## BAGIAN 6 — All Studies List

### Test 6.1: Click study di list
**Langkah:**
1. Buat beberapa study
2. Klik salah satu study di bagian "All Studies"

**Expected:**
- Study tersebut menjadi `selectedStudy`
- Jika statusnya `in_progress`, card "Add Sample" muncul untuk study itu

---

### Test 6.2: Status badge warna di list
**Expected warna per status:**
- `draft` → abu-abu
- `in progress` → biru
- `paused` → orange
- `completed` → hijau

---

## BAGIAN 7 — Offline Mode

### Test 7.1: Test tanpa backend
**Langkah:**
1. Stop backend (Ctrl+C di terminal backend)
2. Refresh frontend http://localhost:3007
3. Tunggu 5 detik

**Expected:**
- Status berubah: `🟡 Local Storage Mode`
- Masih bisa buat study (pakai local state, bukan API)
- Study tetap bisa dibuat dan di-manage
- **Tidak ada error merah** yang mengganggu

---

### Test 7.2: Reconnect backend
**Langkah:**
1. Start backend lagi
2. Refresh halaman

**Expected:**
- Status kembali: `🟢 Backend Connected`

---

## BAGIAN 8 — Design System & UI

### Test 8.1: Glassmorphism effect
**Lihat:**
- Card punya efek frosted glass (blur + semi-transparent)
- Background gradient ungu-ke-biru terlihat menembus card
- Border tipis putih transparan di card

**Expected:**
- Tidak lag saat scroll
- Blur smooth, tidak patah-patah

---

### Test 8.2: Button states
**Test setiap tombol:**
- **Normal:** warna ungu solid dengan shadow
- **Hover:** warna sedikit lebih gelap
- **Click:** scale 95% sesaat (ada animasi press)
- **Loading:** muncul spinner + teks "Loading..."
- **Disabled:** opacity 50%, cursor not-allowed

---

### Test 8.3: Input states
**Test input field:**
- **Normal:** border abu-abu
- **Hover:** border sedikit lebih gelap
- **Focus:** border berubah ungu + outline ungu

---

### Test 8.4: Rounded corners
**Expected:**
- Cards: `rounded-xl` (16px)
- Buttons: `rounded-lg` (8px)
- Inputs: `rounded-lg` (8px)
- Progress bar: `rounded-full`
- Badge status: `rounded-full`

---

### Test 8.5: Touch target size (tablet)
**Expected semua tombol:**
- Minimum height: 48px (`min-h-12`)
- Cukup besar untuk disentuh dengan jari di tablet

---

## BAGIAN 9 — Performance (Tablet Test)

### Test 9.1: Scroll performance
**Langkah:**
1. Buat 10+ study
2. Scroll halaman naik-turun dengan cepat

**Expected:**
- Tidak ada lag/stuttering
- Animasi tetap smooth

---

### Test 9.2: Rapid button clicks
**Langkah:**
1. Klik "Create Study" berkali-kali cepat

**Expected:**
- Hanya 1 study yang dibuat (throttle 300ms aktif)
- Tidak crash atau error

---

### Test 9.3: Rapid "Add Sample"
**Langkah:**
1. Klik "Add Sample" berkali-kali cepat

**Expected:**
- Debounce 100ms mencegah duplicate request
- Hanya 1 sample ditambah per klik

---

## BAGIAN 10 — Browser DevTools Check

### Test 10.1: Tidak ada console error
**Langkah:**
1. Buka DevTools: F12 → Console
2. Lakukan semua aksi di UI

**Expected:**
- Tidak ada error merah
- Mungkin ada warning kuning (acceptable)

---

### Test 10.2: Network requests
**Langkah:**
1. F12 → Network tab
2. Buat study, add sample, dll

**Expected API calls:**
```
POST /api/sampling-spec-rnd/studies/create       → 200 ✅
GET  /api/sampling-spec-rnd/studies/{id}/data    → 200 ✅
POST /api/sampling-spec-rnd/studies/{id}/start   → 200 ✅
POST /api/sampling-spec-rnd/studies/{id}/add-sample → 200 ✅
GET  /api/sampling-spec-rnd/studies/{id}/data    → 200 ✅
```

---

### Test 10.3: Tidak ada 404 atau 500 error
**Expected:**
- Semua request di Network tab: status 200
- Tidak ada request merah (4xx/5xx)

---

## ✅ Test Checklist (Quick Reference)

### Connection
- [ ] Status "🟢 Backend Connected" muncul saat backend running
- [ ] Status "🟡 Local Storage Mode" saat backend mati

### Create Study
- [ ] Input nama → klik Create → study muncul di list
- [ ] Input kosong → tidak ada aksi

### Study Actions
- [ ] Start Study → status "in progress", muncul Pause + Complete
- [ ] Pause → status "paused", muncul Resume + Complete
- [ ] Resume → status "in progress" kembali
- [ ] Complete → status "completed", pindah ke All Studies

### Add Sample
- [ ] Input cycle time → Add Sample → progress bertambah
- [ ] Mean Time terupdate setelah tambah sample
- [ ] Input kosong → tidak ada aksi
- [ ] Card Add Sample hilang saat paused/completed

### UI & Design
- [ ] Glassmorphism terlihat (blur + semi-transparent)
- [ ] Gradient background ungu-biru
- [ ] Rounded corners di semua elemen
- [ ] Button: hover darker, click scale-down, loading spinner
- [ ] Progress bar smooth
- [ ] Status badge warna berbeda per status

### Performance
- [ ] Tidak lag saat scroll
- [ ] Create Study berkali-kali cepat → hanya 1 study (throttle)
- [ ] Tidak ada console error di DevTools

### Network
- [ ] Semua API calls 200 OK di Network tab
- [ ] Tidak ada request 4xx/5xx

---

## 🐛 Bug yang Mungkin Ditemukan

| Gejala | Kemungkinan Penyebab | Fix |
|--------|---------------------|-----|
| 🟡 Local Storage Mode padahal backend running | Backend di port berbeda | Cek port 8007 |
| Create Study tidak muncul | API error | Cek Network tab |
| Add Sample tidak update stats | Data fetch gagal | Cek console error |
| Blur tidak terlihat | Browser tidak support | Coba Chrome/Edge |
| Tombol tidak responsif | Throttle/debounce | Normal behavior |

---

**Last Updated:** October 13, 2026
**Frontend URL:** http://localhost:3009
**Backend URL:** http://127.0.0.1:8009
