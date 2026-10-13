# PRD — Lukla Operations Engine (Wagile)

| Atribut | Nilai |
| :---- | :---- |
| Nama Proyek | Lukla Operations Engine |
| Entitas Bisnis | Lukla Manufacturing (Fasilitas Konveksi Ciwidey) x Snøhund |
| Versi Dokumen | 2.0 |
| Status | Draft — Menunggu Persetujuan |
| Klasifikasi | Internal Confidential / Restricted Enterprise Blueprint |
| Pendekatan | Wagile — Kontrak Tetap (Bagian A) + Backlog Agile (Bagian B) |
| Sumber Kebenaran (Source of Truth) | BRD v2.3.0 — `openspec/changes/BRD - Lukla Operations Engine - v2.2.1 - FINAL.md` |
| Pendahulu | PRD v1.3 (telah digantikan oleh dokumen ini) |

**Cara membaca dokumen ini** — struktur Bagian A mengikuti kerangka PRD Confluence (tabel kepala dokumen, tujuan, asumsi, pertanyaan terbuka, di luar ruang lingkup) dan enam pertanyaan pembingkaian dari Lenny Rachitsky (Deskripsi / Masalah / Mengapa / Keberhasilan / Audiens / Apa). Dokumen ini **merujuk** BRD, bukan menyalinnya: matriks panjang (RBAC lengkap, rumus penuh, spesifikasi UI lengkap) tetap hidup di BRD dan diarahkan lewat tautan bagian.

> **Aturan dua lapis:**
> - **Bagian A (Kontrak)** bersifat tetap. Perubahan pada Bagian A memerlukan persetujuan ulang para penandatangan di A.10.
> - **Bagian B (Backlog)** bersifat hidup. Isi Bagian B boleh berubah tiap Sprint tanpa persetujuan ulang, selama tetap di dalam ruang lingkup Bagian A.

---

# BAGIAN A — KONTRAK RUANG LINGKUP (Lapisan Tetap untuk Persetujuan)

## A.1 Deskripsi Produk

Lukla Operations Engine adalah platform manajemen operasional pabrik konveksi berbasis event-driven. Platform ini menghubungkan seluruh alur kerja — **Sampel → Order → Gudang → Cutting → Jahit → QC → Payroll** — di atas buku besar *double-entry ledger* yang immutable (tidak bisa diubah). Sistem memisahkan kepemilikan material lewat aturan program, mencatat hasil kerja lantai produksi tiap 30 menit, dan menghitung biaya komersial serta gaji secara otomatis tanpa spreadsheet manual. *(Sumber: BRD §1.)*

## A.2 Masalah yang Diselesaikan

Hari ini, lantai produksi dan gudang Lukla punya tiga titik rawan *(Sumber: BRD §1)*:

1. **Kontaminasi silang bahan antarklien** — Bahan baku Klien A bisa terpakai untuk pesanan Klien B karena sistem tidak punya pembatas. Akibatnya stok kurang, kontrak jadi sengketa, dan kerugiannya sulit dipulihkan.
2. **Payroll borongan berantakan saat jumlah operator naik-turun (1 sampai 70+)** — Pabrik menggaji dengan upah borongan (*piece-rate*), bukan gaji bulanan tetap. Rekonsiliasi manual tiap Sabtu memakan lebih dari 8 jam dan gampang salah hitung: uang makan (10%–15%) berubah-ubah, pembagian bonus QC 3 arah lambat, dan overhead bulanan tidak bisa dibebankan adil ke tiap potong pakaian.
3. **Jejak revisi prototipe hilang (*R&D spec drift*)** — Sampel belum tercatat digital, jadi hasil time study, spesifikasi kain, dan rate card komponen tersebar di catatan kertas. Saat order masuk produksi massal, biaya dan target jahit meleset dari rencana.

## A.3 Mengapa Ini Penting Sekarang

Empat pendorong bisnis dari BRD §4:

