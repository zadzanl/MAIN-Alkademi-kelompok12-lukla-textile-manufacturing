# **LEMBAR PERSETUJUAN DOKUMEN**

| Peran / Jabatan | Nama Pejabat | Entitas | Status | Tanggal |
| :---- | :---- | :---- | :---- | :---- |
| Executive Sponsor / Owner | \[NAMA \- WAJIB DIISI\] | Lukla Mfg | Pending Review | \- |
| Head of Operations / Plant Manager | \[NAMA \- WAJIB DIISI\] | Lukla Mfg | Pending Review | \- |
| Finance & Commercial Lead | \[NAMA \- WAJIB DIISI\] | Lukla Mfg | Pending Review | \- |
| Lead Solution Architect | \[NAMA \- WAJIB DIISI\] | Consulting Team | Pending Review | \- |
| Lead Software Engineer | \[NAMA \- WAJIB DIISI\] | Engineering Team | Pending Review | \- |

# **BUSINESS REQUIREMENTS DOCUMENT (BRD) LUKLA OPERATIONS ENGINE**

Nama Proyek: ***Lukla Operations Engine***

Entitas Bisnis: Lukla Manufacturing (Fasilitas Konveksi Ciwidey) x Snøhund

Lokasi Fasilitas: Ciwidey, Kabupaten Bandung, Jawa Barat

Versi Dokumen: 2.3.0

Tanggal Rilis: 12 Oktober 2026

Status Dokumen: Draft \- Menunggu Persetujuan

Klasifikasi: Internal Confidential / Restricted Enterprise Blueprint

# **RIWAYAT REVISI DOKUMEN**

*Versi 0.1.0 (12/10/2026) | Disetujui Oleh: Engineering Team | Penulis: Engineering Team | Deskripsi: Draft dekonstruksi awal dari slide presentasi pitch deck.*

*Versi 1.0.0 (12/10/2026) | Disetujui Oleh: Engineering Team | Penulis: Engineering Team | Deskripsi: Peringkasan dokumen*

*Versi 2.0.0 (12/10/2026) | Disetujui Oleh: Engineering Team | Penulis: Engineering Team | Deskripsi: Adversarial review, kemudian revisi. Integrasi akuntansi double-entry, dampak neraca/pembukuan, pemetaan alur As-Is vs To-Be, matriks prioritas kebutuhan fungsional, skema anti-kontaminasi silang, kalkulasi upah borongan (piece-rate), pembagian bonus QC 3 arah, dan biaya overhead per unit.*

*Versi 2.2.0 (12/10/2026) | Disetujui Oleh: Engineering Team | Penulis: Engineering Team | Deskripsi: Update komprehensif menindaklanjuti Approval Gate, Matriks Peran & Akuntabilitas, Alur Kerja To-Be & Diagram Mermaid, Resequencing Sprint & Scrum Cadence, Product Backlog 22 FR, dan Acceptance Criteria Test Scenarios.*
*Versi 2.3.0 (12/10/2026) | Disetujui Oleh: Engineering Team | Penulis: Engineering Team | Deskripsi: Audit traceability terhadap 00-deconstruction.md rev 4; koreksi inventaris FR, pemulihan FR-9.1/FR-9.2, penandaan sumber, dan konsolidasi pertanyaan UNRESOLVED.*

# **DAFTAR ISI**

1. ***Ringkasan Eksekutif***
2. ***Deskripsi Proyek***
3. ***Ruang Lingkup Proyek***
4. ***Pendorong Bisnis***
5. ***Proses Operasional Saat Ini (As-Is)***
6. ***Proses Operasional Usulan (To-Be)***
7. ***Kebutuhan Fungsional***
8. ***Kebutuhan Non-Fungsional***
9. ***Dampak Laporan Keuangan & Neraca***
10. ***Analisis Biaya & Manfaat***
11. ***Kebutuhan Sumber Daya***
12. ***Jadwal, Tonggak Pencapaian & Tenggat Waktu***
13. ***Asumsi & Batasan Bisnis***
14. ***Glosarium Terminologi***
15. ***Referensi Dokumen***
16. ***Lampiran Teknis & Spesifikasi Sistem***

# **1\. RINGKASAN**

Lukla Manufacturing menjalankan pabrik konveksi pakaian di Ciwidey, Jawa Barat, dengan kapasitas fleksibel sampai sekitar 70 mesin jahit aktif. Model bisnis Lukla Manufacturing adalah hybrid: pabrik memproduksi merek sendiri, Snøhund, dan menerima jasa maklon (manufacturing-contract toll) dari berbagai merek fashion eksternal (B2B).

Hari ini, lantai produksi dan gudang Lukla punya tiga titik rawan:

1. Bahan antarklien tercampur (kontaminasi silang): Bahan baku Klien A bisa terpakai untuk pesanan Klien B karena sistem tidak punya pembatas. Akibatnya stok kurang, kontrak jadi sengketa, dan kerugiannya sulit dipulihkan.
2. Payroll borongan berantakan saat jumlah operator naik-turun (1 sampai 70+): Pabrik tidak menggaji bulanan tetap, melainkan upah borongan (piece-rate). Rekonsiliasi manual tiap Sabtu memakan lebih dari 8 jam dan gampang salah hitung. Uang makan (10% sampai 15%) berubah-ubah, pembagian bonus QC 3 arah lambat, dan overhead bulanan pabrik tidak bisa dibebankan secara adil ke tiap potong pakaian.
3. Jejak revisi prototipe hilang (R\&D spec drift): Sampel belum tercatat digital, jadi hasil time study, spesifikasi kain, dan rate card komponen tersebar di catatan kertas. Saat order masuk produksi massal, biaya dan target jahit meleset dari rencana.

Lukla Operations Engine adalah platform manajemen operasional pabrik berbasis event-driven. Platform ini menghubungkan seluruh alur kerja (Sampel → Order → Gudang → Cutting → Jahit → QC → Payroll) di atas double-entry ledger yang immutable (tidak bisa diubah). Sistem memisahkan kepemilikan material lewat aturan program, mencatat hasil kerja lantai produksi tiap 30 menit, dan menghitung biaya komersial serta gaji secara otomatis tanpa spreadsheet manual.

# **2\. DESKRIPSI PROYEK**

Proyek ini membangun sistem inti (core operating engine) untuk konveksi garmen skala menengah di Indonesia. Kerja sama maklon Lukla terbagi dalam tiga skema komersial, dan skema itulah yang menentukan siapa pemilik fisik dan hukum atas bahan baku:

