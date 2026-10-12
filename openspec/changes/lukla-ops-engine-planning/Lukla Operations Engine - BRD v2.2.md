# **BUSINESS REQUIREMENTS DOCUMENT (BRD) LUKLA OPERATIONS ENGINE**

Nama Proyek: ***Lukla Operations Engine*** 

Entitas Bisnis: Lukla Manufacturing (Fasilitas Konveksi Ciwidey) x Snøhund 

Lokasi Fasilitas: Ciwidey, Kabupaten Bandung, Jawa Barat 

Versi Dokumen: 2.1.0 

Tanggal Rilis: 12 Oktober 2026 

Status Dokumen: Siap Review & Persetujuan (Baseline v2) 

Klasifikasi: Internal Confidential / Restricted Enterprise Blueprint

# **RIWAYAT REVISI DOKUMEN** 

*Versi 0.1.0 (12/10/2026) | Disetujui Oleh: Engineering Team | Penulis: Engineering Team Deskripsi: Draft dekonstruksi awal dari slide presentasi pitch deck.* 

*Versi 1.0.0 (12/10/2026) | Disetujui Oleh: Internal Lead | Penulis: Product Lead Deskripsi: Rilis v1 ringkasan dokumen*

*Versi 2.0.0 (12/10/2026) | Disetujui Oleh: Lead Solution Architect | Penulis: Solution Architect / Consulting Director*

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

# **1\. RINGKASAN EKSEKUTIF**

1. Lukla Manufacturing menjalankan pabrik konveksi pakaian di Ciwidey, Jawa Barat, dengan kapasitas fleksibel sampai sekitar 70 mesin jahit aktif. Model bisnis Lukla Manufacturing adalah hybrid: pabrik memproduksi merek sendiri, Snøhund, dan menerima jasa maklon (manufacturing-contract toll) dari berbagai merek fashion eksternal (B2B).

Hari ini, lantai produksi dan gudang Lukla punya tiga titik rawan:

2. Bahan antarklien tercampur (kontaminasi silang): Bahan baku Klien A bisa terpakai untuk pesanan Klien B karena sistem tidak punya pembatas. Akibatnya stok kurang, kontrak jadi sengketa, dan kerugiannya sulit dipulihkan.  
3. Payroll borongan berantakan saat jumlah operator naik-turun (1 sampai 70+): Pabrik tidak menggaji bulanan tetap, melainkan upah borongan (piece-rate). Rekonsiliasi manual tiap Sabtu memakan lebih dari 8 jam dan gampang salah hitung. Uang makan (10% sampai 15%) berubah-ubah, pembagian bonus QC 3 arah lambat, dan overhead bulanan pabrik tidak bisa dibebankan secara adil ke tiap potong pakaian.  
4. Jejak revisi prototipe hilang (R\&D spec drift): Sampel belum tercatat digital, jadi hasil time study, spesifikasi kain, dan rate card komponen tersebar di catatan kertas. Saat order masuk produksi massal, biaya dan target jahit meleset dari rencana.

Lukla Operations Engine adalah platform manajemen operasional pabrik berbasis event-driven. Platform ini menghubungkan seluruh alur kerja (Sampel → Order → Gudang → Cutting → Jahit → QC → Payroll) di atas double-entry ledger yang immutable (tidak bisa diubah). Sistem memisahkan kepemilikan material lewat aturan program, mencatat hasil kerja lantai produksi tiap 30 menit, dan menghitung biaya komersial serta gaji secara otomatis tanpa spreadsheet manual.

# **2\. DESKRIPSI PROYEK** 

* Proyek ini membangun sistem inti (core operating engine) untuk konveksi garmen skala menengah di Indonesia. Kerja sama maklon Lukla terbagi dalam tiga skema komersial, dan skema itulah yang menentukan siapa pemilik fisik dan hukum atas bahan baku:

* Skema CMT (Cut, Make, Trim): Klien B2B menyediakan seluruh bahan baku utama (kain) dan bahan pembantu/aksesoris. Lukla hanya menyumbang tenaga kerja dan mesin untuk cutting, perakitan jahit (sewing assembly), dan finishing. Bahan klien berstatus titipan kustodial, bukan aset neraca Lukla.  
* Skema Semi-CMT: Klien menyediakan bahan utama (kain luar/shell). Lukla mengadakan sisanya: bahan pembantu, furing, benang, kancing, dan resleting.  
* Skema CMT \+ Bahan (Full Package): Lukla mengadakan semua bahan baku, kain, dan aksesoris, lalu memproduksi dari awal sampai akhir. Skema ini juga dipakai untuk merek internal Snøhund.

Platform ini menggantikan catatan kertas dan spreadsheet dengan satu sistem terpadu. Aturan integritas data berlaku pada setiap pergerakan barang dan pengakuan biaya tenaga kerja di lantai pabrik.

# **3\. RUANG LINGKUP PROYEK** 

##   **3.1 Dalam Ruang Lingkup (In Scope)**

* Manajemen Multi-Tenant & Identitas Kepemilikan Material: Penandaan wajib pasangan client\_id dan order\_id pada setiap lot bahan baku, rol kain, bundel potongan, dan barang jadi.  
* Validasi Anti-Kontaminasi Silang: Pembatasan sistemik setingkat basis data (database-level trigger) yang menolak penerbitan material milik Klien X untuk pesanan Klien Y.  
* Manajemen Siklus Sampel & R\&D Time Study: Pelacakan versi prototipe (v1, v2, dan seterusnya), instrumen stopwatch digital pencatat waktu perakitan per komponen, penetapan konsumsi bahan, dan konversi spesifikasi master ke pesanan massal.  
* Pelacakan Output Lantai per 30 Menit: Terminal antarmuka ramah-sentuh bagi mandor untuk menginput jumlah hasil jahit per penjahit/komponen dalam interval 30 menit.  
* Manajemen Alokasi Kapasitas Dinamis: Penataan lini jahit fleksibel yang mampu menampung lonjakan operator dari 1 hingga 70+ penjahit tanpa batasan slot kaku.  
* Inspeksi Kontrol Kualitas (QC) & Taksonomi Cacat: Klasifikasi unit menjadi Pass, Repair, atau Reject/Scrap beserta pencatatan jenis cacat garmen (broken stitch, puckering, uneven seam).  
* Mesin Penggajian Borongan Mingguan:  
  ***Kalkulasi upah borongan penjahit: jumlah unit terverifikasi dikalikan rate komponen. Perhitungan pool uang makan mengambang mingguan sebesar 10% sampai 15% dari total ongkos jahit. Perhitungan bonus QC 3 arah yang dibagi rata untuk Mandor 1, Mandor 2, dan Kepala Operasional dari unit lolos QC. Alokasi biaya overhead operasional bulanan pabrik ke per unit pakaian jadi.***  
* Portal Eksternal Klien B2B: Akses mandiri bagi klien maklon untuk memantau status pesanan, milestone, dan saldo stok bahan titipan secara terisolasi.  
* Matriks Tata Kelola & Kontrol Akses (RBAC): Penegakan hak akses dan pembatasan operasional pada 8 peran pengguna.

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

Proses operasional baru mentransformasi pabrik menjadi ekosistem terintegrasi 6 fase dari penerimaan awal, pemotongan, lantai jahit, QC, hingga penggajian yang saling terhubung secara digital dan real-time. 

# 

# **7\. KEBUTUHAN FUNGSIONAL**

Skala Prioritas Kebutuhan

* 1 (Critical): Wajib ada pada peluncuran perdana. Kegagalan fungsi ini menyebabkan sistem tidak dapat beroperasi atau melanggar integritas finansial/kustodial.  
* 2 (High): Sangat penting untuk keberhasilan proyek, namun sistem masih dapat berjalan secara terbatas.  
* 3 (Medium): Memberikan nilai tambah efisiensi operasional.  
* 4 (Low): Fitur pendukung kenyamanan operasional.  
* 5 (Future): Di luar cakupan rilis saat ini.

## **Matriks Kategori Kebutuhan Fungsional**

## **Kategori RC1: Manajemen Multi-Tenant & Keamanan Akses**