* **BD-1 — Proteksi aset kustodial & kepatuhan kontrak maklon:** menghilangkan risiko tuntutan hukum dan ganti rugi karena kain titipan klien terpakai pihak lain, dan mengembalikan kepercayaan merek besar untuk menaruh volume maklon bernilai tinggi di Lukla.
* **BD-2 — Efisiensi administratif & akurasi penggajian mingguan:** mengeliminasi rekap manual akhir pekan yang memakan 8–10 jam kerja tim keuangan, dan menghilangkan sengketa hitungan borongan dengan operator.
* **BD-3 — Optimalisasi throughput & visibilitas lantai pabrik:** mengubah pemantauan pasif berbasis catatan harian menjadi pemantauan aktif per interval 30 menit; bottleneck komponen terlihat dalam hitungan jam.
* **BD-4 — Standarisasi biaya pokok produksi (COGS):** kalkulasi biaya riil per unit (bahan riil + ongkos jahit terverifikasi + overhead bulanan riil) mencegah *underpricing* pada penawaran maklon baru.

## A.4 Kriteria Keberhasilan

| # | Metrik Keberhasilan | Baseline | Target |
| :---- | :---- | :---- | :---- |
| 1 | Waktu rekap payroll borongan mingguan (tiap Sabtu) | Lebih dari 8 jam manual | Kurang dari 15 menit |
| 2 | Insiden kontaminasi silang bahan antarklien | Berulang, kerugian sulit dipulihkan | 0 insiden lolos |
| 3 | Siklus konversi kas (penerbitan faktur setelah produksi) | Sekitar 35 hari | Kurang dari 14 hari |

Angka-angka di atas adalah metrik bisnis, bukan tanggal. *(Sumber: BRD §1, §9.2.)*

## A.5 Audiens & Pengguna

Sistem melayani **8 peran pengguna**: Owner/Eksekutif, Tim Sample/Adis, Gudang/Warehouse, Kepala Produksi/Mandor, Penjahit/Tailor, QC Inspector, Finance & Payroll, dan Klien Maklon B2B (portal eksternal). Matriks izin dan pembatasan lengkap tiap peran ada di **Lampiran L.1** (pointer ke matriks RBAC kanonik).

## A.6 Ruang Lingkup Tingkat Tinggi

Dalam ruang lingkup *(ringkasan dari BRD §3.1)*: manajemen multi-tenant & identitas kepemilikan material, validasi anti-kontaminasi silang, siklus sampel & time study R&D, pelacakan output lantai per 30 menit, alokasi kapasitas dinamis (1–70+ penjahit), inspeksi QC & taksonomi cacat, mesin penggajian borongan mingguan (upah borongan, pool uang makan, bonus QC 3 arah, overhead per unit), portal eksternal klien B2B, dan matriks RBAC 8 peran.

Rincian lengkap ruang lingkup ada di **BRD §3.1**; daftar di-luar-ruang-lingkup ada di **BRD §3.2** dan dirangkum di **B.6** dokumen ini.

## A.7 Asumsi

Asumsi-asumsi berikut diambil dari BRD §13.1 dan dianggap benar sampai dibantah:

| # | Asumsi | Keterangan Sumber |
| :---- | :---- | :---- |
| AS-1 | Skala kapasitas pabrik adalah sekitar 70 mesin jahit. | BRD §13.1 |
| AS-2 | Mandor memiliki disiplin melakukan input verifikasi setiap 30 menit. | BRD §13.1 |
| AS-3 | Persentase uang makan (10%–15%) ditentukan manual oleh Finance. | BRD §13.1 |
| AS-4 | Bonus QC dibagi rata untuk 3 pimpinan lapangan (2 Mandor Lini, 1 Kepala Ops). | BRD §13.1; konfigurabilitas penerima **belum ditentukan di sumber** (lihat A.9). |

## A.8 Ketergantungan & Batasan Sistemik

Batasan tetap yang tidak bisa dinegosiasi *(Sumber: BRD §13.2, §8)*:

* **Immutable ledger:** catatan transaksi buku besar yang sudah dikunci bersifat absolut, tidak dapat diubah oleh siapa pun. Pembatalan hanya lewat **transaksi pembalik**, tanpa operasi UPDATE/DELETE pada tabel buku besar (NFR-02).
* **Guardrail anti-kontaminasi silang:** penerbitan surat perintah potong wajib merujuk lot bahan yang terverifikasi di gudang; perilaku sumber yang berlaku adalah **penolakan** transaksi bahan milik Klien A untuk pesanan Klien B.
* **RBAC 8 peran:** penegakan hak akses dan pembatasan operasional pada 8 peran pengguna (FR-2.1; matriks di L.1).
* **Rantai ketergantungan modul:** urutan pembangunan mengikuti MOD-01 → MOD-05 (BRD §12.1) — Core Ledger & RBAC → Multi-Tenant Warehouse & Guardrail → Sample R&D & Rate Card → Shop Floor MES & QC → Payroll & COGS Costing.

