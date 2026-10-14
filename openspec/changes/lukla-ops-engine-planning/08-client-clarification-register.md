# 08 — Master Client Clarification & Uncertainty Register
**Change:** `lukla-ops-engine-planning`  
**Date:** 2026-10-13  
**Status:** DRAFT FOR CLIENT ALIGNMENT  
**Purpose:** Konsolidasi menyeluruh atas seluruh pertanyaan bisnis, komersial, operasional, hukum, dan tata kelola yang **TIDAK ADA / TIDAK DISEBUTKAN di dalam slide pitch deck (Slides 00–09)** dan wajib diklarifikasi kepada klien / pemilik bisnis sebelum implementasi teknis dikunci.

---

## Ringkasan Eksekutif & Struktur Triage Pertanyaan

Berdasarkan tinjauan adversarial 360° yang melibatkan perspektif Eksekutif Pabrik, Kepala Operasional & Mandor, Finance & Commercial Lead, serta Klien Maklon B2B eksternal, seluruh ketidakpastian dikelompokkan ke dalam 6 domain utama:

```
+---------------------------------------------------------------------------------------------------+
|                        REGISTER KLARIFIKASI KLIEN (CLIENT CLARIFICATION DOMAINS)                  |
+---------------------------------------------------------------------------------------------------+
| 1. Tata Kelola Komersial & Skema Maklon (CMT, Semi-CMT, Full Package)                             |
| 2. Akuntansi Finansial, Perpajakan & Alokasi Overhead                                             |
| 3. Rekayasa Payroll Mingguan, Uang Makan & Bonus QC                                               |
| 4. Operasional Lantai Jahit Ciwidey & Ergonomi Mandor                                             |
| 5. Pengendalian Kualitas (QC), Retur & Perlindungan Merek                                         |
| 6. Kesenjangan Sumber Pitch Deck (Provenance & Slide Missing)                                     |
+---------------------------------------------------------------------------------------------------+
```

---

## DOMAIN 1: TATA KELOLA KOMERSIAL & SKEMA MAKLON

### 1.1 Persentase Toleransi Susut & Limbah Kain CMT (Shrinkage & Scrap Allowance)
* **Konteks:** Pada skema CMT, kain 100% milik klien. Di lapangan tekstil, kain mengalami penyusutan alami (2%–5%), cacat tenun/rajut dari pabrik kain, dan sisa potong (marker waste 12%–18%).
* **Pertanyaan untuk Klien:**
  1. Berapa batas toleransi susut dan limbah potong (*allowable scrap tolerance*) yang disepakati secara kontraktual (misal: maksimal 3% atau 5%)?
  2. Jika limbah kain melebihi batas toleransi akibat kesalahan pola/operator potong, bagaimana mekanisme kompensasi kepada klien (apakah potong tagihan jasa jahit atau ganti rugi fisik)?
  3. Siapa yang menanggung risiko jika kain yang dikirim klien ternyata cacat bawaan dari pabrik tekstil (*fabric defect from mill*) setelah terlanjur dipotong?

### 1.2 Kepemilikan & Pengelolaan Sisa Kain / Perca (Remnants & Scrap Ownership)
* **Konteks:** Setiap pemotongan pakaian menyisakan potongan kecil (*perca kain*) dan sisa gulungan utuh (*end-of-roll* $\ge 1\text{ meter}$).
* **Pertanyaan untuk Klien:**
  1. Untuk sisa gulungan kain utuh ($\ge 1\text{ meter}$), apakah wajib dikembalikan bersama pengiriman barang jadi, atau disimpan di gudang Lukla sebagai saldo titipan untuk pesanan berikutnya?
  2. Untuk limbah perca potongan kain kecil, apakah Lukla berhak membuang/menjual kiloan sebagai perca peredam/lap untuk menutup biaya operasional, atau wajib diserahkan kembali ke klien?
  3. Bagaimana prosedur pemusnahan perca berlogo/bercorak khusus untuk mencegah pembajakan merek di pasar gelap Ciwidey/Bandung?