* ID FR-1.1 (Prioritas: 1 \- Critical) oleh Owner & Legal. Sistem harus mengisolasi seluruh data operasional dan inventaris secara multi-tenant sehingga data Klien B2B tidak dapat diakses oleh klien lain.  
* ID FR-2.1 (Prioritas: 1 \- Critical) oleh Executive Management. Sistem harus menegakkan kontrol akses berbasis peran (RBAC) pada 8 peran pengguna dengan pembatasan mutlak antara pencatatan operasional dan penyesuaian finansial.  
* ID FR-3.1 (Prioritas: 1 \- Critical) oleh Finance & Auditor. Sistem harus mencatat seluruh riwayat revisi dan transaksi ke dalam audit trail yang bersifat append-only.

## **Kategori RC2: Siklus Sampel, Time Study & R\&D Garmen**

* ID FR-4.1 (Prioritas: 2 \- High) oleh Tim Sample / Adis. Sistem harus mengelola siklus versi sampel prototipe dengan menyimpan riwayat perubahan parameter jahitan dan spesifikasi kain.  
* ID FR-4.2 (Prioritas: 2 \- High) oleh Kepala Produksi. Sistem harus menyediakan instrumen pencatatan time study per komponen garmen.  
* ID FR-4.3 (Prioritas: 1 \- Critical) oleh Tim Sample & Owner. Sistem harus menghasilkan Master Spec Sheet terkunci saat sampel disetujui klien.

## **Kategori RC3: Manajemen Gudang, Bahan Kustodial & Cutting**

* ID FR-5.1 (Prioritas: 1 \- Critical) oleh Warehouse Manager. Mewajibkan input identitas pemilik (client\_id) dan alokasi pesanan (order\_id) saat penerimaan bahan baku kain.  
* ID FR-5.2 (Prioritas: 1 \- Critical) oleh Finance Officer. Pencatatan penerimaan bahan titipan tanpa membebankannya sebagai hutang dagang lancar perusahaan.  
* ID FR-6.1 (Prioritas: 2 \- High) oleh Warehouse Manager. Mengelola pencatatan stok opname secara real-time.  
* ID FR-6.2 (Prioritas: 1 \- Critical) oleh Executive. Anti-Cross Contamination Engine memblokir otomatis upaya penerbitan bahan baku ke lantai cutting jika pemilik bahan berbeda dengan pemesan kerja.  
* ID FR-6.3 (Prioritas: 2 \- High) oleh Kepala Produksi. Mencatat hasil pemotongan kain massal, rasio limbah kain, dan efisiensi konsumsi.

## **Kategori RC4: Eksekusi Lantai Produksi (Shop Floor MES)**

* ID FR-7.1 (Prioritas: 1 \- Critical) oleh Kepala Produksi. Mendukung pengaturan tata letak lini produksi dinamis dan alokasi fleksibel operator penjahit.  
* ID FR-7.2 (Prioritas: 1 \- Critical) oleh Owner. Mengelola rate card ongkos jahit per komponen artikel berdasarkan hasil time study.  
* ID FR-7.3 (Prioritas: 1 \- Critical) oleh Mandor. Menyediakan antarmuka terminal sentuh bagi mandor untuk menginput jumlah hasil jahit dalam blok interval 30 menit.  
* ID FR-7.4 (Prioritas: 1 \- Critical) oleh Mandor & Finance. Setiap unit komponen hasil jahit otomatis berstatus Menunggu QC dan mengikat hak upah bersyarat bagi operator.

## **Kategori RC5: Kontrol Kualitas (QC) & Penanganan Cacat**

* ID FR-8.1 (Prioritas: 1 \- Critical) oleh QC Inspector. Antarmuka terminal QC untuk mengklasifikasikan unit menjadi Pass, Repair, atau Reject.  
* ID FR-8.2 (Prioritas: 2 \- High) oleh QC Inspector. Mewajibkan pemilihan taksonomi jenis cacat saat unit ditandai Repair atau Reject.  
* ID FR-8.3 (Prioritas: 1 \- Critical) oleh Kepala Produksi. Mengarahkan kembali unit berstatus Repair ke antrean kerja penjahit tanpa menambah kredit upah borongan ganda.