## A.9 Pertanyaan Terbuka (Open Questions)

Delapan item pertama di bawah ini adalah daftar lengkap item UNRESOLVED dari BRD §13.3; item ke-9 adalah konflik antar-dokumen. **Tidak ada pertanyaan di bawah ini yang diputuskan di dokumen ini** — semuanya menunggu keputusan pemilik keputusan yang berwenang.

| No | Pertanyaan Terbuka | Kedudukan di Sumber | Status |
| :---- | :---- | :---- | :---- |
| OQ-1 | Batas tiga pilar asli FR-2.1 (RBAC) tidak dapat diverifikasi karena slide sumber (slide 02c) tidak tersedia; matriks 8 peran saat ini bersumber dari slide 04. | BRD §13.3 item 1 | UNRESOLVED |
| OQ-2 | Slide 07 asli di disk tidak tersedia; isi kebutuhan payroll bersumber dari transkrip chat yang disimpan sebagai referensi. | BRD §13.3 item 2 | UNRESOLVED |
| OQ-3 | Detail FR-5 (Gudang): transaksi persediaan, aturan penyesuaian stok, dan prosedur stok opname belum ditentukan. | BRD §13.3 item 3 | UNRESOLVED |
| OQ-4 | Detail FR-6 (Cutting): batch, marker, limbah kain, dan pencatatan hasil potong belum ditentukan (FR-7.3 hanya mencatat hasil jahit). | BRD §13.3 item 4 | UNRESOLVED |
| OQ-5 | FR-1.4 memiliki penanda di sumber tetapi tidak memiliki teks definisi. | BRD §13.3 item 5 | UNRESOLVED |
| OQ-6 | Apakah pembagian bonus tetap (2 Mandor + 1 Kepala Operasional) dapat dikonfigurasi? | BRD §13.3 item 6 | UNRESOLVED |
| OQ-7 | Apa basis definisi perhitungan persentase uang makan 10%–15%? | BRD §13.3 item 7 | UNRESOLVED |
| OQ-8 | Catatan paritas register: tidak ada lagi bagian sumber yang tidak terbaca; dicatat untuk kelengkapan rekam jejak, bukan sebagai kebutuhan. | BRD §13.3 item 8 | UNRESOLVED (catatan paritas) |
| OQ-9 | **Konflik antar-dokumen — pembulatan sisa bonus QC.** Posisi A (PRD v1.3, "Catatan Penting untuk Eksekusi"): sisa pembulatan — walau Rp 1 — masuk ke **cadangan pabrik**, bukan mematahkan aplikasi. Posisi B (BRD §13.2 & §16.1): penanganan pembulatan dan sisa bonus QC **belum ditentukan** dan sisa **tidak boleh dialokasikan ke rekening tertentu**. Kedua posisi dikutip apa adanya; keputusan ditunda kepada pemilik keputusan. | PRD v1.3 vs BRD §13.2/§16.1 | UNRESOLVED — konflik antar-dokumen |

## A.10 Lembar Persetujuan

Perubahan apa pun pada Bagian A (termasuk tabel ini) memerlukan persetujuan ulang. Kolom Tanggal diisi saat penandatanganan.

| Peran / Jabatan | Nama Pejabat | Entitas | Status | Tanggal |
| :---- | :---- | :---- | :---- | :---- |
| Executive Sponsor / Owner | [NAMA — WAJIB DIISI] | Lukla Mfg | Pending Review | - |
| Head of Operations / Plant Manager | [NAMA — WAJIB DIISI] | Lukla Mfg | Pending Review | - |
| Finance & Commercial Lead | [NAMA — WAJIB DIISI] | Lukla Mfg | Pending Review | - |
| Lead Solution Architect | [NAMA — WAJIB DIISI] | Consulting Team | Pending Review | - |
| Lead Software Engineer | [NAMA — WAJIB DIISI] | Engineering Team | Pending Review | - |

---

# BAGIAN B — BACKLOG AGILE (Lapisan Hidup untuk Tim Scrum)

## B.0 Cara Kerja Backlog Ini