### 1.3 Alur Pengadaan & Penagihan Skema Semi-CMT
* **Konteks:** Pada Semi-CMT, klien menyediakan kain luar, sementara Lukla mengadakan bahan pembantu (furing, benang, kancing, resleting).
* **Pertanyaan untuk Klien:**
  1. Bagaimana mekanisme penagihan bahan pembantu tersebut ke klien: apakah menggunakan sistem paket harga satuan tetap (*Fixed Package Fee per Garment*), metode *Cost-Plus* (Harga Beli Supplier + Markup %), atau *Reimbursement at Cost* murni dengan melampirkan nota supplier?
  2. Kapan pembayaran bahan pembantu jatuh tempo: apakah ditalangi Lukla di awal lalu ditagih di akhir, atau klien wajib membayar deposit bahan di muka?

### 1.4 Kebijakan Uang Muka (Down Payment) & Termin Kredit Maklon
* **Konteks:** Biaya tenaga kerja borongan wajib cair tunai/transfer setiap Sabtu sore, sementara penagihan klien B2B umumnya memiliki tempo pembayaran.
* **Pertanyaan untuk Klien:**
  1. Apakah sistem wajib mengunci proses pemotongan kain (*Cutting Gate*) sampai klien membayar Uang Muka (DP, misal 30%–50%)?
  2. Apa syarat pembayaran (*payment terms*) untuk pelunasan: apakah *Cash Before Delivery* (CBD sebelum barang keluar gerbang pabrik) atau kredit tempo (Net 14 / Net 30 hari pasca Surat Jalan diterima)?

---

## DOMAIN 2: AKUNTANSI FINANSIAL, PERPAJAKAN & OVERHEAD

### 2.1 Kebijakan Alokasi Biaya Overhead Bulanan Pabrik (FR-10.4)
* **Konteks:** Formula saat ini membagi total biaya bulanan fasilitas (listrik, air, internet, gedung) dengan total unit pakaian jadi bulan tersebut. Jika produksi anjlok dari 5.000 ke 500 unit, overhead per unit melonjak 10x lipat.
* **Pertanyaan untuk Klien:**
  1. Apakah biaya overhead ini hanya untuk analisis manajerial internal, ataukah memengaruhi harga tagihan ke klien maklon secara retrospektif? (Standar komersial: penawaran harga CMT ke klien wajib mengikat di awal).
  2. Apakah alokasi overhead menggunakan pembagian unit mentah, atau diboboti berdasarkan durasi penjahitan (*Standard Allowed Minutes* / SAM)? Contoh: Jaket Parka 45 menit menyerap overhead yang sama atau lebih besar dibanding Tote Bag 3 menit?
  3. Apakah Lukla setuju menggunakan *Tarif Overhead Standar Ditentukan di Muka (Predetermined Normal Rate)* agar biaya per unit stabil, dan selisih kapasitas menganggur (*idle capacity*) diakui langsung di laporan laba rugi bulanan?

### 2.2 Penilaian Moneter Persediaan Titipan CMT (Custodial Valuation Trap)
* **Konteks:** Klien maklon B2B hampir tidak pernah membuka harga beli asli kain mereka kepada konveksi demi menjaga rahasia dagang.
* **Pertanyaan untuk Klien:**
  1. Apakah klien maklon bersedia mencantumkan nilai rupiah per meter pada Surat Jalan pengiriman bahan ke Lukla?
  2. Jika klien menolak membuka harga kain, apakah klien setuju persediaan titipan CMT dicatat dalam **Buku Pembantu Kuantitas Fisik (Subledger Meter/Yard, non-moneter)** tanpa dimasukkan ke jurnal nilai rupiah buku besar umum agar tidak mendistorsi neraca Lukla?

### 2.3 Status Pajak (PPN 11% & PPh Pasal 23)
* **Konteks:** Jasa maklon garmen merupakan objek PPh Pasal 23 (tarif 2%) dan PPN jika entitas berstatus PKP.
* **Pertanyaan untuk Klien:**
  1. Apakah entitas Lukla Manufacturing berstatus Pengusaha Kena Pajak (PKP) yang wajib menerbitkan Faktur Pajak PPN 11% pada setiap invoice komersial?
  2. Apakah modul penagihan harus memotong otomatis PPh Pasal 23 (2%) dan mencatat penagihan Bukti Potong Pajak (Bupot) dari klien?

