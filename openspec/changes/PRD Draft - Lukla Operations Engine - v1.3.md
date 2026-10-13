> **STATUS: SUPERSEDED** — Dokumen ini digantikan oleh "PRD - Lukla Operations Engine - v2.0 - Wagile.md". Disimpan untuk riwayat.

# **LAPORAN KOMPREHENSIF PROYEK: LUKLA OPERATIONS ENGINE**

***Platform: Web App (Responsive Desktop & Tablet PWA) | Sistem Desain: Apple Human Interface Guidelines (HIG) Inspire kelompok 12***

## **1\. RINGKASAN EKSEKUTIF & BUSINESS BRIEF**

Lukla Manufacturing beroperasi dengan model produksi hibrida, yaitu menangani merek internal (Snøhund) sekaligus melayani maklon B2B eksternal (skema CMT, Semi-CMT, dan Full Package). Saat ini, operasional pabrik menghadapi tiga kendala utama yang menghambat skala bisnis:

* Kontaminasi silang material antar-klien di gudang.  
* Inefisiensi dan kekacauan perhitungan upah borongan mingguan untuk 1 hingga 70+ penjahit yang berfluktuasi, termasuk perhitungan uang makan dan pembagian bonus QC yang dilakukan manual via spreadsheet.  
* Hilangnya rekam jejak revisi sampel (R\&D drift) dari tahap prototipe ke produksi massal.

Produk Lukla Operations Engine dibangun untuk mendigitalisasi dan mengotomatisasi seluruh siklus ini melalui sistem *event-driven* yang berbasis *double-entry ledger* yang ketat dan tidak dapat diubah (immutable)

## 

## **2\. KEBUTUHAN PRODUK (PRD) & BATASAN SISTEM**

Tujuan utama sistem ini adalah:

* Memastikan segregasi inventaris 100% aman (tidak ada bahan Klien A yang dipotong untuk pesanan Klien B).  
* Mengotomatisasi sistem payroll upah borongan mingguan.  
* Menciptakan rekam jejak operasional terpusat dari sampel hingga inspeksi akhir (QC).

### 

### 

### **2.1USER STORIES**

* Sebagai Warehouse Manager, saya ingin sistem memblokir pengeluaran kain jika ID Klien bahan tidak cocok dengan ID pesanan, agar saya terhindar dari kerugian akibat salah potong material.  
* Sebagai Mandor Lini (Foreperson), saya ingin layar sentuh untuk memasukkan jumlah jahitan (tally) masing-masing penjahit setiap 30 menit, agar saya tidak perlu mencatat manual di kertas yang mudah hilang.  
* Sebagai Tim Finance, saya ingin sistem otomatis menghitung upah borongan, uang makan (10-15%), dan pembagian bonus QC setiap hari Sabtu, agar saya tidak perlu menghabiskan 8 jam lembur merangkai rumus Excel.  
* Sebagai Klien Maklon B2B, saya ingin memiliki portal untuk melihat status pesanan dan saldo kain titipan secara mandiri, agar saya memiliki visibilitas dan merasa aman mempercayakan produksi ke Lukla.

### 

### **Enam Antarmuka (UI Views) Utama**

1. Executive Operations Dashboard (View 01): Pantauan lini aktif dan grafik output 30 menit.  
2. Sample & Time Study Tracker (View 02): Perekaman versi spesifikasi produk dan stopwatch digital.  
3. Multi-Client Warehouse Grid (View 03): Tabel inventaris dengan pemblokiran otomatis (anti-cross contamination).  
4. Floor Terminal (View 04): Antarmuka tablet sentuh bagi mandor untuk input tally jahitan per 30 menit.  
5. QC Inspection Terminal (View 05): Pemindai status akhir garmen (Pass, Repair, Reject) dan taksonomi cacat.  
6. Payroll & Costing Workspace (View 06): Kalkulasi otomatis upah borongan, uang makan, pembagian bonus QC 3-arah, dan biaya overhead.

### **Batasan Sistem Utama (Strict Constraints)**

* ***Immutable Ledger:** Transaksi tidak bisa di-UPDATE/DELETE. Harus melalui transaksi pembalik.*  
* ***Anti-Contamination Guardrail:** Sistem basis data wajib menolak (abort) pemotongan bahan jika client\_id bahan tidak sama dengan pesanan*.