* Bagian ini adalah dokumen hidup: **boleh berubah tiap Sprint tanpa persetujuan ulang**, selama tetap di dalam ruang lingkup Bagian A. Perubahan yang keluar dari ruang lingkup harus naik ke Bagian A.
* Kadensi Scrum mengikuti BRD §12.4: **Sprint Planning** setiap Senin pagi (2 jam) untuk menyetujui Sprint Backlog; **Daily Standup** 15 menit setiap pukul 08.30 WIB (Google Meet/on-site Ciwidey) untuk mengidentifikasi hambatan; **Sprint Review & Demo** setiap Jumat sore (1 jam) untuk mendemonstrasikan increment kepada Stakeholder Lukla; dan **Sprint Retrospective** (evaluasi internal tim teknis setelah Sprint Review untuk perbaikan proses berkelanjutan).
* **Reprioritisasi diperbolehkan** pada Sprint Planning — urutan item di B.1 dan isi Sprint di B.2 boleh ditata ulang, selama rantai ketergantungan MOD-01 → MOD-05 (A.8) tetap dihormati.
* **Definition of Done:** item dinyatakan selesai hanya setelah lulus skenario penerimaan yang relevan di **B.4** (mengacu pada kriteria penerimaan BRD §16.6).
* Item yang definisinya belum selesai di sumber ditaruh di subbagian "Menunggu klarifikasi" dan **tidak** dimasukkan ke Sprint mana pun.

## B.1 Product Backlog

Prioritas mengikuti skala BRD §7: **1 (Kritis)** = wajib ada pada peluncuran perdana; **2 (Tinggi)** = sangat penting, sistem masih bisa berjalan terbatas tanpanya. Inventaris FR adalah gabungan matriks BRD §7 dan inventaris BRD §16.5 — total 26 ID.

| ID | Kategori | Deskripsi Singkat | Prioritas | Sumber BRD |
| :---- | :---- | :---- | :---- | :---- |
| FR-1.1 | RC1 — Multi-Tenant & Akses | Isolasi seluruh data operasional & inventaris per klien B2B (multi-tenant) | 1 (Kritis) | BRD §7 RC1; §16.5 |
| FR-2.1 | RC1 — Multi-Tenant & Akses | Kontrol akses berbasis peran (RBAC) pada 8 peran pengguna | 1 (Kritis) | BRD §7 RC1; §16.5 |
| FR-3.1 | RC1 — Multi-Tenant & Akses | Audit trail append-only untuk seluruh riwayat revisi & transaksi | 1 (Kritis) | BRD §7 RC1; §16.5 |
| FR-4.1 | RC2 — Sampel & R&D | Riwayat versi sampel prototipe (v1, v2, dst.) beserta parameter jahitan & spesifikasi kain | 2 (Tinggi) | BRD §7 RC2; §16.5 |
| FR-4.2 | RC2 — Sampel & R&D | Instrumen pencatatan time study per komponen garmen | 2 (Tinggi) | BRD §7 RC2; §16.5 |
| FR-4.3 | RC2 — Sampel & R&D | Master Spec Sheet terkunci saat sampel disetujui klien | 1 (Kritis) | BRD §7 RC2; §16.5 |
| FR-5.1 | RC3 — Gudang & Cutting | Wajib input identitas pemilik (client_id) dan alokasi pesanan (order_id) saat penerimaan bahan baku | 1 (Kritis) | BRD §7 RC3; §16.5 |
| FR-5.2 | RC3 — Gudang & Cutting | Pencatatan penerimaan bahan titipan tanpa membebankannya sebagai hutang dagang perusahaan | 1 (Kritis) | BRD §7 RC3; §16.5 |
| FR-6.1 | RC3 — Gudang & Cutting | Pencatatan stok opname secara real-time | 2 (Tinggi) | BRD §7 RC3; §16.5 |
| FR-6.2 | RC3 — Gudang & Cutting | Guardrail anti-kontaminasi silang: tolak penerbitan bahan milik Klien A untuk pesanan Klien B | 1 (Kritis) | BRD §7 RC3; §16.5 |
| FR-6.3 | RC3 — Gudang & Cutting | Catat hasil pemotongan kain massal, rasio limbah, dan efisiensi konsumsi | 2 (Tinggi) | BRD §7 RC3; §16.5 |
| FR-7.1 | RC4 — MES Lantai Produksi | Tata letak lini produksi dinamis & alokasi fleksibel operator penjahit (1–70+) | 1 (Kritis) | BRD §7 RC4; §16.5 |
| FR-7.2 | RC4 — MES Lantai Produksi | Rate card ongkos jahit per komponen artikel berdasarkan hasil time study | 1 (Kritis) | BRD §7 RC4; §16.5 |
| FR-7.3 | RC4 — MES Lantai Produksi | Terminal sentuh bagi mandor untuk input jumlah hasil jahit per blok interval 30 menit | 1 (Kritis) | BRD §7 RC4; §16.5 |
| FR-7.4 | RC4 — MES Lantai Produksi | Unit komponen hasil jahit otomatis berstatus Menunggu QC; upah operator bersifat bersyarat | 1 (Kritis) | BRD §7 RC4; §16.5 |
| FR-8.1 | RC5 — QC & Cacat | Terminal QC untuk mengklasifikasikan unit menjadi Pass, Repair, atau Reject | 1 (Kritis) | BRD §7 RC5; §16.5 |
| FR-8.2 | RC5 — QC & Cacat | Unit Repair kembali ke penjahit yang sama tanpa kredit upah borongan ganda | 2 (Tinggi) | BRD §7 RC5; §16.5 |
| FR-9.1 | RC5 — QC & Cacat | Setiap unit Pass QC menambah bonus pool | 1 (Kritis) | BRD §7 RC5; §16.5 |
| FR-9.2 | RC5 — QC & Cacat | Bonus pool dibagi 3 arah kepada Mandor 1, Mandor 2, dan Kepala Operasional, dibayarkan bersama payroll mingguan | 1 (Kritis) | BRD §7 RC5; §16.5 |
| FR-10.1 | RC6 — Payroll & Costing | Kalkulasi upah borongan mingguan penjahit secara otomatis setiap hari Sabtu | 1 (Kritis) | BRD §7 RC6; §16.5 |
| FR-10.2 | RC6 — Payroll & Costing | Akumulasi pool uang makan mengambang mingguan (10%–15%) | 1 (Kritis) | BRD §7 RC6; §16.5 |
| FR-10.3 | RC6 — Payroll & Costing | Pengumpulan dana bonus QC dan pembagian sama rata menjadi 3 bagian | 1 (Kritis) | BRD §7 RC6; §16.5 |
| FR-10.4 | RC6 — Payroll & Costing | Rekapitulasi total overhead bulanan dan alokasi beban overhead per unit garmen jadi | 2 (Tinggi) | BRD §7 RC6; §16.5 |

