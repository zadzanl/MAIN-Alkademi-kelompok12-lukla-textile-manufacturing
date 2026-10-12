# **Business Brief: Lukla Operations Engine**

**Lukla Operations Engine** adalah platform manajemen manufaktur berbasis *event-driven* yang dirancang untuk fasilitas produksi pakaian Lukla Manufacturing di Ciwidey, Jawa Barat. Fasilitas ini beroperasi dengan model *hybrid*, menangani produksi merek internal (Snøhund) sekaligus melayani maklon B2B eksternal dengan skema CMT (Cut, Make, Trim), Semi-CMT, dan Full Package.

Sistem ini dibangun untuk menyelesaikan tiga krisis operasional utama: **kontaminasi silang material antar-klien, inefisiensi perhitungan upah borongan (dengan fluktuasi 1-70+ pekerja), dan hilangnya rekam jejak revisi sampel (*R\&D drift*).**

Sebagai solusi, Lukla Operations Engine menerapkan arsitektur double-entry accounting yang immutable. Setiap pergerakan fisik (penerimaan bahan, transisi lini per 30 menit, QC, hingga perhitungan upah) dicatat sebagai transaksi finansial yang saling terikat. Hal ini menjamin segregasi inventaris multi-tenant secara absolut, visibilitas operasional yang presisi, dan eksekusi *payroll* mingguan yang sepenuhnya terotomatisasi.

# **Business Requirements Document (BRD)**

## **1\. Konteks Bisnis & Model Operasional**

Lukla Manufacturing mengelola kapasitas dinamis hingga 70 mesin jahit aktif. Model bisnis maklon dibagi menjadi tiga skema komersial yang menentukan kepemilikan dan pengadaan bahan baku:

* **CMT (Cut, Make, Trim):** 100% bahan baku dan aksesoris disediakan oleh klien B2B. Lukla hanya menyediakan jasa potong, jahit, dan *finishing*.  
* **Semi-CMT:** Klien menyediakan kain utama, Lukla melakukan *sourcing* komponen sekunder (furing, benang, perangkat keras).  
* **CMT \+ Bahan (Full Package):** Lukla melakukan *sourcing* seluruh bahan baku dan aksesoris, sekaligus mengeksekusi produksi dari awal hingga akhir (standar untuk merek internal Snøhund).

## **2\. Tantangan Bisnis Utama**

* **Kontaminasi Silang Inventaris Multi-Tenant:** Bahan baku, barang setengah jadi (WIP), dan produk jadi dari berbagai klien disimpan secara bersamaan tanpa batasan sistem. Risiko operator menggunakan bahan Klien A untuk pesanan Klien B sering memicu kekurangan inventaris, kerugian material, dan sengketa kontrak.  
* **Kompleksitas *Payroll* Pekerja Borongan:** Tidak ada sistem gaji bulanan tetap; jumlah operator berfluktuasi. Pabrik membutuhkan sistem otomatis untuk mencatat *output* borongan per 30 menit, mencairkan upah mingguan (Sabtu), menerapkan uang makan mengambang (10-15%), membagi bonus QC untuk *leadership*, dan mengalokasikan *overhead* pabrik ke setiap unit yang diproduksi.  
* **Hilangnya Rekam Jejak R\&D:** Prototyping fisik saat ini tidak memiliki pelacakan digital terpusat. Parameter teknis (kebutuhan kain, waktu pengerjaan, *rate card*, *defect log*) tersebar di catatan kertas, menyebabkan anomali saat transisi dari sampel ke produksi massal.

## **3\. Objektif Strategis**

* **Segregasi Mutlak Inventaris Multi-Tenant:** Mengeliminasi kesalahan fisik secara terprogram melalui *mandatory owner-tagging* pada semua bahan baku, WIP, dan SKU jadi.  
* **Pelacakan Operasional yang *Immutable*:** Melacak *output* per komponen setiap 30 menit di lini jahit untuk memastikan perhitungan produksi, pengurangan inventaris, dan pencairan *payroll* berasal dari data yang terverifikasi.  
* **Penyelesaian Komersial Multi-Tier Otomatis:** Mendukung *invoicing* otomatis dan *payroll* mingguan untuk seluruh skema produksi tanpa rekonsiliasi *spreadsheet* manual.

## **4\. Matriks Stakeholder & Tata Kelola (RBAC)**