---

## DOMAIN 3: REKAYASA PAYROLL MINGGUAN, UANG MAKAN & BONUS QC

### 3.1 Dasar Pembagian Pool Uang Makan 10%–15% ke Individu Penjahit (FR-10.2)
* **Konteks:** Slide 07 hanya mendefinisikan total dana pool uang makan ($\text{Pool} = \mu \times \sum \text{Wage}$), namun TIDAK mendefinisikan bagaimana uang tersebut dibagikan ke masing-masing penjahit pada hari Sabtu.
* **Pertanyaan untuk Klien:**
  1. **Opsi A (Proporsional terhadap hasil borongan):** Penjahit yang upah borongannya besar mendapat uang makan lebih besar ($\text{Uang Makan}_i = \mu \times \text{Upah}_i$). *(Kritik: Kebutuhan makan harian operator tidak bergantung pada kecepatan jahit).*
  2. **Opsi B (Dibagi rata per kepala aktif):** Total pool dibagi rata kepada seluruh penjahit yang terdaftar minggu tersebut. *(Kritik: Penjahit yang baru masuk hari Kamis menerima uang makan yang sama dengan yang masuk penuh sejak Senin).*
  3. **Opsi C (Berbasis Hari Kehadiran / Mandays):** Pool dibagi rata per hari kehadiran fisik. *(Membutuhkan pencatatan absensi harian sederhana di sistem).*
  4. Mana opsi yang disepakati untuk diterapkan?

### 3.2 Penanggung Beban Finansial Uang Makan
* **Konteks:** Nilai 10%–15% dari total upah jahit adalah beban tunai yang cukup besar.
* **Pertanyaan untuk Klien:**
  1. Siapakah yang menanggung dana uang makan ini: apakah menjadi Beban Operasional Internal Lukla yang memotong margin jasa maklon, ataukah disematkan sebagai komponen biaya tambahan (*surcharge*) pada kontrak klien maklon?

### 3.3 Tata Kelola & Mitigasi Moral Hazard Bonus QC 3-Arah (FR-9.2 / FR-10.3)
* **Konteks:** Bonus QC dibagikan rata untuk 2 Mandor + 1 Kepala Operasional dari setiap unit yang `PASS` QC, sedangkan QC Inspector yang memeriksa mendapat 0%. Hal ini menciptakan insentif buruk di mana mandor menekan QC Inspector untuk meloloskan barang cacat demi uang bonus.
* **Pertanyaan untuk Klien:**
  1. Apakah struktur penerima bonus QC tetap kaku dibagi 3 (2 Mandor + 1 Kepala Ops), ataukah dapat direstrukturisasi agar tim QC Inspector juga menerima bagian (misal: 25% tim QC, 75% pimpinan lini)?
  2. Apa yang terjadi jika jumlah mandor yang bertugas berubah (misal hanya 1 mandor di musim sepi, atau 3 mandor di musim ramai)? Apakah pembagian bonus menjadi dinamis mengikuti jumlah mandor aktif?
  3. Bagaimana penanganan sisa pembulatan rupiah (misal Rp 100.000 ÷ 3 = Rp 33.333,33 sisa Rp 1)? Apakah dialokasikan ke kas cadangan pabrik (*reserve fund*) atau ditambahkan ke Kepala Ops?
  4. Apakah ada klausul penalti pemotongan bonus (*clawback*) jika di kemudian hari pakaian yang diloloskan ternyata di-reject dan diklaim ganti rugi oleh klien B2B saat barang tiba di gudang mereka?

### 3.4 Batas Waktu Cut-Off & Logistik Pembayaran Sabtu Sore
* **Konteks:** Perhitungan payroll dijalankan otomatis setiap hari Sabtu.
* **Pertanyaan untuk Klien:**
  1. Pukul berapa batas waktu cut-off output jahit hari Sabtu diberlakukan (misal: Sabtu pukul 12:00 siang atau 15:00 sore)?
  2. Bagaimana nasib jahitan hari Sabtu yang belum sempat diinspeksi oleh QC pada jam cut-off: apakah langsung ditransfer ke siklus Sabtu minggu depan?
  3. Bagaimana metode pencairan upah kepada penjahit borongan di Ciwidey: apakah transfer bank langsung (apakah seluruh penjahit memiliki rekening), atau penarikan uang tunai fisik dalam amplop di meja kasir pabrik?
  4. Siapa pejabat yang memiliki hak persetujuan akhir (*approval gate*) untuk mengeksekusi pencairan payroll di sistem (Owner / Plant Manager)?