* Skema CMT (Cut, Make, Trim): Klien B2B menyediakan seluruh bahan baku utama (kain) dan bahan pembantu/aksesoris. Lukla hanya menyumbang tenaga kerja dan mesin untuk cutting, perakitan jahit (sewing assembly), dan finishing. Bahan klien berstatus titipan kustodial, bukan aset neraca Lukla.
* Skema Semi-CMT: Klien menyediakan bahan utama (kain luar/shell). Lukla mengadakan sisanya: bahan pembantu, furing, benang, kancing, dan resleting.
* Skema CMT \+ Bahan (Full Package): Lukla mengadakan semua bahan baku, kain, dan aksesoris, lalu memproduksi dari awal sampai akhir. Skema ini juga dipakai untuk merek internal Snøhund.

Platform ini menggantikan catatan kertas dan spreadsheet dengan satu sistem terpadu. Aturan integritas data berlaku pada setiap pergerakan barang dan pengakuan biaya tenaga kerja di lantai pabrik.

# **3\. RUANG LINGKUP PROYEK**

##   **3.1 Dalam Ruang Lingkup (In Scope)**

* Manajemen Multi-Tenant & Identitas Kepemilikan Material: Penandaan wajib pasangan client\_id dan order\_id pada setiap lot bahan baku, rol kain, bundel potongan, dan barang jadi. [inferred] (adopted planning detail; source concept: slide 02b)
* Validasi Anti-Kontaminasi Silang: Pembatasan sistemik setingkat basis data (database-level trigger) yang menolak penerbitan material milik Klien X untuk pesanan Klien Y. [inferred] (planning mechanism not in source; source-backed behavior is rejection)
* Manajemen Siklus Sampel & R\&D Time Study: Pelacakan versi prototipe (v1, v2, dan seterusnya), instrumen stopwatch digital pencatat waktu perakitan per komponen, penetapan konsumsi bahan, dan konversi spesifikasi master ke pesanan massal. [inferred] (planning detail; source concepts: slides 02, 03, 08)
* Pelacakan Output Lantai per 30 Menit: Terminal antarmuka ramah-sentuh bagi mandor untuk menginput jumlah hasil jahit per penjahit/komponen dalam interval 30 menit. [slide 06]
* Manajemen Alokasi Kapasitas Dinamis: Penataan lini jahit fleksibel yang mampu menampung lonjakan operator dari 1 hingga 70+ penjahit tanpa batasan slot kaku. [slide 06]
* Inspeksi Kontrol Kualitas (QC) & Taksonomi Cacat: Klasifikasi unit menjadi Pass, Repair, atau Reject/Scrap beserta pencatatan jenis cacat garmen (broken stitch, puckering, uneven seam). [inferred] (source statuses and defect-category view are on slides 05 and 08; detailed taxonomy is planning detail)
* Mesin Penggajian Borongan Mingguan: [inferred] (planning grouping of the source-backed payroll components)
  ***Kalkulasi upah borongan penjahit: jumlah unit terverifikasi dikalikan rate komponen. Perhitungan pool uang makan mengambang mingguan sebesar 10% sampai 15% dari total ongkos jahit. Perhitungan bonus QC 3 arah yang dibagi rata untuk Mandor 1, Mandor 2, dan Kepala Operasional dari unit lolos QC. Alokasi biaya overhead operasional bulanan pabrik ke per unit pakaian jadi.*** [slide 07] (the grouping is [inferred])
* Portal Eksternal Klien B2B: Akses mandiri bagi klien maklon untuk memantau status pesanan, milestone, dan saldo stok bahan titipan secara terisolasi. [inferred] (planning detail; source concept: slides 04 and 08)
* Matriks Tata Kelola & Kontrol Akses (RBAC): Penegakan hak akses dan pembatasan operasional pada 8 peran pengguna. [assumption] (FR-2.1 is not verifiable on missing slide 02c; the eight-role matrix is observed on slide 04)

## **3.2 Di Luar Ruang Lingkup (Out of Scope)**

* Kompensasi Ketenagakerjaan Statuter: Perhitungan potongan BPJS Ketenagakerjaan/Kesehatan, pajak penghasilan PPh 21, uang lembur formal, dan pesangon formal (lingkup terbatas pada upah borongan dan tunjangan makan operasional).
* Akuntansi Finansial Lengkap: Pelaporan pajak korporasi, depresiasi aset gedung/mesin, dan rekonsiliasi perbankan multi-rekening eksternal.
* Logistik Pengiriman & Armada Kendaraan: Pelacakan armada truk ekspedisi pihak ketiga atau integrasi API kurir logistik eksternal.
* Pengadaan Bahan Baku Terotomatisasi (MRP): Pengambilan keputusan pembelian kain secara otomatis dari supplier tekstil (hanya mencakup pencatatan purchase order internal).
* Aplikasi Seluler Native: Sistem dibangun berbasis Web Responsive PWA untuk perangkat desktop dan tablet sentuh industri.

# **4\. PENDORONG BISNIS**

BD-1: Proteksi Aset Kustodial & Kepatuhan Kontrak Maklon. Menghilangkan risiko tuntutan hukum dan ganti rugi material akibat kain titipan klien terpakai oleh pesanan pihak lain. Mengembalikan kepercayaan merek fashion besar untuk menaruh volume produksi maklon bernilai tinggi di Lukla.
BD-2: Efisiensi Administratif & Akurasi Penggajian Mingguan. Mengeliminasi proses rekapitulasi manual di akhir pekan yang memakan waktu 8 sampai 10 jam kerja tim keuangan. Menghilangkan sengketa perhitungan jumlah jahitan borongan dengan operator jahit.
BD-3: Optimalisasi Throughput & Visibilitas Lantai Pabrik. Mengubah tata kelola pabrik dari pemantauan pasif berbasis catatan harian menjadi pemantauan aktif berbasis interval 30 menit. Mengidentifikasi penumpukan bottleneck komponen dalam hitungan jam.
BD-4: Standarisasi Biaya Pokok Produksi (COGS Precision). Menyediakan kalkulasi biaya riil per unit pakaian jadi yang akurat (bahan baku riil \+ ongkos jahit terverifikasi \+ alokasi overhead bulanan riil), mencegah underpricing pada penawaran kontrak maklon baru.

# **5\. PROSES OPERASIONAL SAAT INI (AS-IS)**