> **Catatan silang (wajib):** FR-9.2 dan FR-10.3 adalah **SATU aturan bonus bagi-tiga yang sama** dengan dua ID sumber berbeda. Jangan dijadikan dua aturan independen dan jangan dijadikan dua skenario penerimaan terpisah. *(BRD §7 dan §16.5, cross-note.)*

### Menunggu klarifikasi

Tiga ID berikut ada di inventaris sumber tetapi definisinya belum selesai (lihat A.9, OQ-3/OQ-4/OQ-5). Mereka **belum dimasukkan ke Sprint mana pun** sampai diperjelas.

| ID | Deskripsi Singkat | Prioritas | Sumber BRD |
| :---- | :---- | :---- | :---- |
| FR-1.4 | Elemen onboarding klien/pesanan — teks definisi tidak tersedia di sumber | Belum ditentukan di sumber | BRD §16.5; §13.3 |
| FR-5 | **Pengelompokan fase "Gudang"** — stok multi-klien, penerimaan titipan; anak: FR-5.1, FR-5.2 | Belum ditentukan di sumber | BRD §16.5; §13.3 |
| FR-6 | **Pengelompokan fase "Cutting"** — anak: FR-6.1, FR-6.2, FR-6.3 | Belum ditentukan di sumber | BRD §16.5; §13.3 |

> FR-5 dan FR-6 adalah pengelompokan tingkat fase, bukan fitur tunggal; prioritas riil dibawa oleh ID anaknya (FR-5.1/5.2 dan FR-6.1/6.2/6.3), yang sudah masuk tabel utama di atas.

## B.2 Rencana Sprint

Empat Sprint, **tanpa tanggal** — urutan mengikuti rantai ketergantungan modul BRD §12.1 (MOD-01 → MOD-05). Panjang tiap Sprint disepakati di Sprint Planning.

### Sprint 1 — Core Ledger & RBAC (MOD-01)