| Peran | Cakupan Operasional | Batasan Sistem (Constraints) |
| :---- | :---- | :---- |
| **Owner / Executive** | Akses BI *analytics*, konfigurasi sistem, dan penyesuaian *rate-card* dinamis. | Tidak dapat mengubah catatan *ledger* finansial/inventaris historis yang sudah dikunci. |
| **Sample Team** | Mencatat konsumsi sampel, *time studies*, dan menyetujui iterasi versi sampel. | Tidak dapat mengubah sampel ke pesanan produksi massal tanpa persetujuan *Executive*. |
| **Warehouse Manager** | Menerima material, memproses stok titipan, melakukan *stock opname*. | Diblokir otomatis jika menerbitkan material dengan Client ID atau Order ID yang tidak valid. |
| **Production Head** | Mengalokasikan operator ke lini, mengatur *rate card*, mencatat *output* per 30 menit. | Dilarang memodifikasi rumus *payroll* atau mengubah status akhir QC. |
| **Tailor / Operator** | Melihat antrean perakitan komponen, menginput *tally* penyelesaian. | Akses *read-only* pada catatan yang sudah diverifikasi *Foreperson*. |
| **QC Inspector** | Menginspeksi produk jadi, mencatat *defect*, mengategorikan status (Pass, Repair, Reject). | Dilarang memodifikasi syarat komersial pesanan atau upah borongan. |
| **Finance & Payroll** | Menyetujui PO, menerbitkan *invoice*, menghitung upah mingguan dan *overhead*. | Dilarang keras menyesuaikan saldo stok inventaris fisik secara manual. |
| **Maklon Client** | Melacak progres pesanan dan saldo stok bahan baku titipan (via *External Portal*). | Terisolasi oleh aturan multi-tenant; hanya dapat melihat data yang cocok dengan client\_id mereka. |

# **Product Requirements Document (PRD)**

## **1\. Dekonstruksi Arsitektur & Domain**

Sistem ini menggunakan basis data relasional untuk menjaga integritas transaksi manufaktur dengan pendekatan *Double-Entry Ledger*. Setiap pergerakan material dan transisi perakitan diberlakukan sebagai transaksi finansial atomik.

* **Skema Consigned Inventory (CMT):** Bahan baku klien dicatat sebagai liabilitas kustodial, bukan aset Lukla.  
* **Skema Owned Inventory (Full Package/Snøhund):** Bahan baku dibeli dan dicatat sebagai aset.  
* **Kapitalisasi Tenaga Kerja:** Saat *output* borongan diverifikasi, biaya tenaga kerja langsung dikapitalisasi ke dalam nilai inventaris (WIP).  
* **Pencegahan Kontaminasi (FR-6.2):** *Database trigger* memvalidasi identitas stok berdasarkan SKU, Owner ID, dan Assigned Order ID.

## **2\. Spesifikasi Komputasi Sistem**

* **Upah Borongan Mingguan Tailor:** Dihitung setiap hari Sabtu. (\$\\text{Output 30 menit terverifikasi} \\times \\text{Rate per komponen}\$).  
* **Uang Makan Mengambang:** Persentase \$10\\text{--}15%\$ dari total upah, dikonfigurasi oleh divisi Finance.  
* **Bonus QC (Three-Way Split):** Didistribusikan merata kepada Foreperson 1, Foreperson 2, dan Head Ops dari total unit yang lolos QC dibagi 3\.  
* **Alokasi Overhead Pabrik per Unit:** Dihitung bulanan untuk penentuan Harga Pokok Penjualan (COGS).

## **3\. Kebutuhan Antarmuka Pengguna (UI)**

* **Executive Operations Dashboard:** Pemantauan status lini aktif, metrik kecepatan interval 30 menit.  
* **Sample & Time Study Tracker:** Manajemen versi spesifikasi (v1, v2) dan instrumen *stopwatch* digital.  
* **Multi-Client Warehouse Grid:** Manajemen stok titipan dan *dispatch* dengan mekanisme *blocking modal*.  
* **Floor Terminal:** Antarmuka pencatatan jumlah jahitan yang diselesaikan masing-masing penjahit per interval waktu.  
* **QC Inspection Terminal:** Antarmuka pemindaian status final (*Pass, Repair, Reject*).  
* **Payroll & Costing Workspace:** Dasbor rekonsiliasi keuangan akhir pekan.

## **4\. Rencana Eksekusi (Agile Sprints)**

* **Sprint 1:** Double-Entry Core & RBAC Engine.  
* **Sprint 2:** Multi-Tenant Inventory Engine.  
* **Sprint 3:** Manufacturing Execution (MES).  
* **Sprint 4:** Dynamic Payroll & QC Bonus Engine.  
* **Sprint 5:** Full UI & End-to-End Validation.