Saat ini, seluruh operasional di pabrik Ciwidey mengandalkan dokumen kertas fisik (surat jalan, travel card bundel, kartu borongan) dan spreadsheet terpisah. Titik masalah utama alur As-Is:

1. Penerimaan Gudang: Stok titipan klien bercampur dengan stok kain milik Snøhund di rak yang sama tanpa identitas sistemik yang memblokir pengeluaran salah.
2. Lantai Produksi: Penjahit menghitung sendiri hasil produksinya di kartu kertas. Sering terjadi penggelembungan angka atau kehilangan lembaran kartu borongan.
3. Audit QC: Cacat kain baru diketahui di tahap akhir tanpa keterlacakan penjahit mana yang bertanggung jawab atas komponen cacat tersebut.
4. Rekonsiliasi Payroll: Setiap Sabtu sore, tim finance harus merekapitulasi data borongan untuk sekitar 70 penjahit dengan rumus uang makan dan bonus mandor secara manual di Excel, yang rentan salah ketik formula.

# **6\. PROSES OPERASIONAL USULAN (TO-BE)**

Proses operasional To-Be mentransformasi pabrik konveksi Lukla Ciwidey menjadi ekosistem digital berbasis event-driven. Seluruh pergerakan barang, pencatatan hasil kerja, hingga perhitungan gaji dikunci dalam aturan immutable double-entry ledger untuk menjamin transparansi, ketepatan waktu, dan eliminasi kontaminasi silang material.

## **6.1 Enam Fase Operasional To-Be**

* Fase 1: Penerimaan & Pengelolaan Gudang (Segregasi Multi-Tenant). Setiap material yang masuk wajib mencantumkan tag client\_id dan order\_id. Sistem secara otomatis mencatat persediaan CMT sebagai aset kustodial (off-balance sheet) dan menolak pencampuran lot antar-klien. [inferred] (planning detail; source concepts: slides 03, 04, 04b, 08)
* Fase 2: R\&D, Sampel & Time Study. Tim sampel memproduksi prototipe, merekam waktu kerja per komponen via instrumen digital, dan mengunci Master Spec Sheet serta Rate Card sebelum produksi massal dimulai. [inferred] (planning detail; source concepts: slides 03, 06, 08)
* Fase 3: Pemotongan (Cutting) & Validasi Guardrail. Sebelum kain dipotong, an implementation mechanism may verify kesesuaian client\_id bahan dengan Work Order [inferred] (planning detail not in source); source-backed behavior is rejection of a mismatched material/order. Jika cocok, surat perintah potong diterbitkan dan bundel diberi barcode. [inferred] (adopted workflow detail; ownership remains unresolved)
* Fase 4: Eksekusi Lantai Produksi (Shop Floor MES). Mandor menginput hasil jahit per penjahit/komponen pada terminal layar sentuh setiap interval 30 menit. Data langsung tercatat di ledger sebagai unit 'Menunggu QC'. [slide 06] (ledger implementation detail is inferred)
* Fase 5: Inspeksi Kontrol Kualitas (QC). Petugas QC memindai unit dan menetapkan status: Pass (siap kemas & hak gaji aktif), Repair (kembali ke penjahit tanpa gaji ganda), atau Reject (scrap/potong gaji). [inferred] (workflow detail; source-backed status/routing is on slide 05)
* Fase 6: Payroll & Kalkulasi COGS Otomatis. Setiap Sabtu, sistem merekap upah borongan unit Pass, menghitung pool uang makan mengambang (10%-15%), membagi bonus QC 3 arah, dan mengalokasikan overhead pabrik per unit. [inferred] (planning grouping; source components: slide 07 chat attachment)

## **6.2 Matriks Perbandingan Proses As-Is vs To-Be**

| Area Operasional | Proses Saat Ini (As-Is) | Proses Usulan (To-Be) | Dampak Bisnis |
| :---- | :---- | :---- | :---- |
| Penerimaan Bahan | Manual, tanpa tag unik per klien, rentan tertukar | Sistemic Tagging (client\_id & order\_id), Kustodial Off-Balance Sheet | Eliminasi sengketa klaim bahan 100% |
| Gudang & Cutting | Pemeriksaan visual manual oleh staf gudang | Anti-Cross Contamination Guardrail (Db Trigger blocking) [inferred] (planning detail not in source) | Mencegah salah potong bahan (hemat Rp 15-40jt/insiden) |
| R\&D & Rate Card | Catatan kertas, estimasi waktu tidak terstandar | Digital Time Study per komponen, Master Spec terkunci | Akurasi COGS & margin kontrak terjaga |
| Lantai Jahit | Kartu borongan kertas, dihitung akhir hari/minggu | Floor Terminal Touchscreen, input interval 30 menit | Visibilitas realtime & deteksi bottleneck cepat |
| Inspeksi QC | Pencatatan manual di akhir jalur, tanpa melacak penjahit | QC Terminal Scan, taksonomi cacat terhubung ke penjahit | Tanggung jawab kualitas & perbaikan tanpa upah ganda |
| Payroll & Financial | Rekap Excel Sabtu \>8 jam, formula rawan eror | Otomatisasi kalkulasi Sabtu \<15 menit, ledger immutable | Efisiensi admin 95% & klaim upah presisi |

## **6.3 Diagram Alur Kerja End-to-End To-Be (Mermaid Flowchart)**

# **![][image1]**

# **7\. KEBUTUHAN FUNGSIONAL**

Skala Prioritas Kebutuhan

* 1 (Critical): Wajib ada pada peluncuran perdana. Kegagalan fungsi ini menyebabkan sistem tidak dapat beroperasi atau melanggar integritas finansial/kustodial.
* 2 (High): Sangat penting untuk keberhasilan proyek, namun sistem masih dapat berjalan secara terbatas.
* 3 (Medium): Memberikan nilai tambah efisiensi operasional.
* 4 (Low): Fitur pendukung kenyamanan operasional.
* 5 (Future): Di luar cakupan rilis saat ini.

## **Matriks Kategori Kebutuhan Fungsional**

## **Kategori RC1: Manajemen Multi-Tenant & Keamanan Akses**