## **Kategori RC6: Mesin Penggajian Fleksibel & Penetapan Biaya**

* ID FR-10.1 (Prioritas: 1 \- Critical) oleh Finance. Mengkalkulasi upah borongan mingguan penjahit secara otomatis setiap hari Sabtu.  
* ID FR-10.2 (Prioritas: 1 \- Critical) oleh Finance. Menghitung akumulasi pool uang makan mengambang mingguan (10% sampai 15%).  
* ID FR-10.3 (Prioritas: 1 \- Critical) oleh Executive. Mengumpulkan dana bonus QC dan membaginya sama rata menjadi 3 bagian untuk mandor dan kepala operasional dengan pembulatan ke bawah.  
* ID FR-10.4 (Prioritas: 2 \- High) oleh Finance. Merekapitulasi total biaya overhead bulanan dan menghitung alokasi beban overhead per unit garmen jadi.

# **8\. KEBUTUHAN NON-FUNGSIONAL**

* NFR-01 (Multi-Tenant Data Isolation): Pemisahan logis data antar-klien. Kueri data portal klien wajib memiliki predikat client\_id. Toleransi kebocoran data adalah 0%.  
* NFR-02 (Ledger Immutability): Setiap transaksi dicatat dengan prinsip append-only. Pembatalan transaksi melalui transaksi pembalik tanpa operasi UPDATE/DELETE pada tabel buku besar.  
* NFR-03 (Floor Terminal Response Time): Waktu respon antarmuka sentuh tidak boleh melebihi 500 milidetik.  
* NFR-04 (Concurrency): Basis data harus menangani penulisan data bersamaan dari minimal 10 lini jahit pada jendela waktu 30 menit tanpa deadlock.  
* NFR-05 (Offline Tolerance): Terminal produksi memiliki local cache sehingga mandor tetap dapat menginput saat WiFi pabrik gangguan sementara.  
* NFR-06 (Kompatibilitas Layar Sentuh): Antarmuka dirancang dengan tombol minimal 48x48 piksel.

# **9\. DAMPAK LAPORAN KEUANGAN & NERACA**

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

* Berwujud: Mencegah kerugian penggantian kain akibat salah potong (sekitar Rp 15 \- 40 juta per insiden).  
* Berwujud: Mereduksi waktu kerja staf Finance dari 8 jam menjadi kurang dari 15 menit per minggu.  
* Berwujud: Mencegah kebocoran penggelembungan hasil jahit (efisiensi 5% \- 8%).  
* Tak Berwujud: Transparansi data R\&D ke produksi massal dan peningkatan kepercayaan klien B2B.

# **11\. KEBUTUHAN SUMBER DAYA**

## **11.1 Personel Proyek**

* Internal Executive: Penentu kebijakan dan rate card.  
* Kepala Pabrik: Pemilik proses bisnis lapangan.  
* Lead System Architect: Penanggung jawab integritas database.  
* Tim Sample: Penguji modul time study.  
* Mandor & Penjahit: Pengguna uji coba terminal sentuh.

## **11.2 Infrastruktur Pabrik**

* Tablet sentuh 10 inci berpelindung debu, Jaringan LAN/WiFi terdistribusi di area pabrik, 2 PC desktop untuk Finance/Admin.

# **12\. JADWAL, TONGGAK PENCAPAIAN & TENGGAT WAKTU**

## **Sprint 1: Double-Entry Core & RBAC Engine (13 \- 26 Okt 2026\)** 

## **Sprint 2: Multi-Tenant Inventory & Guardrail (27 Okt \- 09 Nov 2026\)** 

## **Sprint 3: Sample Lifecycle, Order & MES Floor (10 \- 23 Nov 2026\)** 

## **Sprint 4: Payroll Borongan & QC Bonus Engine (24 Nov \- 07 Des 2026\)** 

## **Sprint 5: UI Suite & Validasi End-to-End (08 \- 21 Des 2026\)**

## **Tonggak Pencapaian Kritis (Major Milestones)**