## 

## 

## **3\. DESIGN GUIDELINES & TECHNICAL SPECIFICATIONS**

### **3.1 Design Guidelines (Apple Design Language)**

Antarmuka menargetkan penggunaan pada tablet industri di lantai pabrik. Mengadopsi prinsip Apple Human Interface Guidelines (HIG):

* **Tipografi:** Font San Francisco Pro (SF Pro). Kontras tinggi untuk angka metrik.  
* **Material:** Glassmorphism (blur/acrylic) ringan pada header/navbar dan modal popup.  
* **Warna (Apple Semantic):** Success (\#340759), Warning (\#FF9500), Danger (\#FF3B30), Action (\#007AFF).  
* **Komponen & Interaksi:** Touch-first dengan tombol minimal berukuran 48×48 piksel agar mudah ditekan mandor, sudut membulat (12px 16px), dan drop shadow halus.

### 

### **3.2 Struktur Frontend & Backend (React / [Next.js](http://Next.js))**

![%%{init: {'themeVariables': { 'fontSize': '11px' }}}%%graph TD    subgraph Frontend \[Frontend - Next.js\]        src1\["📁 /src"\] --\> app\["📁 /app (Router)"\]        app --\> dash\["/dashboard"\] & sample\["/sample-tracker"\] & wh\["/warehouse"\]        app --\> floor\["/floor"\] & qc\["/qc"\] & pay\["/payroll"\]        src1 --\> comp\["📁 /components"\] & hooks\["📁 /hooks"\]        src1 --\> lib\["📁 /lib"\] & store\["📁 /store"\]    end    subgraph Backend \[Backend - Supabase\]        supa\["📁 /supabase"\] --\> mig\["📁 /migrations"\]        supa --\> func\["📁 /functions"\]        mig --\> rbac\["01\_rbac.sql"\] & led\["02\_ledger.sql"\]        mig --\> inv\["03\_inventory.sql"\] & rls\["04\_rls.sql"\]        mig --\> guard\["05\_trigger.sql"\]    end][image1]

## 

## 

## 

## 

### **3.3 REQUIREMENT MATRIX**  

**Skala Prioritas:** 1 (Critical) | 2 (High) | 3 (Medium) | 4 (Low)

| Req ID | Kategori | Deskripsi Kebutuhan Fungsional | Priority |
| :---- | :---- | :---- | :---- |
| **FR-1.1** | Security | Isolasi data multi-tenant ketat berpredikat client\_id pada seluruh kueri. | 1 |
| **FR-2.1** | Access | Kontrol akses berbasis peran (RBAC) pada 8 peran pengguna dengan batas operasional ketat. | 1 |
| **FR-3.1** | Ledger | Audit trail transaksi bersifat append-only tanpa izin UPDATE/DELETE (Double-Entry). | 1 |
| **FR-4.3** | R\&D | Penguncian Master Spec Sheet & Rate Card saat sampel disetujui untuk diwariskan ke produksi massal. | 1 |
| **FR-6.2** | Warehouse | Anti-Cross Contamination Engine di level DB untuk memblokir pengeluaran bahan antar klien. | 1 |
| **FR-7.3** | Floor MES | Terminal sentuh input hasil jahit interval 30 menit oleh Mandor. | 1 |
| **FR-8.1** | QC | Terminal pemindai QC untuk klasifikasi unit Pass, Repair, atau Reject. | 1 |
| **FR-10.1** | Payroll | Mesin otomatis kalkulasi upah borongan mingguan, uang makan, dan bonus QC (Split 3 arah). | 1 |
| **FR-10.4** | Costing | Alokasi biaya overhead bulanan per unit pakaian jadi (COGS). | 2 |

## 

## **4\. INSTRUKSI PENGEMBANGAN & PEMBAGIAN TUGAS (TASK ASSIGNMENT)**

Berikut adalah pembagian tugas berdasarkan kesepakatan sprint (Berdasarkan acuan target Deliverables Kamis). Mohon setiap Dev berfokus pada Scope masing-masing agar integrasi berjalan lancar.

| Anggota Tim | Fokus Area & Tanggung Jawab (WIP) | Target Deliverables (Kamis) |
| :---- | :---- | :---- |
| **Dev 1 (Frontend & UI/UX)** | Membangun Dashboard Admin, Grid Gudang, dan antarmuka analitik Workspace Payroll. | UI View 1, 3, dan 6 selesai. Integrasi tabel dengan Supabase API untuk baca data stok. |
| **Dev 2 (Frontend "Floor")** | Fokus eksklusif pada Terminal Input 30 Menit, Terminal QC, dan Form Time Study. | UI View 2, 4, dan 5 selesai. Antarmuka touch-friendly berjalan lancar di layar tablet. (Pastikan target sentuh min. 48px). |
| **Dev 3 (Backend & DB Architect)** | Merancang Skema Tabel, Menerapkan Row Level Security (RLS), mengatur RBAC 8 peran. | Supabase siap pakai. Skenario Pengujian 1 (Blokir Kontaminasi) berfungsi di level DB (Trigger berjalan). |
| **Dev 4 (Logic, QA & DevOps)** | Merangkai algoritma Mesin Payroll (gaji, uang makan, overhead), testing skenario, deployment. | Algoritma Skenario 2 & 3 (Payroll & Bonus QC) lolos uji. Vercel & CI/CD beroperasi. |

## **5\. UI ( pages\&screen )**

**Executive Operations Dashboard:** Pantauan status 70+ lini aktif dan grafik kecepatan output per 30 menit.  
**Sample & Time Study Tracker:** Perekaman versi prototipe (v1, v2) dan instrumen stopwatch digital.  
**Multi-Client Warehouse Grid:** Tabel inventaris bahan baku dengan blocking popup jika terdeteksi tabrakan kepemilikan bahan.  
**Floor Terminal:** Antarmuka layar sentuh ramah tablet (tombol min. 48px) untuk input tally jahitan penjahit per interval waktu.  
**QC Inspection Terminal:** Layar inspeksi untuk menetapkan status akhir barang dan mencatat jenis cacat (taksonomi cacat).  
**Payroll & Costing Workspace:** Dasbor rekonsiliasi keuangan hari Sabtu untuk mencairkan payroll otomatis.

### **5.1 ON-FUNCTIONAL REQUIREMENTS & OUT OF SCOPE** 

**Non-Functional Requirements:**

* **Response Time:** Waktu respon antarmuka sentuh di Floor Terminal tidak boleh \>500ms.  
* **Concurrency:** Database harus tahan penulisan serentak dari minimal 10 lini jahit pada jendela penutupan interval tanpa deadlock.  
* **Offline Tolerance:** Cache lokal agar mandor tetap bisa menginput data saat WiFi pabrik putus sesaat.

**Out of Scope (Tidak Masuk Rilis Ini):**

* Perhitungan BPJS, PPh 21, lembur, dan pesangon (hanya fokus upah borongan).  
* Pelaporan pajak korporasi atau depresiasi mesin.  
* Pelacakan truk pengiriman (integrasi logistik).  
* Pembelian material otomatis ke supplier (Sistem MRP).

## 

## **6\. TIMELINE & MILESTONES**

* ***Sprint 1:*** Immutable Double-Entry Core & Skema RBAC.  
* ***Sprint 2:*** Multi-Tenant Inventory & Guardrail Anti-Kontaminasi.  
* ***Sprint 3:*** Siklus R\&D Sampel & Floor Terminal 30 Menit.  
* ***Sprint 4:*** Mesin Eksekusi Payroll & Kalkulasi Bonus QC.  
* ***Sprint 5:*** UI Suite, End-to-End Validation, & Persiapan Go-Live.

#### **Catatan Penting untuk Eksekusi**

1. **Frontend (Dev 1 & Dev 2):** Jangan lupa terapkan desain ala Apple. Gunakan sudut membulat, pastikan kontras jelas, dan optimalkan efek glassmorphism tanpa mengorbankan performa (jangan sampai lag di tablet pabrik).  
2. **Backend (Dev 3):** Integritas data adalah harga mati. Pastikan Trigger validate\_material\_dispatch() yang memblokir kontaminasi silang tidak bisa di-bypass oleh siapapun.  
3. **Logic (Dev 4):** Perhatikan pembulatan nilai pecahan saat membagi bonus QC 3 arah. Sisa pembulatan (walau Rp 1\) harus masuk ke cadangan pabrik, bukan mematahkan aplikasi.

	

[image1]: <data:image/png;base64,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> "mermaid-graph/default"