* ID FR-1.1 (Prioritas: 1 \- Critical) oleh Owner & Legal. Sistem harus mengisolasi seluruh data operasional dan inventaris secara multi-tenant sehingga data Klien B2B tidak dapat diakses oleh klien lain. [slide 02b; slide 03]
* ID FR-2.1 (Prioritas: 1 \- Critical) oleh Executive Management. Sistem harus menegakkan kontrol akses berbasis peran (RBAC) pada 8 peran pengguna. [assumption] (slide 02c missing; role count on slide 04) The exact boundary between operational recording and financial adjustments is [inferred] (planning detail not in source) and remains subject to the future RBAC matrix.
* ID FR-3.1 (Prioritas: 1 \- Critical) oleh Finance & Auditor. Sistem harus mencatat seluruh riwayat revisi dan transaksi ke dalam audit trail yang bersifat append-only. [slide 02; slide 03]

## **Kategori RC2: Siklus Sampel, Time Study & R\&D Garmen**

* ID FR-4.1 (Prioritas: 2 \- High) oleh Tim Sample / Adis. Sistem harus mengelola siklus versi sampel prototipe dengan menyimpan riwayat perubahan parameter jahitan dan spesifikasi kain. [slide 02; slide 03]
* ID FR-4.2 [inferred] (planning detail not in source) (Prioritas: 2 \- High) oleh Kepala Produksi. Sistem harus menyediakan instrumen pencatatan time study per komponen garmen. [inferred] (detail instrumen tidak ditentukan sumber)
* ID FR-4.3 [inferred] (planning detail not in source) (Prioritas: 1 \- Critical) oleh Tim Sample & Owner. Sistem harus menghasilkan Master Spec Sheet terkunci saat sampel disetujui klien. [inferred] (detail penguncian tidak ditentukan sumber)

## **Kategori RC3: Manajemen Gudang, Bahan Kustodial & Cutting**

* ID FR-5.1 [inferred] (planning detail not in source) (Prioritas: 1 \- Critical) oleh Warehouse Manager. Mewajibkan input identitas pemilik (client\_id) dan alokasi pesanan (order\_id) saat penerimaan bahan baku kain.
* ID FR-5.2 [inferred] (planning detail not in source) (Prioritas: 1 \- Critical) oleh Finance Officer. Pencatatan penerimaan bahan titipan tanpa membebankannya sebagai hutang dagang lancar perusahaan.
* ID FR-6.1 [inferred] (planning detail not in source) (Prioritas: 2 \- High) oleh Warehouse Manager. Mengelola pencatatan stok opname secara real-time.
* ID FR-6.2 (Prioritas: 1 \- Critical) oleh Executive. The source-backed behavior is rejection of an attempt to issue Client A material for a Client B order. [slide 02; slide 09; enforcement corroborated by slide 04; slide 08] **UNRESOLVED:** module ownership is not settled between Gudang, Cutting, or both/keduanya; this BRD does not assign an owner.
* ID FR-6.3 [inferred] (planning detail not in source) (Prioritas: 2 \- High) oleh Kepala Produksi. Mencatat hasil pemotongan kain massal, rasio limbah kain, dan efisiensi konsumsi.

## **Kategori RC4: Eksekusi Lantai Produksi (Shop Floor MES)**

* ID FR-7.1 (Prioritas: 1 \- Critical) oleh Kepala Produksi. Mendukung pengaturan tata letak lini produksi dinamis dan alokasi fleksibel operator penjahit. [slide 06]
* ID FR-7.2 (Prioritas: 1 \- Critical) oleh Owner. Mengelola rate card ongkos jahit per komponen artikel berdasarkan hasil time study. [slide 06]
* ID FR-7.3 (Prioritas: 1 \- Critical) oleh Mandor. Menyediakan antarmuka terminal sentuh bagi mandor untuk menginput jumlah hasil jahit dalam blok interval 30 menit. [slide 06]
* ID FR-7.4 (Prioritas: 1 \- Critical) oleh Mandor & Finance. Setiap unit komponen hasil jahit otomatis berstatus Menunggu QC dan mengikat hak upah bersyarat bagi operator. [slide 06]

## **Kategori RC5: Kontrol Kualitas (QC) & Penanganan Cacat**

* ID FR-8.1 (Prioritas: 1 \- Critical) oleh QC Inspector. Antarmuka terminal QC untuk mengklasifikasikan unit menjadi Pass, Repair, atau Reject. [slide 05]
* ID FR-8.2 (Prioritas: 2 - High) oleh QC Inspector. Mengembalikan unit Repair ke penjahit yang sama tanpa kredit upah borongan ganda. [slide 05]
* [Removed: BRD-only duplicate; this requirement is FR-8.2. [slide 05]]

* ID FR-9.1 (Prioritas: 1 \- Critical) oleh Executive. Setiap unit Pass QC menambah bonus pool. [slide 05]
* ID FR-9.2 (Prioritas: 1 \- Critical) oleh Executive. Bonus pool dibagi 3 arah kepada Mandor 1, Mandor 2, dan Kepala Operasional, dibayarkan bersama payroll mingguan. [slide 05]

## **Kategori RC6: Mesin Penggajian Fleksibel & Penetapan Biaya**

* ID FR-10.1 (Prioritas: 1 \- Critical) oleh Finance. Mengkalkulasi upah borongan mingguan penjahit secara otomatis setiap hari Sabtu. [slide 07] (chat attachment; corroborated by slides 03 and 08)
* ID FR-10.2 (Prioritas: 1 \- Critical) oleh Finance. Menghitung akumulasi pool uang makan mengambang mingguan (10% sampai 15%). [slide 07] (chat attachment; corroborated by slide 08)
* ID FR-10.3 (Prioritas: 1 \- Critical) oleh Executive. Mengumpulkan dana bonus QC dan membaginya sama rata menjadi 3 bagian untuk mandor dan kepala operasional. [slide 07] (chat attachment; corroborated by slide 05)
* ID FR-10.4 (Prioritas: 2 \- High) oleh Finance. Merekapitulasi total biaya overhead bulanan dan menghitung alokasi beban overhead per unit garmen jadi. [slide 07] (chat attachment; corroborated by slide 08)

**Cross-note:** FR-9.2 and FR-10.3 are two source IDs for one shared divide-by-three bonus rule; they must not become two independent rules or acceptance tests. [slide 05; slide 07]

# **8\. KEBUTUHAN NON-FUNGSIONAL**

