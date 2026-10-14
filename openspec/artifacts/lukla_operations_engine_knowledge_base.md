# Knowledge Base --- Lukla Operations Engine

Sumber: Business Requirements Document (BRD) Lukla Operations Engine
v2.2.1. Status sumber: Draft --- Menunggu
Persetujuan. Klasifikasi sumber: Internal Confidential / Restricted
Enterprise Blueprint.

## 1. Ringkasan Sistem

Lukla Operations Engine adalah platform manajemen operasional untuk
fasilitas konveksi Lukla Manufacturing di Ciwidey, Kabupaten Bandung,
Jawa Barat. Kapasitas fleksibel pabrik sekitar 70 mesin jahit aktif.
Bisnis menggabungkan produksi merek internal Snøhund dan jasa maklon
untuk klien fashion eksternal B2B.

Platform menghubungkan proses Sampel, Order, Gudang, Cutting, Jahit, QC,
Payroll, dan perhitungan biaya. Sistem dirancang berbasis event-driven
dan menggunakan pencatatan double-entry ledger yang bersifat
append-only/immutable untuk menjaga integritas serta jejak audit
transaksi.

## 2. Masalah Bisnis yang Ditangani

1.  Kontaminasi silang bahan: bahan milik Klien A berisiko digunakan
    untuk pesanan Klien B.
2.  Penggajian borongan manual: rekap mingguan untuk operator yang
    jumlahnya dapat berubah dari 1 hingga 70+ orang rawan salah hitung
    dan menghabiskan lebih dari 8 jam.
3.  Jejak revisi sampel tidak terpusat: spesifikasi kain, hasil time
    study, dan rate card tersebar di catatan kertas sehingga estimasi
    biaya dan target produksi dapat meleset.
4.  Visibilitas produksi terbatas: catatan manual menyulitkan
    identifikasi hambatan produksi secara cepat.
5.  Pelacakan cacat terbatas: catatan QC manual tidak selalu menautkan
    cacat ke komponen atau penjahit terkait.

## 3. Model Bisnis Maklon

### CMT (Cut, Make, Trim)

Klien menyediakan seluruh bahan baku utama dan bahan pembantu/aksesori.
Lukla menyediakan tenaga kerja dan mesin untuk cutting, perakitan jahit,
serta finishing. Bahan tersebut merupakan bahan titipan/kustodial klien,
bukan aset persediaan milik Lukla.

### Semi-CMT

Klien menyediakan bahan utama seperti kain luar/shell. Lukla menyediakan
bahan tambahan seperti furing, benang, kancing, resleting, dan aksesori
lainnya.

### CMT + Bahan / Full Package

Lukla menyediakan semua bahan baku dan aksesori serta jasa produksi.
Skema ini juga digunakan untuk pesanan merek internal Snøhund.

## 4. Alur Operasional Target (To-Be)

1.  **Gudang dan segregasi multi-tenant:** setiap lot bahan wajib
    memiliki `client_id` dan `order_id`. Sistem membedakan bahan titipan
    klien dan persediaan milik Lukla.
2.  **Sampel, R&D, dan time study:** tim membuat versi prototipe,
    merekam waktu pengerjaan tiap komponen, mencatat konsumsi bahan, dan
    menyiapkan Master Spec Sheet serta Rate Card.
3.  **Cutting:** sebelum bahan dipotong, sistem memeriksa kecocokan
    pemilik bahan dengan klien pada Work Order. Jika cocok, surat
    perintah potong diterbitkan dan bundel potongan diberi barcode.
4.  **Produksi jahit:** mandor memasukkan output per penjahit dan
    komponen pada interval 30 menit. Output tercatat dengan status
    "Menunggu QC".
5.  **Quality Control (QC):** setiap unit diklasifikasikan sebagai Pass,
    Repair, atau Reject.
6.  **Payroll dan costing:** setiap Sabtu sistem merekap upah borongan
    untuk unit yang memenuhi syarat, menghitung uang makan dan bonus QC,
    serta mengalokasikan overhead bulanan per unit.

## 5. Proteksi Material dan Data Multi-Tenant

-   Setiap lot bahan, rol kain, bundel potongan, dan barang jadi perlu
    ditautkan dengan identitas klien dan pesanan.
-   Sistem harus menolak pengeluaran bahan milik satu klien untuk Work
    Order klien lain.
-   Validasi anti-kontaminasi silang diterapkan pada tingkat database
    melalui guardrail/trigger.
-   Data klien B2B harus terisolasi; klien hanya boleh melihat data
    pesanan dan stok miliknya sendiri.
