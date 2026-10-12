## 5. INSTRUKSI PENGEMBANGAN & PEMBAGIAN TUGAS (TASK ASSIGNMENT)

Berikut adalah pembagian tugas berdasarkan kesepakatan sprint (Berdasarkan acuan target Deliverables Kamis).

**Mohon setiap Dev berfokus pada Scope masing-masing agar integrasi berjalan lancar!**

| Anggota Tim | Fokus Area & Tanggung Jawab (WIP) | Target Deliverables (Kamis) |
| :--- | :--- | :--- |
| **Dev 1 (Frontend & UI/UX)** | Membangun Dashboard Admin, Grid Gudang, dan antarmuka analitik Workspace Payroll. | UI View 1, 3, dan 6 selesai. Integrasi tabel dengan Supabase API untuk baca data stok. |
| **Dev 2 (Frontend "Floor")** | Fokus eksklusif pada Terminal Input 30 Menit, Terminal QC, dan Form Time Study. | UI View 2, 4, dan 5 selesai. Antarmuka *touch-friendly* berjalan lancar di layar tablet. (Pastikan target sentuh min. 48px). |
| **Dev 3 (Backend & DB Architect)** | Merancang Skema Tabel, Menerapkan *Row Level Security* (RLS), mengatur RBAC 8 peran. | Supabase siap pakai. **Skenario Pengujian 1** (Blokir Kontaminasi) berfungsi di level DB (*Trigger berjalan*). |
| **Dev 4 (Logic, QA & DevOps)** | Merangkai algoritma Mesin Payroll (gaji, uang makan, overhead), testing skenario, deployment. | Algoritma **Skenario 2 & 3** (Payroll & Bonus QC) lolos uji. Vercel & CI/CD beroperasi. |

### Catatan Penting untuk Eksekusi:

1. **Frontend (Dev 1 & Dev 2):** Jangan lupa terapkan desain ala Apple. Gunakan sudut membulat, pastikan kontras jelas, dan optimalkan efek *glassmorphism* tanpa mengorbankan performa (jangan sampai lag di tablet pabrik).
2. **Backend (Dev 3):** Integritas data adalah harga mati. Pastikan Trigger `validate_material_dispatch()` yang memblokir kontaminasi silang tidak bisa di-*bypass* oleh siapapun.
3. **Logic (Dev 4):** Perhatikan pembulatan nilai pecahan saat membagi bonus QC 3 arah. Sisa pembulatan (walau Rp 1) harus masuk ke cadangan pabrik, bukan mematahkan aplikasi.