* NFR-01 (Multi-Tenant Data Isolation): Pemisahan logis data antar-klien. Kueri data portal klien wajib memiliki predikat client\_id. Toleransi kebocoran data adalah 0%. [inferred] (planning detail not in source; source concept: slides 02b, 04, 08)
* NFR-02 (Ledger Immutability): Setiap transaksi dicatat dengan prinsip append-only. Pembatalan transaksi melalui transaksi pembalik tanpa operasi UPDATE/DELETE pada tabel buku besar. [inferred] (planning detail not in source; source concept: slides 02, 03)
* NFR-03 (Floor Terminal Response Time): Waktu respon antarmuka sentuh tidak boleh melebihi 500 milidetik. [inferred] (adopted technical planning target; no source threshold)
* NFR-04 (Concurrency): Basis data harus menangani penulisan data bersamaan dari minimal 10 lini jahit pada jendela waktu 30 menit tanpa deadlock. [inferred] (adopted technical planning target; no source threshold)
* NFR-05 (Offline Tolerance): Terminal produksi memiliki local cache sehingga mandor tetap dapat menginput saat WiFi pabrik gangguan sementara. [inferred] (adopted technical planning detail; no offline behavior is specified by the source)
* NFR-06 (Kompatibilitas Layar Sentuh): Antarmuka dirancang dengan tombol minimal 48x48 piksel. [inferred] (adopted technical planning target; slide 06 only establishes a touch-friendly terminal)

# **9\. DAMPAK LAPORAN KEUANGAN & NERACA** [inferred]

## **9.1 Perlakuan Akuntansi Persediaan Kustodial vs Aset Perusahaan Kelemahan pencatatan konvensional adalah mencampuradukkan kain titipan klien dengan persediaan aset pabrik, yang mendistorsi nilai likuiditas dan menimbulkan risiko hukum kepailitan.**

1. Pada Skema CMT (Bahan Titipan Klien) Bahan baku dicatat pada akun persediaan titipan di luar neraca aset lancar perusahaan. Debit: Persediaan Kustodial Titipan / Kredit: Liabilitas Kustodial Klien. Mutasi ini tidak menambah aset lancar Lukla.
2. Pada Skema Full Package (Bahan Milik Perusahaan) Pembelian kain dicatat sebagai aset lancar perusahaan. Debit: Persediaan Bahan Baku (Aset Lancar) / Kredit: Hutang Usaha atau Kas.
3. Kapitalisasi Biaya Tenaga Kerja Langsung (WIP Transformation) Nilai jasa tenaga kerja langsung dikapitalisasi ke dalam persediaan barang dalam proses setiap interval 30 menit. Debit: Persediaan Barang Dalam Proses (WIP) / Kredit: Beban Akrual Gaji Terutang.

## **9.2 Dampak Arus Kas & Modal Kerja Otomatisasi kalkulasi Cost of Goods Sold (COGS) memastikan penerbitan faktur dapat dilakukan seketika, memperpendek siklus konversi kas dari 35 hari menjadi di bawah 14 hari.**

# **10\. ANALISIS BIAYA & MANFAAT**

## **10.1 Estimasi Biaya Proyek**

* Pengadaan 4 unit tablet Android industri untuk lini jahit, 2 unit untuk pos gudang dan QC, serta 2 Access Point WiFi High-Density.
* Alokasi tim pengembang perangkat lunak dan infrastruktur server cloud/lokal di Ciwidey.
* Biaya pelatihan operasional mandor, staf gudang, QC, dan keuangan selama 1 minggu.

## **10.2 Manfaat**

* Berwujud: Mencegah kerugian penggantian kain akibat salah potong.
* Berwujud: Mereduksi waktu kerja staf Finance dari 8 jam menjadi kurang dari 15 menit per minggu.
* Berwujud: Mencegah kebocoran penggelembungan hasil jahit (efisiensi 5% \- 8%).
* Tak Berwujud: Transparansi data R\&D ke produksi massal dan peningkatan kepercayaan klien B2B.

# **11\. KEBUTUHAN SUMBER DAYA**

## **11.1 Matriks Peran Proyek, Tanggung Jawab & Akuntabilitas (project-delivery governance/RACI)**

This is a project-delivery governance/RACI matrix, distinct from the 8 system RBAC roles defined by the source on slide 04. It must not be used as the system permission matrix. The future RBAC matrix must cross-link to the complete slide-04 role set, including Gudang/Warehouse, Penjahit/Tailor, QC Inspector, Finance & Payroll, and Klien Maklon/Ext.

| Peran Proyek | Nama Pejabat | Entitas | Tanggung Jawab Utama | Tingkat Akuntabilitas |
| :---- | :---- | :---- | :---- | :---- |
| Executive Sponsor / Owner | \[NAMA \- WAJIB DIISI\] | Lukla Mfg | Persetujuan anggaran, penetapan arah strategis, penyelesaian eskalasi bisnis | Accountable (A) |
| Head of Operations / Plant Manager | \[NAMA \- WAJIB DIISI\] | Lukla Mfg | Pemilik proses bisnis lapangan, adopsi terminal jahit/QC, manajemen mandor | Responsible (R) |
| Finance & Commercial Lead | \[NAMA \- WAJIB DIISI\] | Lukla Mfg | Validasi formula payroll, audit kustodial, alokasi overhead bulanan | Responsible (R) |
| Lead Solution Architect | \[NAMA \- WAJIB DIISI\] | Consulting | Desain arsitektur event-driven, integritas schema ledger, tata kelola teknis | Accountable (A) |
| Lead Software Engineer | \[NAMA \- WAJIB DIISI\] | Engineering | Pengembangan backend/frontend, implementasi DB triggers & guardrails [inferred] (planning detail not in source) | Responsible (R) |
| Warehouse & Cutting Supervisor | \[NAMA \- WAJIB DIISI\] | Lukla Mfg | Eksekusi tagging multi-tenant, verifikasi penerbitan kain & bundel potong | Consulted / Informed |
| Quality Control (QC) Lead | \[NAMA \- WAJIB DIISI\] | Lukla Mfg | Eksekusi terminal QC, pengujian taksonomi cacat, validasi bonus QC | Consulted / Informed |

* Internal Executive: Penentu kebijakan dan rate card.
* Kepala Pabrik: Pemilik proses bisnis lapangan.
* Lead System Architect: Penanggung jawab integritas database.
* Tim Sample: Penguji modul time study.
* Mandor & Penjahit: Pengguna uji coba terminal sentuh.

## **11.2 Infrastruktur Pabrik**

* Tablet sentuh 10 inci berpelindung debu, Jaringan LAN/WiFi terdistribusi di area pabrik, 2 PC desktop untuk Finance/Admin.