-   Toleransi kebocoran data antar-klien adalah 0%.
-   Jika pemilik bahan dan pemilik pesanan berbeda, sistem harus menolak
    transaksi dan mencatat insiden keamanan.
-   Contoh: roll kain R-101 milik KLIEN-A tidak boleh digunakan pada
    order ORD-B milik KLIEN-B.

## 6. Sampel, Master Spec, Time Study, dan Rate Card

-   Sistem menyimpan versi prototipe, misalnya v1, v2, dan seterusnya,
    termasuk riwayat perubahan spesifikasi kain dan parameter jahitan.
-   Time study merekam waktu pengerjaan per komponen garmen.
-   Konsumsi bahan dan rate card ditentukan berdasarkan spesifikasi
    serta hasil time study.
-   Setelah sampel disetujui klien, Master Spec Sheet dan Rate Card
    dikunci.
-   Pesanan massal harus mewarisi spesifikasi dan rate card dari versi
    sampel yang telah disetujui.
-   Tujuannya mengurangi perbedaan antara spesifikasi sampel, biaya, dan
    target produksi massal.

## 7. Produksi dan Pelacakan Output

-   Kapasitas yang ditargetkan sekitar 70 mesin jahit aktif, dengan
    alokasi operator yang fleksibel dari 1 hingga 70+ penjahit.
-   Mandor memasukkan jumlah hasil jahit per penjahit/komponen pada
    interval 30 menit.
-   Sistem menampilkan output dan progres pesanan agar hambatan produksi
    dapat diketahui lebih cepat.
-   Output jahit awalnya berstatus "Menunggu QC".
-   Rate Card menetapkan tarif upah per komponen artikel.
-   Antarmuka terminal produksi dirancang untuk layar sentuh, dengan
    tombol minimal 48 x 48 piksel.
-   Waktu respons antarmuka terminal ditargetkan tidak lebih dari 500
    milidetik.
-   Sistem perlu mendukung input bersamaan dari minimal 10 lini jahit
    dalam jendela 30 menit tanpa deadlock.
-   Terminal memiliki local cache agar input dapat berlanjut saat Wi-Fi
    terganggu sementara.

## 8. Quality Control (QC)

Status unit: - **Pass:** lolos QC, siap dikemas, dan memenuhi syarat
untuk perhitungan upah sesuai aturan sistem. - **Repair:** perlu
diperbaiki dan dikembalikan ke antrean kerja penjahit. Penyelesaian
ulang tidak boleh menghasilkan kredit upah borongan ganda. - **Reject:**
ditolak dan dapat dikategorikan sebagai scrap sesuai aturan operasional.

Jenis cacat yang disebutkan dalam BRD meliputi: - `broken stitch` ---
jahitan putus/rusak. - `puckering` --- kain atau jahitan berkerut. -
`uneven seam` --- sambungan/jahitan tidak rata.

Jika unit ditandai Repair atau Reject, QC harus memilih kategori cacat.
Sistem harus mempertahankan keterlacakan unit dan tidak memberi upah
ganda untuk unit yang diperbaiki.

## 9. Formula Payroll dan Costing

### Upah borongan mingguan

Upah penjahit dihitung setiap Sabtu: **Upah penjahit = jumlah unit
terverifikasi yang memenuhi syarat × tarif upah komponen.** Rate Card
menjadi sumber tarif per komponen. Status QC menentukan kelayakan unit
sesuai aturan BRD.

### Pool uang makan

**Total uang makan = persentase uang makan × total upah seluruh
penjahit.** Persentase ditetapkan manual oleh Finance pada rentang
10%--15% untuk periode terkait.

### Bonus QC tiga arah

**Total dana bonus QC = jumlah pakaian lolos QC × tarif bonus per
pakaian.** Dana dibagi rata untuk tiga pimpinan lapangan: Mandor 1,
Mandor 2, dan Kepala Operasional. Pembagian menggunakan pembulatan ke
bawah; sisa rupiah dialokasikan ke cadangan operasional.

Contoh BRD: jika total dana bonus Rp100.000, masing-masing menerima
Rp33.333 dan sisa Rp1 masuk cadangan operasional. BRD juga menyebut
skenario pengujian 3.000 unit lolos QC dikalikan tarif bonus.

### Overhead pabrik per unit

**Overhead per unit = total biaya operasional pabrik bulanan ÷ total
unit pakaian jadi yang diproduksi pada bulan tersebut.** Overhead
mencakup biaya operasional pabrik seperti listrik, air, internet, dan
operasional pabrik.