* Milestone 1 (26 Okt): Fondasi basis data double-entry dan RBAC 8 peran teruji.  
* Milestone 2 (09 Nov): Pengujian Skenario Pencegahan Kontaminasi Silang lulus validasi.  
* Milestone 3 (23 Nov): Transisi spesifikasi sampel ke pesanan massal berhasil.  
* Milestone 4 (07 Des): Eksekusi formula payroll hari Sabtu terverifikasi presisi.  
* Milestone 5 (21 Des): Uji coba menyeluruh 6 antarmuka; sistem siap Go-Live.

# **13\. ASUMSI & BATASAN BISNIS** 

## **13.1 Asumsi Operasional**

* Skala kapasitas adalah sekitar 70 mesin jahit.  
* Mandor memiliki disiplin melakukan input verifikasi setiap 30 menit.  
* Persentase uang makan (10% \- 15%) ditentukan manual oleh Finance.  
* Bonus QC dibagi rata untuk 3 pimpinan lapangan (2 Mandor Lini, 1 Kepala Ops).

## **13.2 Batasan Sistemik**

* Catatan transaksi buku besar yang sudah dikunci bersifat absolut, tidak dapat diubah oleh siapapun.  
* Penerbitan surat perintah potong wajib merujuk pada lot bahan yang terverifikasi di gudang.  
* Pembagian nilai uang rupiah pada bonus QC dibulatkan ke bawah, sisa masuk ke cadangan operasional.

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
3. Pembagian Bonus Kontrol Kualitas: Total Dana QC \= Total Pakaian Lolos QC dikalikan Tarif Bonus Per Pakaian. Bonus Mandor \= Total Dana QC dibagi 3 (dibulatkan ke bawah).  
4. Alokasi Biaya Overhead Pabrik per Unit Pakaian: Overhead per Unit \= Total Biaya Operasional Pabrik Bulanan dibagi Total Unit Pakaian Jadi yang Diproduksi Bulan Tersebut.

## **16.2 Logika Basis Data Anti-Kontaminasi Silang Integritas segregasi ditegakkan pada tingkat transaksi.** 

Sistem akan mengambil ID Klien pemilik pesanan target dan ID Klien pemilik bahan yang dikeluarkan. Jika keduanya tidak sama, sistem secara otomatis menolak transaksi dengan pesan peringatan: CRITICAL VIOLATION \- Upaya pengeluaran bahan milik Klien A untuk pesanan Klien B DITOLAK.

## **16.3 Spesifikasi Minimum Required UI Views**

* VIEW 01: Executive Operations Dashboard (Menampilkan grafik output 30 menit dan matriks progres order).  
* VIEW 02: Sample & Time Study Tracker (Menampilkan instrumen stopwatch untuk merekam waktu penjahitan komponen).  
* VIEW 03: Multi-Client Warehouse Inventory Grid (Tabel stok dengan peringatan pop-up jika terjadi tabrakan pemilik bahan).  
* VIEW 04: Floor Terminal (Antarmuka tombol besar sentuh untuk input hasil jahit tiap penjahit pada blok interval 30 menit).  
* VIEW 05: QC Inspection Terminal (Menu pemindaian nomor serial dengan tombol Pass, Repair, atau Reject).  
* VIEW 06: Payroll & Costing Workspace (Layar rekap total borongan murni, alokasi uang makan, dan penentuan overhead akhir minggu).

## **16.4 Empat Skenario Pengujian Penerimaan Bisnis (Acceptance Test Scenarios)**

1. Skenario Pencegahan Kontaminasi: Sistem menggagalkan transaksi jika bahan Klien A akan dipotong untuk pesanan Klien B.  
2. Penambahan Tenaga Dinamis: Mandor mendaftarkan penjahit baru di hari Kamis, sistem tetap dapat merekap gaji mereka pada hari Sabtu beserta persentase uang makan tanpa me-restart siklus.  
3. Pembagian Bonus Rata: 3.000 unit lolos QC dikali tarif bonus, kemudian dana dibagi habis ke 3 pimpinan lapangan dengan pembulatan pecahan ke bawah.  
4. Transisi Revisi Sampel: Sistem mengubah sampel disetujui (v2) menjadi pesanan massal dengan mewarisi secara otomatis spesifikasi dan rate card sebelumnya.

	