# **12\. JADWAL, TONGGAK PENCAPAIAN, RE-SEQUENCING SPRINT & TATA KELOLA SCRUM** [inferred]

**Aturan Start Gate:** Pengembangan perangkat lunak (Sprint 1\) TIDAK BOLEH dimulai sebelum seluruh pejabat pada Lembar Persetujuan Dokumen menandatangani BRD v2.3.0 ini secara resmi.

## **12.1 Matriks Ketergantungan Modul & Urutan Eksekusi**

| Modul ID | Nama Modul | Modul Prasyarat (Prerequisites) | Justifikasi Urutan |
| :---- | :---- | :---- | :---- |
| MOD-01 | Core Ledger & RBAC | Tidak ada (Fondasi Dasar) | Buku besar immutable dan peran RBAC mendasari seluruh transaksi |
| MOD-02 | Multi-Tenant Warehouse & Guardrail | MOD-01 | Stok kustodial dan anti-kontaminasi harus aktif sebelum transaksi bahan |
| MOD-03 | Sample R\&D & Rate Card Engine | MOD-01, MOD-02 | Master Spec dan Rate Card dibutuhkan untuk menghitung upah jahit |
| MOD-04 | Shop Floor MES & Terminal QC | MOD-02, MOD-03 | Pencatatan jahit 30 menit & QC membutuhkan Rate Card dan Data Order |
| MOD-05 | Payroll Borongan & COGS Costing | MOD-04 | Penggajian dan COGS membutuhkan data unit Pass dari Terminal QC |

## **12.2 Rencana 5 Sprint Vertical-Slice (13 Oktober \- 21 Desember 2026\)**

### **Sprint 1: Core Double-Entry Ledger, RBAC & Tenant Isolation (13 \- 26 Okt 2026\)**

* Ruang Lingkup: Membangun schema database append-only ledger, autentikasi RBAC 8 peran, dan predikat isolasi multi-tenant (FR-1.1, FR-2.1, FR-3.1). [inferred] (sprint packaging; cited FR meanings retain their individual status)

### **Sprint 2: Multi-Tenant Warehouse, Off-Balance Sheet & Anti-Cross Contamination Guardrail (27 Okt \- 09 Nov 2026\)**

* Ruang Lingkup: Penerimaan bahan dengan tag client\_id/order\_id, perlakuan akuntansi kustodial, dan database trigger pemblokir kontaminasi silang [inferred] (planning detail not in source) (FR-5.1 [inferred], FR-5.2 [inferred], FR-6.1 [inferred], FR-6.2, FR-6.3 [inferred]).

### **Sprint 3: Sample Lifecycle, Time Study, Master Spec & Shop Floor MES (10 \- 23 Nov 2026\)**

* Ruang Lingkup: Pengelolaan versi sampel, stopwatch time study, penguncian Rate Card, penataan lini jahit, dan terminal touch 30 menit (FR-4.1, FR-4.2 [inferred], FR-4.3 [inferred], FR-7.1, FR-7.2, FR-7.3, FR-7.4). Sprint packaging detail is [inferred] (not source-backed).

### **Sprint 4: QC Terminal, Defect Taxonomy & Automated Payroll Engine (24 Nov \- 07 Des 2026\)**

* Ruang Lingkup: Terminal QC (Pass/Repair/Reject), alur perbaikan tanpa gaji ganda, rekap borongan Sabtu, pool uang makan, bonus QC 3 arah, dan COGS overhead (FR-8.1, FR-8.2, FR-10.1, FR-10.2, FR-10.3, FR-10.4). [slide 05; slide 07] (the sprint packaging and dates are [inferred]; the cited FR meanings remain source-statused individually)

### **Sprint 5: B2B Client Portal, End-to-End Integration & UAT Readiness (08 \- 21 Des 2026\)**

* Ruang Lingkup: Portal mandiri klien B2B, pengujian integrasi 6 antarmuka UI, validasi NFR performance, dan persiapan peluncuran Go-Live (Portal B2B & E2E UI Suite).

## **12.3 Tonggak Pencapaian Berdampak Pengguna (User-Facing Milestones)**

* Milestone M1 (26 Okt 2026): 'Fondasi Data Sehat' \- Sistem RBAC & Buku Besar Terverifikasi Audit.
* Milestone M2 (09 Nov 2026): 'Gudang Bebas Salah Kain' \- Fitur Anti-Kontaminasi Silang Lulus Uji Coba Lapangan.
* Milestone M3 (23 Nov 2026): 'Digital Touch Floor' \- Terminal Jahit 30 Menit & Rate Card Aktif di Lini Produksi.
* Milestone M4 (07 Des 2026): 'Gaji Sabtu Otomatis' \- Eksekusi Formula Borongan, Uang Makan & Bonus QC Tepat Presisi.
* Milestone M5 (21 Des 2026): 'Sistem Siap Go-Live' \- Portal B2B Aktif & UAT End-to-End Disetujui Manajemen.

## **12.4 Tata Kelola & Kadensi Agil / Scrum**

* Sprint Planning: Dilakukan setiap Senin pagi di awal Sprint (Durasi 2 jam) untuk menyetujui Sprint Backlog.
* Daily Standup: Pertemuan 15 menit setiap jam 08.30 WIB via Google Meet/On-site Ciwidey untuk mengidentifikasi hambatan (blockers).
* Sprint Review & Demo: Dilakukan pada Jumat sore di akhir Sprint (Durasi 1 jam) untuk mendemonstrasikan increment kepada Stakeholder Lukla.

# **Sprint Retrospective: Evaluasi internal tim teknis setelah Sprint Review untuk perbaikan proses berkelanjutan.**

## **Sprint 1: Double-Entry Core & RBAC Engine ( \- 2026\)**

## **Sprint 2: Multi-Tenant Inventory & Guardrail ( \- 2026\)**

## **Sprint 3: Sample Lifecycle, Order & MES Floor ( \- 2026\)**

## **Sprint 4: Payroll Borongan & QC Bonus Engine ( \- 2026\)**

## **Sprint 5: UI Suite & Validasi End-to-End ( \- 2026\)**

## **Tonggak Pencapaian Kritis (Major Milestones)**