## 10. Perlakuan Akuntansi yang Dijelaskan BRD

-   **CMT / bahan titipan:** bahan dicatat sebagai persediaan
    kustodial/titipan di luar aset lancar perusahaan, dengan pencatatan
    kustodial yang sesuai.
-   **Full Package / bahan milik Lukla:** pembelian bahan dicatat
    sebagai persediaan bahan baku milik perusahaan dan berpasangan
    dengan hutang usaha atau kas.
-   **Barang dalam proses (WIP):** biaya tenaga kerja langsung
    dikapitalisasi ke persediaan WIP sesuai mekanisme pencatatan setiap
    interval 30 menit.
-   Sistem ini bukan sistem akuntansi finansial lengkap. Pajak
    korporasi, depresiasi gedung/mesin, rekonsiliasi bank
    multi-rekening, PPh 21, BPJS, lembur formal, dan pesangon formal
    dinyatakan di luar ruang lingkup.

## 11. Peran Pengguna dan Kontrol Akses (RBAC)

BRD menyatakan sistem menerapkan RBAC untuk 8 peran: 1.
**Owner/Executive:** melihat analitik dan konfigurasi serta menetapkan
kebijakan/rate card; transaksi yang terkunci tidak boleh diubah. 2.
**Sample/Admin:** mengelola data sampel, spesifikasi, versi, material
sampel, dan time study. 3. **Warehouse:** menerima bahan, mencatat stok,
dan menerbitkan bahan untuk cutting setelah validasi pemilik/order. 4.
**Production Head/Mandor:** mengatur lini dan operator serta mencatat
output produksi. 5. **Tailor/Penjahit:** melihat tugas dan melaporkan
pekerjaan; tidak dapat mengubah output yang telah diverifikasi. 6. **QC
Inspector:** memeriksa unit dan menetapkan Pass/Repair/Reject serta
kategori cacat; tidak mengubah harga atau data order. 7. **Finance &
Payroll:** memvalidasi formula payroll, merekap gaji, mencatat kebutuhan
biaya/pembelian sesuai ruang lingkup, dan menghitung overhead; tidak
mengubah stok fisik gudang secara langsung. 8. **Maklon
Client/External:** melihat status pesanan, milestone, dan stok milik
sendiri saja.

Prinsip keamanan: pemisahan hak akses operasional dan finansial, isolasi
data klien, serta pencatatan audit yang append-only.

## 12. Ledger, Audit Trail, dan Integritas Transaksi

-   Transaksi dicatat menggunakan prinsip double-entry ledger.
-   Riwayat ledger bersifat append-only/immutable: catatan transaksi
    terkunci tidak diubah melalui UPDATE atau DELETE.
-   Koreksi/pembatalan dilakukan melalui transaksi pembalik, bukan
    dengan menghapus riwayat lama.
-   Sistem mencatat jejak audit perubahan/revisi dan transaksi.
-   Integritas ledger merupakan fondasi bagi modul gudang, produksi, QC,
    payroll, dan costing.

## 13. Fitur/Antarmuka Minimum

1.  **Executive Operations Dashboard:** grafik output 30 menit dan
    matriks progres order.
2.  **Sample & Time Study Tracker:** stopwatch digital untuk waktu
    pengerjaan komponen.
3.  **Multi-Client Warehouse Inventory Grid:** tabel stok dan peringatan
    konflik pemilik bahan.
4.  **Floor Terminal:** input output jahit per penjahit dalam blok 30
    menit.
5.  **QC Inspection Terminal:** pemindaian nomor serial dan pilihan
    Pass, Repair, Reject.
6.  **Payroll & Costing Workspace:** rekap borongan, uang makan, bonus
    QC, dan overhead.

Portal klien B2B menyediakan akses mandiri untuk status pesanan,
milestone, dan saldo stok titipan secara terisolasi.

## 14. Kebutuhan Fungsional Prioritas

Prioritas 1 (Critical) meliputi: - Isolasi data multi-tenant. - RBAC
untuk 8 peran. - Audit trail append-only. - Penguncian Master Spec Sheet
dan Rate Card saat sampel disetujui. - Tag `client_id` dan `order_id`
saat penerimaan bahan. - Pencatatan bahan CMT sebagai aset kustodial. -
Pemblokiran pengeluaran bahan yang salah. - Alokasi lini/operator
dinamis. - Rate Card per komponen. - Input output jahit interval 30
menit. - Status "Menunggu QC" dan hak upah bersyarat. - Klasifikasi QC
Pass/Repair/Reject. - Routing Repair tanpa upah ganda. - Payroll
mingguan, pool uang makan, dan pembagian bonus QC.