* **FR:** FR-1.1, FR-2.1, FR-3.1.
* **Wajib ada di Sprint ini:** skema buku besar *immutable double-entry ledger* yang nyata (append-only; pembatalan hanya lewat transaksi pembalik) **dan** minimal satu permukaan UI yang memperlihatkan entri jurnal ledger — inti dari kebutuhan **"UI IMMUTABLE DOUBLE-ENTRY CORE"**.
* **Kenapa duluan:** buku besar immutable dan RBAC mendasari seluruh transaksi modul berikutnya (BRD §12.1).

### Sprint 2 — Multi-Tenant Warehouse & Guardrail (MOD-02)

* **FR:** FR-5.1, FR-5.2, FR-6.1, FR-6.2, FR-6.3.
* **Isi:** penerimaan bahan dengan tag client_id/order_id, perlakuan akuntansi kustodial, database trigger pemblokir kontaminasi silang, stok opname real-time, dan pencatatan hasil cutting.
* **Prasyarat:** MOD-01 aktif — stok kustodial dan anti-kontaminasi harus aktif sebelum transaksi bahan.

### Sprint 3 — Sample Lifecycle, Rate Card, MES Floor, QC (MOD-03 + MOD-04)

* **FR:** FR-4.1, FR-4.2, FR-4.3, FR-7.1, FR-7.2, FR-7.3, FR-7.4, FR-8.1, FR-8.2.
* **Isi:** siklus versi sampel, time study, penguncian Master Spec & rate card, penataan lini jahit, terminal sentuh 30 menit, dan terminal QC.
* **Prasyarat:** MOD-01 dan MOD-02 — pencatatan jahit dan QC membutuhkan rate card dan data order.

### Sprint 4 — Payroll, Costing, Portal & End-to-End (MOD-05)

* **FR:** FR-9.1, FR-9.2, FR-10.1, FR-10.2, FR-10.3, FR-10.4.
* **Isi tambahan:** portal mandiri klien B2B, integrasi end-to-end keenam antarmuka UI, **UAT** (menggunakan skenario B.4), dan **buffer waktu uji** — jendela khusus pengujian dan pencegahan untuk menutup temuan jika ada yang meleset sebelum penyerahan.
* **Prasyarat:** MOD-04 — payroll dan COGS membutuhkan data unit Pass dari Terminal QC.

## B.3 User Stories

Empat cerita pengguna inti (diwarisi dan dirapikan dari PRD v1.3 §2.1):

1. **Sebagai Warehouse Manager**, saya ingin sistem memblokir pengeluaran kain jika ID Klien bahan tidak cocok dengan ID pesanan, agar saya terhindar dari kerugian akibat salah potong material.
2. **Sebagai Mandor Lini (Foreperson)**, saya ingin layar sentuh untuk memasukkan jumlah jahitan (tally) masing-masing penjahit setiap 30 menit, agar saya tidak perlu mencatat manual di kertas yang mudah hilang.
3. **Sebagai Tim Finance**, saya ingin sistem otomatis menghitung upah borongan, uang makan (10%–15%), dan pembagian bonus QC setiap hari Sabtu, agar saya tidak perlu menghabiskan 8 jam lembur merangkai rumus Excel.
4. **Sebagai Klien Maklon B2B**, saya ingin memiliki portal untuk melihat status pesanan dan saldo kain titipan secara mandiri, agar saya memiliki visibilitas dan merasa aman mempercayakan produksi ke Lukla.

## B.4 Skenario Penerimaan (UAT)

Empat skenario pengujian penerimaan bisnis dari BRD §16.4 (kriteria penerimaan penuh Given-When-Then ada di BRD §16.6):

1. **Pencegahan Kontaminasi Silang** — Sistem menggagalkan transaksi jika bahan Klien A akan dipotong untuk pesanan Klien B. *(Uji untuk FR-6.2; pemilik modul Gudang/Cutting masih UNRESOLVED — lihat A.9 OQ-4.)*
2. **Penambahan Tenaga Dinamis** — Mandor mendaftarkan penjahit baru di hari Kamis; sistem tetap dapat merekap gaji mereka pada hari Sabtu beserta persentase uang makan, tanpa me-restart siklus.
3. **Pembagian Bonus Rata** — 3.000 unit lolos QC dikali tarif bonus, kemudian dana dibagi menjadi 3 bagian untuk 3 pimpinan lapangan. *(Uji tunggal untuk aturan bagi-tiga bersama FR-9.2/FR-10.3; penanganan pembulatan/sisa UNRESOLVED — lihat A.9 OQ-9.)*
4. **Transisi Revisi Sampel** — Sistem mengubah sampel disetujui (v2) menjadi pesanan massal dengan mewarisi secara otomatis spesifikasi dan rate card sebelumnya.