* Milestone 1 (26 Okt): Fondasi basis data double-entry dan RBAC 8 peran teruji.
* Milestone 2 (09 Nov): Pengujian Skenario Pencegahan Kontaminasi Silang lulus validasi.
* Milestone 3 (23 Nov): Transisi spesifikasi sampel ke pesanan massal berhasil.
* Milestone 4 (07 Des): Eksekusi formula payroll hari Sabtu terverifikasi presisi.
* Milestone 5 (21 Des): Uji coba menyeluruh 6 antarmuka; sistem siap Go-Live.

# **13\. ASUMSI & BATASAN BISNIS**

## **13.3 Gaps and Open Questions [inferred from register rev 4]**

The following items remain explicitly unresolved because the source deck does not decide them. They must not be implemented as settled requirements:

1. **UNRESOLVED - not in source:** Slide 02c is unavailable; FR-2.1's original three-pillar wording cannot be verified.
2. **UNRESOLVED - not in source:** The original on-disk slide 07 is unavailable; the available chat transcription is retained as `[slide 07]` (chat attachment).
3. **UNRESOLVED - not in source:** FR-5 Gudang detail: inventory transactions, adjustment rules, and stock-opname procedure are unspecified.
4. **UNRESOLVED - not in source:** FR-6 Cutting detail: batches, markers, wastage, and cutting-output recording are unspecified; FR-7.3 records sewing output.
5. **UNRESOLVED - not in source:** FR-1.4 has an observed badge but no definition text.
6. **UNRESOLVED - not in source:** Whether the fixed bonus split of 2 mandor plus 1 kepala operasional is configurable is unspecified.
7. **UNRESOLVED - not in source:** The base definition for the 10–15% uang makan calculation is unspecified.
8. **UNRESOLVED - not in source:** No material illegible source spots remain; this is recorded for register parity, not as a requirement.

This subsection consolidates the eight unresolved items in `00-deconstruction.md` revision 4, including the unresolved Gudang/Cutting/both ownership of FR-6.2 and the unresolved bonus remainder handling. Any additional BRD detail marked `[inferred]` or `[assumption]` is planning content, not source-backed functional scope.

## **13.1 Asumsi Operasional**

* Skala kapasitas adalah sekitar 70 mesin jahit.
* Mandor memiliki disiplin melakukan input verifikasi setiap 30 menit.
* Persentase uang makan (10% \- 15%) ditentukan manual oleh Finance.
* Bonus QC dibagi rata untuk 3 pimpinan lapangan (2 Mandor Lini, 1 Kepala Ops). [slide 05] UNRESOLVED - not in source: konfigurabilitas penerima belum ditentukan.

## **13.2 Batasan Sistemik**

* Catatan transaksi buku besar yang sudah dikunci bersifat absolut, tidak dapat diubah oleh siapapun.
* Penerbitan surat perintah potong wajib merujuk pada lot bahan yang terverifikasi di gudang. [inferred] UNRESOLVED - not in source: detail aturan Gudang/Cutting tidak ditentukan.
* UNRESOLVED - not in source: penanganan pembulatan dan sisa bonus QC belum ditentukan; jangan mengalokasikan sisa ke rekening tertentu.

# **14\. GLOSARIUM TERMINOLOGI**

* Maklon: Kerja sama klien menyerahkan produksi pakaian kepada Lukla.
* CMT: Klien menyediakan 100% bahan baku; Lukla menyediakan jasa jahit dan finishing.
* Semi-CMT: Klien menyediakan kain utama; Lukla menyediakan furing dan aksesoris.
* Full Package: Lukla menyediakan seluruh bahan baku dan jasa produksi.
* Borongan: Kompensasi kerja berdasarkan jumlah unit fisik yang diselesaikan.
* Uang Makan: Tunjangan mingguan 10%-15% dari total ongkos jahit.
* Rate Card: Tabel tarif upah per komponen garmen hasil time study.
* Titipan / Konsinyasi: Bahan milik klien yang disimpan di gudang Lukla.
* Kontaminasi Silang: Kesalahan bahan titipan Klien A terpakai untuk Klien B.

# **15\. REFERENSI DOKUMEN**

1. Slide Pitch Deck Lukla Operations Engine (Slide 00 \- 09).
2. OpenSpec Architecture Blueprint: artifacts/overall-plan-draft.md.
3. OpenSpec Source Deconstruction & Traceability Register.
4. Standard Operating Procedure (SOP) Produksi Konveksi Lukla.

# **16\. LAMPIRAN TEKNIS & SPESIFIKASI SISTEM**

## **16.1 Formulasi Matematis Perhitungan Payroll & Biaya**

1. Upah Borongan Mingguan Penjahit: Dihitung setiap Sabtu. Upah Penjahit \= Total penjumlahan dari (Unit Terverifikasi dikalikan Tarif Upah Komponen).
2. Pool Uang Makan Mengambang: Total Uang Makan \= Persentase Uang Makan dikalikan Total Upah Seluruh Penjahit.
3. Pembagian Bonus Kontrol Kualitas: Total Dana QC \= Total Pakaian Lolos QC dikalikan Tarif Bonus Per Pakaian. Bonus Mandor \= Total Dana QC dibagi 3. UNRESOLVED - not in source: penanganan pembulatan/sisa belum ditentukan.
4. Alokasi Biaya Overhead Pabrik per Unit Pakaian: Overhead per Unit \= Total Biaya Operasional Pabrik Bulanan dibagi Total Unit Pakaian Jadi yang Diproduksi Bulan Tersebut.

## **16\.2 Logika Basis Data Anti-Kontaminasi Silang [inferred]** (planning detail not in source; source-backed behavior is rejection) Integritas segregasi ditegakkan pada tingkat transaksi.

Sistem akan mengambil ID Klien pemilik pesanan target dan ID Klien pemilik bahan yang dikeluarkan. Jika keduanya tidak sama, sistem secara otomatis menolak transaksi dengan pesan peringatan: **[inferred]** (illustrative UI copy, not a source-prescribed string) `CRITICAL VIOLATION - Upaya pengeluaran bahan milik Klien A untuk pesanan Klien B DITOLAK`.

## **16.3 Spesifikasi Minimum Required UI Views**