Prioritas 2 (High) meliputi pengelolaan versi sampel, time study, stok
opname real-time, pencatatan limbah/efisiensi cutting, taksonomi cacat,
dan alokasi overhead per unit.

## 15. Kebutuhan Non-Fungsional

-   Isolasi data antar-klien: toleransi kebocoran 0%.
-   Ledger immutable dengan transaksi pembalik.
-   Waktu respons terminal maksimal 500 ms.
-   Minimal 10 lini jahit menulis data dalam jendela 30 menit tanpa
    deadlock.
-   Offline tolerance melalui local cache saat gangguan Wi-Fi sementara.
-   Desain antarmuka untuk layar sentuh dengan tombol minimal 48 x 48
    piksel.

## 16. Jadwal Sprint dalam BRD

Dokumen memuat rencana 5 sprint vertikal dengan urutan mengikuti dependensi modul (MOD-01 hingga MOD-05). Tanggal pelaksanaan sengaja tidak dicantumkan pada dokumen deliverable; penanggalan final ditetapkan setelah persetujuan BRD. 1.
**Sprint 1:** Core Double-Entry Ledger, RBAC, tenant
isolation. 2. **Sprint 2:** Multi-tenant warehouse,
pencatatan kustodial, guardrail anti-kontaminasi. 3. **Sprint 3:** siklus sampel, time study, Master Spec, Rate Card, Shop
Floor MES. 4. **Sprint 4:** QC terminal, defect
taxonomy, payroll otomatis, bonus QC, costing overhead. 5. **Sprint 5:**
portal klien B2B, integrasi end-to-end, pengujian
UAT dan kesiapan Go-Live.

BRD menyatakan Sprint 1 tidak boleh dimulai sebelum pejabat pada lembar
persetujuan menandatangani dokumen yang disyaratkan. Dokumen sumber
sendiri berstatus draft menunggu persetujuan.

## 17. Acceptance Test / Kriteria Penerimaan

1.  **Pencegahan kontaminasi silang:** sistem menolak penggunaan bahan
    Klien A untuk order Klien B dan mencatat insiden.
2.  **Penambahan tenaga dinamis:** penjahit baru yang didaftarkan pada
    hari Kamis tetap masuk rekap gaji Sabtu dan perhitungan uang makan
    tanpa memulai ulang siklus.
3.  **Pembagian bonus QC:** pool bonus dari unit lolos QC dibagi tiga
    dengan pembulatan ke bawah; sisa rupiah masuk cadangan operasional.
4.  **Transisi revisi sampel:** sampel v2 yang disetujui dapat dijadikan
    pesanan massal dengan mewarisi spesifikasi dan Rate Card.
5.  **Perbaikan tanpa upah ganda:** unit yang kembali dari Repair tidak
    menambah kredit borongan baru saat diperiksa ulang.

## 18. Batasan dan Hal yang Tidak Boleh Diasumsikan

-   Dokumen sumber berstatus draft dan menunggu persetujuan.
-   Sistem tidak mencakup seluruh kebutuhan akuntansi dan
    ketenagakerjaan formal.
-   Persentase uang makan dipilih manual oleh Finance dalam rentang
    10%--15%.
-   Identitas pejabat pada lembar persetujuan masih berupa placeholder
    yang wajib diisi.
-   Jangan mengarang nama klien, tarif komponen, jumlah upah, tarif
    bonus, nilai stok, atau angka operasional yang tidak tersedia di
    dokumen.
-   Jika pertanyaan tidak dapat dijawab dari BRD, nyatakan bahwa
    informasi tersebut tidak dijelaskan dalam dokumen sumber.

## 19. Panduan Jawaban untuk Chatbot Knowledge Base

Saat menjawab: - Gunakan informasi dalam knowledge base ini sebagai
sumber utama. - Jawab dalam Bahasa Indonesia kecuali pengguna meminta
bahasa lain. - Jelaskan istilah teknis dengan sederhana saat
dibutuhkan. - Bedakan fakta yang tertulis di BRD dari contoh atau
inferensi. - Untuk pertanyaan angka/formula, tampilkan formula dan
sebutkan input yang dibutuhkan jika nilainya belum tersedia. - Jangan
mengarang kebijakan atau angka yang tidak ada di dokumen. - Karena
dokumen diklasifikasikan internal confidential/restricted, informasi
internal hanya boleh ditampilkan kepada pengguna yang memang berwenang.
Isolasi data klien harus ditegakkan oleh sistem akses, bukan hanya
mengandalkan instruksi chatbot.