## B.5 Antarmuka (6 UI Views)

Enam antarmuka minimum (spesifikasi lengkap di **BRD §16.3**):

1. **VIEW 01 — Executive Operations Dashboard:** grafik output 30 menit dan matriks progres order.
2. **VIEW 02 — Sample & Time Study Tracker:** instrumen stopwatch untuk merekam waktu penjahitan komponen.
3. **VIEW 03 — Multi-Client Warehouse Inventory Grid:** tabel stok dengan peringatan pop-up jika terjadi tabrakan pemilik bahan.
4. **VIEW 04 — Floor Terminal:** tombol besar sentuh untuk input hasil jahit tiap penjahit pada blok interval 30 menit.
5. **VIEW 05 — QC Inspection Terminal:** pemindaian nomor serial dengan tombol Pass, Repair, atau Reject.
6. **VIEW 06 — Payroll & Costing Workspace:** rekap total borongan murni, alokasi uang makan, dan penentuan overhead akhir minggu.

> Permukaan UI jurnal ledger yang diwajibkan di Sprint 1 (B.2) berada di dalam suite keenam antarmuka ini.

## B.6 Di Luar Ruang Lingkup

Daftar lengkap di **BRD §3.2**. Ringkasnya, **tidak** termasuk:

1. **Kompensasi ketenagakerjaan statuter** — BPJS Ketenagakerjaan/Kesehatan, PPh 21, uang lembur formal, pesangon formal.
2. **Akuntansi finansial lengkap** — pelaporan pajak korporasi, depresiasi aset, rekonsiliasi multi-rekening eksternal.
3. **Logistik pengiriman & armada** — pelacakan truk ekspedisi pihak ketiga atau integrasi API kurir.
4. **Pengadaan bahan baku terotomatisasi (MRP)** — keputusan pembelian otomatis dari supplier (hanya PO internal yang dicatat).
5. **Aplikasi seluler native** — sistem dibangun sebagai Web Responsive PWA untuk desktop dan tablet sentuh industri.

---

# LAMPIRAN

## L.1 RBAC 8 Peran

Kedelapan peran sistem: **Owner/Eksekutif (Internal), Tim Sample/Adis (Sample), Gudang/Warehouse (Stok), Kepala Produksi/Mandor (Line), Penjahit/Tailor (Operator), QC Inspector (Quality), Finance & Payroll (Finance), Klien Maklon/Ext (B2B Portal).**

Matriks izin (IZIN), pembatasan (PEMBATASAN), dan celah yang belum diputuskan (UNSPECIFIED) **tidak diduplikasi di sini**. Sumber kanonik: `openspec/changes/lukla-ops-engine-planning/artifacts/04-rbac-matrix.md` (dirujuk oleh BRD §11.1).

## L.2 Rumus Payroll & Costing

Empat rumus inti (rumus matematis lengkap **tidak diduplikasi di sini** — lihat **BRD §16.1**):

1. **Upah Borongan Mingguan Penjahit** — dihitung setiap Sabtu: unit terverifikasi × tarif upah komponen.
2. **Pool Uang Makan Mengambang** — persentase uang makan (10%–15%) × total upah seluruh penjahit.
3. **Pembagian Bonus Kontrol Kualitas (bagi 3)** — total pakaian lolos QC × tarif bonus per pakaian, dibagi 3; penanganan pembulatan/sisa UNRESOLVED (lihat A.9 OQ-9).
4. **Alokasi Biaya Overhead Pabrik per Unit Pakaian** — total biaya operasional bulanan ÷ total unit pakaian jadi bulan tersebut.

## L.3 Glosarium

Glosarium lengkap ada di **BRD §14**. Istilah kunci:

* **Maklon** — kerja sama klien menyerahkan produksi pakaian kepada Lukla.
* **CMT (Cut, Make, Trim)** — klien menyediakan 100% bahan baku; Lukla menyediakan jasa jahit dan finishing.
* **Borongan** — kompensasi kerja berdasarkan jumlah unit fisik yang diselesaikan (*piece-rate*).
* **Kontaminasi Silang** — kesalahan bahan titipan Klien A terpakai untuk Klien B.
* **Uang Makan** — tunjangan mingguan 10%–15% dari total ongkos jahit.