* VIEW 01: Executive Operations Dashboard (Menampilkan grafik output 30 menit dan matriks progres order). [slide 08]
* VIEW 02: Sample & Time Study Tracker (Menampilkan instrumen stopwatch untuk merekam waktu penjahitan komponen). [slide 08]
* VIEW 03: Multi-Client Warehouse Inventory Grid (Tabel stok dengan peringatan pop-up jika terjadi tabrakan pemilik bahan). [slide 08]
* VIEW 04: Floor Terminal (Antarmuka tombol besar sentuh untuk input hasil jahit tiap penjahit pada blok interval 30 menit). [slide 08]
* VIEW 05: QC Inspection Terminal (Menu pemindaian nomor serial dengan tombol Pass, Repair, atau Reject). [slide 08]
* VIEW 06: Payroll & Costing Workspace (Layar rekap total borongan murni, alokasi uang makan, dan penentuan overhead akhir minggu). [slide 08]

## **16.4 Empat Skenario Pengujian Penerimaan Bisnis (Acceptance Test Scenarios)**

1. Skenario Pencegahan Kontaminasi: Sistem menggagalkan transaksi jika bahan Klien A akan dipotong untuk pesanan Klien B. [slide 09]
2. Penambahan Tenaga Dinamis: Mandor mendaftarkan penjahit baru di hari Kamis, sistem tetap dapat merekap gaji mereka pada hari Sabtu beserta persentase uang makan tanpa me-restart siklus. [slide 09]
3. Pembagian Bonus Rata: 3.000 unit lolos QC dikali tarif bonus, kemudian dana dibagi menjadi 3 bagian untuk 3 pimpinan lapangan. UNRESOLVED - not in source: penanganan pembulatan/sisa belum ditentukan. [slide 09]
4. Transisi Revisi Sampel: Sistem mengubah sampel disetujui (v2) menjadi pesanan massal dengan mewarisi secara otomatis spesifikasi dan rate card sebelumnya. [slide 09]

# **16.5 Lampiran: Product Backlog Komprehensif (observed FR inventory) [slide 03; slide 05; slide 06; slide 07]**

| FR ID | One-line meaning | Sumber |
|---|---|---|
| FR-1.1 | Multi-tenant platform; data isolated per client | [slide 03; slide 02b] |
| FR-1.4 | Client/order onboarding element (definition text unavailable) | [slide 03] |
| FR-2.1 | Role-based access control (8-role matrix on slide 04) | [assumption; slide 04] |
| FR-3.1 | Audit trail / traceable history (including sample revisions) | [slide 02; slide 03] |
| FR-4.1 | Sample revision tracking / versioning (v1, v2, …) | [slide 02; slide 03] |
| FR-5 | Gudang (warehouse) phase — multi-client stock, consignment receiving | [slide 03; slide 02] |
| FR-6 | Cutting phase | [slide 03] |
| FR-6.2 | Cross-client contamination guardrail — reject Client A material for Client B order. **UNRESOLVED:** ownership is not settled between Gudang, Cutting, or both/keduanya; this backlog does not assign an owner. | [slide 02; slide 09; enforcement corroborated by slide 04; slide 08] |
| FR-7.1 | Alokasi Kapasitas Dinamis — lines rearranged by active sewer count per day; “Tidak ada slot kaku” | [slide 06] |
| FR-7.2 | Rate Card per Artikel & Klien — per-component ongkos jahit differs per article; rate card managed by Owner | [slide 06] |
| FR-7.3 | Output 30 Menit — mandor inputs sewing output per penjahit/komponen every 30 min via touch-friendly terminal | [slide 06] |
| FR-7.4 | Assembly → Menunggu QC — finished units enter QC queue; wages recognized only after QC verification | [slide 06] |
| FR-8.1 | QC inspection of every finished unit; status Pass / Repair / Reject determines next action route | [slide 05] |
| FR-8.2 | Repair tanpa Gaji Ganda — Repair unit returns to the same sewer; no double piece-rate credit | [slide 05] |
| FR-9.1 | QC bonus pool derived from QC-passed output | [slide 05] |
| FR-9.2 | Bonus pool split 3 ways: 2 mandor + 1 kepala operasional | [slide 05] |
| FR-10.1 | Every Saturday: verified component output × rate jahit per artikel; mandor verification, no sewer-count limit | [slide 07] (chat attachment); [slide 03; slide 08] |
| FR-10.2 | 10–15% of total ongkos jahit generated in one production period; percentage manually entered per period | [slide 07] (chat attachment); [slide 08] |
| FR-10.3 | Pool from QC-passed products across clients/orders at rate per pcs; ÷3 to 2 mandor + 1 kepala operasional | [slide 07] (chat attachment); [slide 05; slide 09] |
| FR-10.4 | Monthly electricity/water/internet/factory operations total ÷ all units produced that month | [slide 07] (chat attachment); [slide 08] |

**Cross-note:** FR-9.2 and FR-10.3 refer to the same divide-by-three rule under two source IDs; §16.5 remains an observed-only inventory. [slide 05; slide 07]

# **16.6 Lampiran: Acceptance Criteria & Skenario Pengujian Lanjut**

Setiap kebutuhan fungsional dalam BRD ini wajib memenuhi kriteria penerimaan berbasis skenario format Given-When-Then sebelum dinyatakan selesai (Done):

* **AC-FR-6.2 (Anti-Cross Contamination):** GIVEN lot kain roll \#R-101 terdaftar atas client\_id 'KLIEN-A', WHEN an authorized warehouse/cutting workflow attempts to issue that roll to order\_id 'ORD-B' (pemilik 'KLIEN-B'), THEN sistem menolak transaksi. Gudang/Cutting ownership remains **UNRESOLVED**; this scenario does not assign the actor or module. The rejection message shown below is illustrative only: **[inferred]** `CRITICAL VIOLATION - Materials belong to KLIEN-A`. [slide 02; slide 09] (implementation mechanism is [inferred])
* **AC-FR-8.2 (Perbaikan Tanpa Upah Ganda):** GIVEN unit garmen \#U-501 ditandai 'Repair' oleh QC akibat cacat jahitan, WHEN unit dikembalikan ke penjahit dan diselesaikan kembali ke QC, THEN sistem memverifikasi nomor unit dan TIDAK menambahkan kredit borongan baru pada akun penjahit tersebut.
* **AC-FR-10.3 (Presisi Pembagian Bonus QC 3-Arah):** GIVEN total unit lolos QC mingguan menghasilkan pool bonus Rp 100.000, WHEN sistem memproses alokasi untuk Mandor 1, Mandor 2, dan Kepala Ops, THEN sistem membagi pool menjadi tiga bagian. [slide 07; slide 05] UNRESOLVED - not in source: penanganan pembulatan/sisa belum ditentukan. This is the same divide-by-three rule as FR-9.2, referenced under two source IDs, not a second bonus rule.