---

## DOMAIN 4: OPERASIONAL LANTAI JAHIT CIWIDEY & ERGONOMI MANDOR

### 4.1 Jam Istirahat, Sholat Jumat & Pencatatan Waktu Menganggur (Downtime)
* **Konteks:** Sistem mencatat output setiap 30 menit. Di pabrik nyata terdapat jeda istirahat resmi (12:00–13:00, sholat Jumat 11:30–13:00), mati lampu PLN, jarum patah, dan mesin rusak.
* **Pertanyaan untuk Klien:**
  1. Bagaimana perlakuan sistem terhadap blok istirahat resmi: apakah interval tersebut dinonaktifkan otomatis agar grafik dashboard efisiensi tidak anjlok menampilkan angka 0 palsu?
  2. Apakah terminal mandor perlu dilengkapi form pencatatan kendala pabrik (*downtime codes*: `PLN Padam`, `Jarum Patah`, `Tunggu Mekanik`, `Tunggu Pasokan Kain`)?
  3. Jika terjadi pemadaman listrik PLN selama 1–2 jam di Ciwidey, apakah penjahit borongan menerima uang tunggu dasar, atau murni tanpa upah?

### 4.2 Prosedur Resolusi Sengketa Borongan Harian
* **Konteks:** Penjahit dan mandor rawan berselisih hitungan jumlah potong (misal: mandor mencatat 15 potong, penjahit merasa menyelesaikan 20 potong). Begitu bundel kain berpindah ke meja lain, penghitungan ulang fisik sudah mustahil.
* **Pertanyaan untuk Klien:**
  1. Bagaimana mekanisme pencegahan sengketa borongan harian sebelum hari Sabtu: apakah penjahit menerima sobekan kupon fisik dari kartu bundel, atau sistem mencetak lembar rekap harian (*daily closing slip*) untuk diparaf bersama penjahit sebelum pulang jam 17:00?
  2. Berapa menit jendela waktu toleransi bagi mandor untuk mengoreksi kesalahan input angka di tablet secara mandiri sebelum transaksi terkunci permanen?

### 4.3 Kebijakan Penalti Pakaian Reject / Cacat Permanen
* **Konteks:** BRD §6.1 menyebutkan status "Reject (scrap/potong gaji)".
* **Pertanyaan untuk Klien:**
  1. Jika penjahit melakukan kesalahan fatal yang merusak kain hingga harus di-Reject/Scrap, apa sanksi resminya: apakah penjahit hanya kehilangan upah jahit untuk unit tersebut (upah Rp 0), ataukah ada pemotongan ganti rugi harga bahan kain dari total gajinya?
  2. Jika ada pemotongan ganti rugi kain, berapa batas maksimal pemotongan upah yang diperbolehkan agar tidak melanggar ketentuan ketenagakerjaan dan memicu pengunduran diri massal penjahit?

---

## DOMAIN 5: PENGENDALIAN KUALITAS (QC), RETUR & PERLINDUNGAN MEREK

### 5.1 Standar Penerimaan Kualitas (AQL) & Audit Klien Independen
* **Konteks:** Pesanan maklon B2B skala menengah umumnya mengacu pada standar Acceptable Quality Level (AQL) sebelum pengiriman.
* **Pertanyaan untuk Klien:**
  1. Standar AQL apa yang menjadi acuan serah terima barang (misal: AQL 2.5 Major, 4.0 Minor)?
  2. Apakah klien maklon diizinkan mengirimkan auditor QC eksternal pihak ketiga (misal: SGS, Intertek, atau tim internal klien) untuk melakukan inspeksi final acak (*Final Random Inspection*) di pabrik Lukla sebelum Surat Jalan pengiriman diterbitkan?
  3. Apakah diperlukan prosedur pemindaian jarum (*metal / needle detector inspection*) sebelum barang dikemas ke dalam karton master?

