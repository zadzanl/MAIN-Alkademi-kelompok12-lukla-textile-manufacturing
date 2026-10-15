# Visual QA Checklist — Sampling & Spec R&D Frontend

Tujuan: memverifikasi hasil perapian desain (token, dark mode, badge, responsif) **di browser**.
Tidak ada langkah otomatis di sini — ini daftar cek manual.

## Cara menjalankan

```powershell
# Terminal 1 — backend
cd prototypes\sampling-spec-rnd\backend
.\venv\Scripts\activate
uvicorn src.main:app --reload --port 8009

# Terminal 2 — frontend
cd prototypes\sampling-spec-rnd\frontend
npm run dev            # http://localhost:3009
```

Di setiap halaman, cek **mode terang DAN mode gelap** (tombol Dark/Light Mode di sidebar, atau menu Pengaturan).

## A. Animasi (WAJIB tetap ada — jangan sampai hilang)

- [ ] **Sampul sidebar**: klik salah satu bab (mis. "Sampling & Studi") → daftar item terbuka dengan animasi slide-down halus.
- [ ] **Halaman buku**: pindah antar menu → konten masuk dengan efek page-turn (rotateY halus).
- [ ] **Cross-fade tema**: klik toggle Dark/Light → warna bertransisi lembut (tidak "patah").
- [ ] **Hover item sidebar**: geser halus ke kanan saat di-hover.
- [ ] **Modal**: buka "Buat Studi Baru" → panel naik (slide-up) + backdrop blur.

## B. Konsistensi warna & badge

- [ ] Badge status di tabel (Draft/Berjalan/Selesai, dsb.) punya warna latar+teks yang konsisten antar halaman.
- [ ] Di **mode gelap**, badge tetap terbaca (tidak ada teks gelap di latar gelap / sebaliknya).
- [ ] Tombol primer biru (`#0071e3`) seragam di semua halaman.
- [ ] Tidak ada elemen yang tiba-tiba "menghilang" di mode gelap (teks/ikon hilang).

## C. Halaman (cek terang + gelap)

- [ ] Overview (KPI, chart, mini-table)
- [ ] Versi Sample
- [ ] Stopwatch
- [ ] Studi Aktif
- [ ] Produksi & Tally (+ mode terminal)
- [ ] Studi Waktu (list + tombol Buat)
- [ ] Daftar Studi
- [ ] Versi Spec (list + tombol Buat)
- [ ] Daftar Spec
- [ ] Analisis Drift
- [ ] Laporan
- [ ] Quality Control (+ mode terminal)
- [ ] Buku Besar (mock)
- [ ] Payroll & Costing (mock)
- [ ] Pengaturan (toggle tema, pemilih font, info sistem)

## D. Komponen & form

- [ ] Header: judul, subtitle, caption status backend (hijau "terhubung" / merah "tidak"), search, avatar.
- [ ] Input search global: fokus punya ring biru; background benar di gelap.
- [ ] Tabel: header, hover baris, teks sel, kode ID.
- [ ] Tombol: normal / hover / active (press) / disabled.
- [ ] Modal: Escape menutup, klik backdrop menutup, fokus masuk ke dialog.

## E. Responsif (tablet & ponsel)

- [ ] Lebar tablet (~768–1024px): grid KPI & tabel rapi, tidak overflow.
- [ ] Lebar ponsel (<640px): sidebar tersembunyi; tombol **hamburger** muncul di header → membuka sidebar sebagai drawer; klik menu menutup drawer; klik backdrop menutup drawer.
- [ ] Touch target tombol ≥ 48px.

## F. Preferensi pengguna

- [ ] Toggle tema tersimpan setelah refresh (localStorage `ui-dark`).
- [ ] Pilihan font tersimpan setelah refresh (localStorage `ui-font`), dan tiap font berubah.

## G. Performa & konsol

- [ ] Tidak ada error merah di DevTools Console saat menelusuri semua halaman.
- [ ] Tidak ada request 4xx/5xx pada Network (mode sampling live).
- [ ] Scroll tetap halus.

## Catatan
- Ledger & Payroll berjalan **mock** (in-memory) sampai backend tim siap; label "Mock" muncul di view terkait.
- Jika ada yang tidak sesuai, catat: halaman + mode (terang/gelap) + komponen.