### 5.2 Alur Retur Barang Jadi dari Klien (Customer RMA & Post-Delivery Warranty)
* **Konteks:** BRD saat ini hanya menangani perbaikan (*Repair*) di lantai jahit sebelum barang keluar. Belum ada alur jika 2 minggu kemudian klien komplain menemukan 50 jaket jahitannya lepas saat tiba di toko retail mereka.
* **Pertanyaan untuk Klien:**
  1. Bagaimana alur perbaikan retur pakaian dari klien luar: siapa yang menanggung ongkos kirim dan biaya jahit ulang jika penjahit aslinya sudah tidak bekerja di pabrik?
  2. Bagaimana perlakuan pembukuan atas klaim biaya ganti rugi retur dari klien?

### 5.3 Perlindungan Hak Cipta Desain Klien vs. Brand Internal Snøhund (Chinese Wall)
* **Konteks:** Lukla memproduksi merek internalnya sendiri (*Snøhund*) di pabrik dan mesin yang sama dengan klien maklon.
* **Pertanyaan untuk Klien:**
  1. Kebijakan perlindungan kerahasiaan (*Non-Disclosure & IP Protection*) apa yang diwajibkan oleh klien B2B untuk menjamin bahwa pola digital (CAD), pola potong, tabel ukuran (*tech pack*), dan spesifikasi bahan mereka tidak disalin atau digunakan untuk koleksi ritel Snøhund?
  2. Apakah akses berkas pola dan desain klien luar di sistem harus diisolasi ketat sehingga hanya tim sampel tertentu yang bisa membuka, dan tertutup bagi staf marketing/produk Snøhund?

### 5.4 Otoritas Pengesahan Sampel Digital (Sample Sign-Off Workflow)
* **Konteks:** Transisi dari Sampel v1 $\rightarrow$ v2 menjadi Pesanan Massal (FR-4.1) membutuhkan konfirmasi agar tidak terjadi sengketa spesifikasi saat produksi massal.
* **Pertanyaan untuk Klien:**
  1. Siapa pejabat dari pihak klien yang berwenang memberikan pengesahan akhir (*Client Sign-Off*) atas Sampel v2: apakah wajib tanda tangan digital / persetujuan resmi di portal sistem, atau cukup surat persetujuan fisik/email yang diunggah ke sistem?
  2. Siapa pejabat internal Lukla yang berwenang mengubah status sampel menjadi Surat Perintah Kerja Massal (Owner atau Plant Manager)?

---

## DOMAIN 6: KESENJANGAN SUMBER PITCH DECK (PROVENANCE GAPS)

### 6.1 Status Fisik Slide 02c (Pilar Solusi & FR-2.1)
* **Konteks:** Slide 02c tidak memiliki foto pada disk repositori dan tidak ada lampiran chat. FR-2.1 (RBAC 8 Peran) saat ini berstatus `[assumption]`.
* **Permintaan ke Klien:** Mohon lampirkan salinan asli slide 02c untuk memastikan tidak ada pilar arsitektur atau hak akses lain yang terlewat.

### 6.2 Status Foto Fisik Asli Slide 07 (Mesin Payroll)
* **Konteks:** Slide 07 hanya tersedia dalam bentuk transkripsi teks lampiran chat, belum ada foto fisik beresolusi tinggi di repositori.
* **Permintaan ke Klien:** Mohon verifikasi apakah foto fisik asli Slide 07 dapat diarsipkan untuk menutup integritas ketertelusuran sumber secara 100%.

### 6.3 Definisi & Ruang Lingkup FR-1.4 (Onboarding Klien & Order)
* **Konteks:** Badge `FR-1.4` terlihat pada diagram Fase 1 Slide 03, namun teks definisinya tidak tercantum di slide manapun.
* **Pertanyaan untuk Klien:** Apa ruang lingkup spesifik yang diharapkan pada modul FR-1.4: apakah formulir pendaftaran profil legal klien dan master data kontak, atau mencakup verifikasi NPWP dan kontrak legal maklon?

---

*Register disusun dan dikonsolidasi oleh Lead Solution Architect untuk disajikan kepada pemangku kepentingan Lukla Manufacturing.*

