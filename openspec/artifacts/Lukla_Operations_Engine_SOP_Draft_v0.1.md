# LUKLA OPERATIONS ENGINE

## Draft Standar Operasional Prosedur (SOP) --- Enam Fase Operasional

**Kode dokumen:** LUKLA-SOP-OPS-001\
**Versi:** 0.1 --- Draft untuk validasi\
**Tanggal penyusunan:** 13 Oktober 2026\
**Sumber utama:** *Lukla Operations Engine --- BRD v2.2.1*\
**Status:** BELUM DISETUJUI --- tidak berlaku sebagai kebijakan resmi
sebelum ditinjau dan disahkan pihak Lukla\
**Klasifikasi:** Internal Confidential / Restricted Enterprise Blueprint

------------------------------------------------------------------------

## 1. Tujuan dokumen

Dokumen ini menerjemahkan kebutuhan proses dalam BRD Lukla Operations
Engine menjadi prosedur kerja awal yang dapat ditinjau oleh karyawan
Lukla dan dijadikan sumber informasi untuk Knowledge Base (KB) AI.

SOP ini bertujuan untuk: - menjaga pemisahan material berdasarkan klien
dan pesanan; - menjaga jejak sampel, time study, spesifikasi, dan Rate
Card; - mencatat output produksi secara konsisten; - melacak keputusan
QC; - mendukung perhitungan upah borongan dan biaya produksi dengan data
yang dapat ditelusuri.

**Penting:** BRD adalah sumber kebutuhan sistem, bukan bukti bahwa
seluruh langkah operasional sudah menjadi kebijakan resmi. Bagian yang
belum ditentukan diberi label **\[PERLU VALIDASI LUKLA\]**. Jangan
menerapkan usulan tersebut sebagai aturan resmi sebelum disetujui.

## 2. Cara membaca status ketentuan

-   **\[BRD --- EKSPLISIT\]**: ketentuan dinyatakan langsung di BRD
    v2.2.1.
-   **\[TURUNAN OPERASIONAL\]**: langkah kerja yang disusun untuk
    mengoperasionalkan kebutuhan BRD; perlu ditinjau pemilik proses.
-   **\[PERLU VALIDASI LUKLA\]**: keputusan, formulir, ambang batas,
    penanggung jawab rinci, atau pengecualian yang tidak ditetapkan
    dengan jelas di BRD.
-   **\[DI LUAR CAKUPAN\]**: bukan bagian dari ruang lingkup sistem
    menurut BRD.

## 3. Ruang lingkup dan batasan

SOP ini mencakup enam fase operasional: 1. Gudang dan segregasi
material. 2. Sampel, time study, Master Spec Sheet, dan Rate Card. 3.
Cutting / pemotongan. 4. Produksi jahit dan pencatatan output tiap 30
menit. 5. Quality Control (QC). 6. Payroll borongan dan kalkulasi
overhead/COGS.

SOP juga memuat kontrol lintas fase yang berkaitan dengan identitas
klien/pesanan, akses pengguna, pencatatan ledger, bukti kerja, dan
penggunaan dokumen untuk AI.

**Di luar cakupan BRD:** penghitungan kepatuhan ketenagakerjaan/pajak
formal seperti BPJS, PPh 21, lembur formal, pesangon; akuntansi lengkap;
pelacakan logistik/kendaraan; MRP otomatis penuh; dan aplikasi mobile
native. SOP ini tidak menetapkan kebijakan hukum atau kompensasi yang
tidak ada di BRD.

## 4. Peran yang disebut dalam BRD

  -----------------------------------------------------------------------
  Peran                               Tanggung jawab yang relevan dengan
                                      SOP
  ----------------------------------- -----------------------------------
  Owner / Executive                   Penentu kebijakan dan Rate Card;
                                      kewenangan persetujuan rinci perlu
                                      dikonfirmasi.

  Sample / Admin                      Pengelolaan sampel, versi, time
                                      study, spesifikasi, dan data Rate
                                      Card.

  Warehouse                           Penerimaan, identifikasi,
                                      penyimpanan, serta transaksi
                                      material.

  Production Head / Mandor            Pengelolaan kegiatan produksi dan
                                      pencatatan output
                                      penjahit/komponen.

  Tailor / Penjahit                   Melakukan pekerjaan jahit; data
                                      output dicatat oleh Mandor pada
                                      terminal sesuai BRD.

  QC Inspector                        Memeriksa unit dan menetapkan
                                      status Pass, Repair, atau Reject.

  Finance & Payroll                   Rekap upah borongan, uang makan,
                                      bonus QC, dan perhitungan overhead
                                      sesuai formula BRD.

  Maklon Client / External            Akses terbatas pada data kliennya
                                      sendiri.
  -----------------------------------------------------------------------

**\[PERLU VALIDASI LUKLA\]**: tentukan pejabat pengganti, jalur eskalasi
per shift, siapa yang menyetujui koreksi, siapa yang menyelesaikan
selisih stok, dan siapa yang mengesahkan payroll sebelum pembayaran.

## 5. Kontrol lintas fase

### 5.1 Identitas klien dan pesanan

**\[BRD --- EKSPLISIT\]** Setiap material harus memiliki `client_id` dan
`order_id`. Sistem membandingkan klien pemilik material dengan klien
pemilik pesanan tujuan. Jika tidak cocok, transaksi pengeluaran ditolak
oleh guardrail tingkat database.

**Prosedur kerja \[TURUNAN OPERASIONAL\]:** 1. Pastikan identitas klien
dan pesanan tersedia sebelum transaksi material dilakukan. 2. Pilih
klien dan pesanan yang benar di sistem. 3. Periksa hasil validasi
sistem. 4. Jika transaksi ditolak atau identitas tidak jelas, jangan
mencoba mengakali pembatasan; hentikan transaksi dan eskalasikan sesuai
jalur yang disahkan.

**Bukti pencatatan:** transaksi material, `client_id`, `order_id`, hasil
validasi/penolakan, dan catatan insiden bila ada.

### 5.2 Akses pengguna

**\[BRD --- EKSPLISIT\]** BRD mendefinisikan delapan peran RBAC dan
menyatakan klien eksternal hanya boleh melihat datanya sendiri.

**Prosedur \[TURUNAN OPERASIONAL\]:** 1. Pengguna masuk dengan akun dan
peran yang diberikan. 2. Gunakan hanya tampilan dan data yang diperlukan
untuk peran tersebut. 3. Jangan membagikan akun atau menyalin data klien
lain ke kanal yang tidak berwenang. 4. Laporkan akses yang tampak keliru
kepada penanggung jawab sistem.

**\[PERLU VALIDASI LUKLA\]**: proses permintaan akun, perubahan peran,
penonaktifan akun, pemeriksaan akses berkala, dan respons insiden akses
belum dijelaskan secara rinci di BRD.

### 5.3 Ledger dan koreksi

**\[BRD --- EKSPLISIT\]** Ledger dirancang append-only/immutable.
Koreksi dilakukan melalui transaksi pembalik/reversing, bukan mengubah
atau menghapus transaksi historis.

**Prosedur \[TURUNAN OPERASIONAL\]:** 1. Identifikasi transaksi yang
keliru dan kumpulkan bukti pendukung. 2. Ajukan koreksi kepada peran
yang berwenang. 3. Jika disetujui, buat transaksi pembalik dan transaksi
pengganti sesuai kemampuan sistem. 4. Catat alasan, referensi transaksi
asal, pelaku, waktu, dan persetujuan sesuai mekanisme yang ditetapkan.

**\[PERLU VALIDASI LUKLA\]**: format alasan koreksi, tingkat
persetujuan, dan batas waktu penanganan belum ditentukan.

------------------------------------------------------------------------

# 6. SOP-01 --- Gudang dan Segregasi Material

## 6.1 Tujuan

Mencegah material antarklien tercampur dan memastikan pergerakan
material terlacak berdasarkan klien dan pesanan.

## 6.2 PIC

-   **Pelaksana:** Warehouse.
-   **Koordinasi terkait:** Warehouse/Cutting Supervisor sebagaimana
    disebut dalam BRD.
-   **Eskalasi:** atasan gudang atau Kepala Pabrik sesuai struktur yang
    akan disahkan.

**\[PERLU VALIDASI LUKLA\]**: tetapkan pemilik proses final, pejabat
pengganti, dan pemberi persetujuan untuk selisih stok.

## 6.3 Prosedur penerimaan

1.  Terima material beserta informasi/dokumen yang menyertainya.
    **\[TURUNAN OPERASIONAL\]**
2.  Identifikasi skema komersial pesanan: CMT, Semi-CMT, atau CMT +
    Bahan / Full Package. **\[BRD --- EKSPLISIT: skema menentukan pihak
    penyedia material\]**
3.  Pastikan identitas klien dan pesanan dapat ditentukan.
4.  Catat material dengan `client_id` dan `order_id`. **\[BRD ---
    EKSPLISIT\]**
5.  Jika identitas material tidak lengkap atau tidak konsisten, tahan
    proses penempatan/pengeluaran sampai ditinjau. **\[TURUNAN
    OPERASIONAL; perlu persetujuan Lukla\]**
6.  Simpan material dengan cara yang menjaga pemisahan kepemilikan
    antarklien. **\[BRD --- EKSPLISIT pada prinsip segregasi; tata letak
    rinci perlu validasi\]**

## 6.4 Prosedur penyimpanan dan pengeluaran

1.  Cari material berdasarkan identitas klien dan pesanan.
2.  Sebelum mengeluarkan material, cocokkan klien pemilik material
    dengan klien pada pesanan tujuan.
3.  Jalankan transaksi pengeluaran melalui sistem.
4.  Jika guardrail menolak transaksi karena klien tidak cocok, jangan
    keluarkan material dan jangan mengubah identitas untuk melewati
    penolakan.
5.  Catat dan eskalasikan ketidaksesuaian menurut prosedur yang
    disahkan.
6.  Pastikan transaksi material yang berhasil memiliki jejak pencatatan.

**\[BRD --- EKSPLISIT\]** Sistem harus menolak transaksi bila
`client_id` pemilik material berbeda dengan `client_id` pemilik pesanan
tujuan.

## 6.5 Perlakuan berdasarkan skema komersial

-   **CMT:** klien menyediakan bahan baku utama dan bahan
    pembantu/aksesori; bahan klien berstatus titipan kustodial, bukan
    aset neraca Lukla.
-   **Semi-CMT:** klien menyediakan bahan utama; Lukla mengadakan bahan
    pembantu/aksesori seperti furing, benang, kancing, dan resleting.
-   **CMT + Bahan / Full Package:** Lukla mengadakan seluruh bahan dan
    memproduksi; skema ini juga digunakan untuk merek internal Snøhund.

**\[PERLU VALIDASI LUKLA\]**: prosedur pencatatan rinci, kode lokasi
fisik, satuan ukur, toleransi selisih, cycle count, retur material, sisa
potongan, dan otorisasi penyesuaian stok tidak dijabarkan lengkap dalam
BRD.

## 6.6 Bukti pencatatan

-   Data penerimaan dan pengeluaran material.
-   `client_id` dan `order_id`.
-   Identitas material dan jumlah/satuan yang digunakan oleh sistem.
-   Catatan penolakan guardrail atau ketidaksesuaian.
-   Referensi transaksi koreksi bila ada.

## 6.7 Kontrol dan eskalasi

**Kontrol wajib dari BRD:** identitas klien/pesanan pada material dan
guardrail anti-kontaminasi pada tingkat transaksi.

**Eskalasi:** hentikan transaksi yang identitasnya tidak jelas atau
ditolak sistem; laporkan kepada atasan gudang/penanggung jawab yang
ditunjuk. **\[PERLU VALIDASI LUKLA\]**: kanal pelaporan, waktu respons,
dan otoritas pelepasan material.

------------------------------------------------------------------------

# 7. SOP-02 --- Sampel, Time Study, Master Spec Sheet, dan Rate Card

## 7.1 Tujuan

Menjaga jejak versi sampel, spesifikasi, waktu kerja komponen, dan tarif
upah agar produksi dan perhitungan biaya merujuk pada data yang
disetujui.

## 7.2 PIC

-   **Pelaksana:** Sample/Admin.
-   **Pemilik kebijakan/Rate Card:** Owner/Executive, sebagaimana
    dijelaskan BRD.
-   **Pihak terkait:** tim Sample dan pihak klien sesuai proses
    persetujuan.

**\[PERLU VALIDASI LUKLA\]**: tetapkan siapa yang merekam, memeriksa,
dan mengesahkan time study serta spesifikasi akhir.

## 7.3 Prosedur pembuatan dan revisi sampel

1.  Buat catatan sampel untuk produk/pesanan terkait. **\[TURUNAN
    OPERASIONAL\]**
2.  Berikan identitas versi yang dapat ditelusuri, misalnya v1, v2, dan
    seterusnya. **\[BRD --- EKSPLISIT: versi sampel harus dikelola\]**
3.  Catat perubahan spesifikasi dari versi sebelumnya. **\[TURUNAN
    OPERASIONAL\]**
4.  Hubungkan versi sampel dengan klien dan pesanan yang benar jika
    informasi tersebut tersedia di sistem. **\[TURUNAN OPERASIONAL;
    detail field perlu validasi\]**
5.  Simpan hasil tinjauan/persetujuan klien sesuai mekanisme yang
    ditetapkan.
6.  Setelah klien menyetujui, Master Spec Sheet dan Rate Card yang
    terkait dikunci sesuai rancangan BRD. **\[BRD --- EKSPLISIT\]**
7.  Jika diperlukan revisi setelah penguncian, jangan menimpa riwayat
    lama; ajukan proses revisi/versi baru sesuai mekanisme yang
    disetujui. **\[TURUNAN OPERASIONAL; perlu validasi\]**

## 7.4 Prosedur time study

1.  Pilih komponen pekerjaan yang akan diukur dan pastikan sampel/versi
    yang digunakan jelas. **\[TURUNAN OPERASIONAL\]**
2.  Rekam waktu pengerjaan komponen menggunakan instrumen
    stopwatch/time-study pada sistem sesuai desain BRD.
3.  Pastikan catatan waktu terkait dengan komponen dan versi sampel yang
    tepat.
4.  Tinjau hasil pencatatan untuk memastikan data tidak tertukar dengan
    komponen atau versi lain. **\[TURUNAN OPERASIONAL\]**
5.  Simpan hasil time study sebagai referensi saat menyusun spesifikasi
    dan Rate Card.

**\[PERLU VALIDASI LUKLA\]**: jumlah pengulangan pengukuran, cara
menangani pencilan, siapa yang memvalidasi hasil, satuan dan pembulatan
waktu, serta standar waktu yang diterima tidak ditentukan dalam BRD.

## 7.5 Prosedur Master Spec Sheet dan Rate Card

1.  Kumpulkan spesifikasi komponen dan hasil time study yang relevan.
2.  Susun Master Spec Sheet dan Rate Card untuk ditinjau.
3.  Minta persetujuan pihak yang berwenang sesuai kebijakan Lukla.
4.  Setelah persetujuan klien, kunci dokumen yang disetujui sesuai
    kemampuan sistem. **\[BRD --- EKSPLISIT\]**
5.  Pastikan proses produksi dan payroll merujuk pada versi yang
    berlaku; jangan mengasumsikan tarif yang belum disetujui.

## 7.6 Bukti pencatatan

-   Catatan sampel dan riwayat versi.
-   Spesifikasi komponen.
-   Rekaman time study.
-   Master Spec Sheet.
-   Rate Card dan status persetujuan/penguncian.
-   Catatan perubahan/revisi dan referensi versi sebelumnya, jika fitur
    tersebut tersedia.

## 7.7 Kontrol dan eskalasi

**Kontrol BRD:** versi sampel, time study, Master Spec Sheet, dan Rate
Card harus memiliki jejak; Master Spec Sheet dan Rate Card dikunci
setelah persetujuan klien.

**Eskalasi:** jika versi sampel, spesifikasi, atau Rate Card tidak
jelas/bertentangan, jangan memilih versi berdasarkan perkiraan. Minta
Sample/Admin dan pihak berwenang memastikan versi yang berlaku.
**\[Jalur persetujuan rinci perlu validasi\]**

------------------------------------------------------------------------

# 8. SOP-03 --- Persiapan Order dan Cutting

## 8.1 Tujuan

Memastikan material dan spesifikasi yang digunakan pada pemotongan
sesuai dengan klien, pesanan, dan informasi produk yang berlaku.

## 8.2 PIC

-   **Pelaksana terkait:** Warehouse dan tim Cutting.
-   **Koordinasi:** Warehouse & Cutting Supervisor.
-   **Referensi spesifikasi:** Sample/Admin dan Master Spec Sheet yang
    disetujui.

**\[PERLU VALIDASI LUKLA\]**: BRD menyebut cutting dan guardrail, tetapi
rincian peran operator cutting dan pemberi izin mulai potong perlu
ditetapkan.

## 8.3 Prosedur

1.  Identifikasi pesanan yang akan diproses.
2.  Pastikan `client_id` dan `order_id` pada pesanan tersedia.
3.  Periksa skema komersial agar sumber material sesuai dengan tanggung
    jawab penyediaan material.
4.  Pastikan material yang akan dikeluarkan memang milik klien/pesanan
    yang dituju.
5.  Pastikan spesifikasi yang digunakan merujuk pada Master Spec
    Sheet/versi yang disetujui. **\[TURUNAN OPERASIONAL dari kontrol
    spesifikasi BRD\]**
6.  Ajukan transaksi pengeluaran material melalui sistem dan patuhi
    hasil guardrail.
7.  Lakukan pemotongan berdasarkan spesifikasi dan proses kerja cutting
    yang disahkan Lukla. **\[Langkah teknis pemotongan tidak dirinci
    dalam BRD\]**
8.  Catat hasil pemotongan/bundel sesuai kemampuan sistem dan prosedur
    yang disahkan. BRD menyebut verifikasi penerbitan kain dan bundel
    potong, tetapi struktur data rinci perlu validasi.
9.  Jika terjadi ketidaksesuaian identitas material, spesifikasi, atau
    pesanan, hentikan penggunaan material terkait dan eskalasikan.

## 8.4 Kontrol

-   Tidak boleh menggunakan material untuk pesanan dengan `client_id`
    yang tidak sesuai.
-   Guardrail database harus memblokir transaksi material lintas klien.
-   Spesifikasi yang digunakan harus dapat ditelusuri ke versi yang
    berlaku.
-   **\[PERLU VALIDASI LUKLA\]**: metode rekonsiliasi kain masuk vs kain
    terpakai, pencatatan sisa potongan, toleransi susut/cacat, dan
    persetujuan hasil cutting.

## 8.5 Bukti pencatatan

-   Referensi order dan identitas klien.
-   Referensi material yang dikeluarkan.
-   Hasil validasi guardrail.
-   Referensi spesifikasi/versi sampel.
-   Catatan hasil cutting atau bundel potong jika tersedia.
-   Catatan insiden dan tindakan koreksi.

## 8.6 Eskalasi

Untuk penolakan guardrail atau ketidaksesuaian spesifikasi/material,
jangan lanjut menggunakan material sampai penanggung jawab yang ditunjuk
meninjau kasus. **\[PERLU VALIDASI LUKLA\]**: siapa yang memberi
keputusan akhir dan bagaimana material yang sudah terlanjur dipotong
ditangani.

------------------------------------------------------------------------

# 9. SOP-04 --- Produksi Jahit dan Pencatatan Output Tiap 30 Menit

## 9.1 Tujuan

Merekam output kerja secara konsisten menurut penjahit, komponen, dan
pesanan serta menyediakan data yang dapat diverifikasi untuk QC dan
payroll.

## 9.2 PIC

-   **Pelaksana input:** Production Head/Mandor.
-   **Pelaksana pekerjaan:** Tailor/Penjahit.
-   **Penerima tahap berikutnya:** QC Inspector.

## 9.3 Prosedur

1.  Pastikan pesanan yang berjalan memiliki data order dan
    spesifikasi/Rate Card yang berlaku.
2.  Pastikan terminal produksi menampilkan konteks pesanan dan komponen
    yang benar. **\[TURUNAN OPERASIONAL\]**
3.  Pada setiap interval 30 menit, Mandor memasukkan hasil jahit per
    penjahit/komponen melalui terminal layar sentuh. **\[BRD ---
    EKSPLISIT\]**
4.  Data yang dicatat masuk ke ledger sebagai unit **"Menunggu QC"**.
    **\[BRD --- EKSPLISIT\]**
5.  Pastikan input berkaitan dengan penjahit, komponen, dan order yang
    benar sejauh field tersedia pada sistem.
6.  Jika input salah atau ganda, jangan menghapus/menimpa catatan
    ledger; ikuti proses koreksi melalui transaksi pembalik dan catatan
    pengganti yang diizinkan. **\[BRD --- EKSPLISIT untuk prinsip
    ledger; detail operasional perlu validasi\]**
7.  Kirim/siapkan unit untuk proses QC sesuai alur kerja yang ditetapkan
    Lukla.

## 9.4 Kontrol

-   Pencatatan dilakukan setiap 30 menit.
-   Unit baru berstatus Menunggu QC; status ini tidak boleh dianggap
    sebagai unit Pass.
-   Data output harus bisa ditelusuri ke pekerja/komponen/order sesuai
    rancangan sistem.
-   Ledger bersifat append-only/immutable; koreksi harus menjaga jejak
    transaksi.

## 9.5 Bukti pencatatan

-   Catatan output per interval 30 menit.
-   Identitas penjahit, komponen, order, dan waktu pencatatan sesuai
    field sistem.
-   Status awal Menunggu QC.
-   Riwayat koreksi bila ada.

## 9.6 Eskalasi

Jika terminal tidak tersedia, konteks order salah, atau pencatatan
gagal, laporkan kepada Mandor/Production Head dan penanggung jawab
sistem. BRD menyebut toleransi cache lokal/offline, tetapi tidak
menetapkan prosedur manual pengganti, batas durasi offline, atau tata
cara sinkronisasi. **\[PERLU VALIDASI LUKLA\]** Jangan membuat angka
atau langkah pemulihan sendiri; gunakan prosedur downtime yang kelak
disahkan.

------------------------------------------------------------------------

# 10. SOP-05 --- Quality Control (QC)

## 10.1 Tujuan

Menetapkan dan merekam status kualitas tiap unit agar unit yang lolos,
perlu perbaikan, atau ditolak diperlakukan sesuai alur sistem.

## 10.2 PIC

-   **Pelaksana:** QC Inspector.
-   **Pihak terkait:** Mandor/Penjahit untuk Repair.
-   **Pengguna data berikutnya:** Finance & Payroll dan pihak produksi.

## 10.3 Prosedur pemeriksaan

1.  Ambil unit yang menunggu pemeriksaan dan identifikasi nomor
    serial/unit melalui terminal QC.
2.  Periksa unit berdasarkan standar inspeksi yang berlaku di Lukla.
    **\[PERLU VALIDASI LUKLA: standar inspeksi rinci dan taksonomi cacat
    tidak tersedia lengkap dalam ringkasan BRD\]**
3.  Catat hasil pemeriksaan pada terminal.
4.  Tetapkan salah satu status yang tersedia: **Pass**, **Repair**, atau
    **Reject**. **\[BRD --- EKSPLISIT\]**
5.  Pastikan status tersimpan dan terkait dengan unit yang benar.

## 10.4 Arti status sesuai BRD

-   **Pass:** unit siap dikemas dan mengaktifkan hak gaji sesuai
    ketentuan sistem.
-   **Repair:** unit kembali ke penjahit untuk diperbaiki; tidak boleh
    menghasilkan pembayaran ganda untuk unit yang sama.
-   **Reject:** unit ditandai sebagai scrap/ditolak dan diproses sesuai
    aturan yang berlaku dalam sistem; BRD menyebut "potong gaji" dalam
    uraian alur, tetapi detail kebijakan dan penerapannya harus
    divalidasi oleh Lukla sebelum diberlakukan.

**Catatan penting:** SOP ini tidak menafsirkan "potong gaji" sebagai
izin otomatis untuk melakukan pemotongan upah tertentu. Ketentuan
kompensasi formal dan hukum berada di luar cakupan BRD; setiap aturan
kompensasi memerlukan tinjauan dan persetujuan yang sesuai.

## 10.5 Prosedur Repair

1.  Catat status Repair pada unit yang diperiksa.
2.  Arahkan unit kembali ke proses/peran perbaikan sesuai alur produksi
    Lukla.
3.  Setelah perbaikan, unit diperiksa kembali sesuai mekanisme yang
    ditetapkan.
4.  Pastikan riwayat status tetap dapat ditelusuri dan unit tidak
    dihitung sebagai pembayaran ganda.

**\[PERLU VALIDASI LUKLA\]**: apakah unit mempertahankan serial yang
sama, bagaimana riwayat inspeksi ulang dicatat, dan bagaimana kegagalan
berulang diputuskan.

## 10.6 Prosedur Reject

1.  Catat status Reject pada unit yang benar.
2.  Catat alasan/jenis cacat jika fitur tersebut tersedia.
3.  Pisahkan unit dari alur unit Pass sesuai proses fisik yang akan
    disahkan. **\[TURUNAN OPERASIONAL\]**
4.  Eskalasikan keputusan scrap, penggunaan ulang material, dan dampak
    payroll kepada pihak berwenang sesuai kebijakan yang disahkan.

**\[PERLU VALIDASI LUKLA\]**: definisi scrap, tingkat cacat, bukti foto,
persetujuan reject, dan aturan finansialnya belum dirinci lengkap dalam
BRD.

## 10.7 Kontrol

-   Setiap unit diperiksa dengan referensi serial/unit.
-   Hanya status Pass yang dinyatakan mengaktifkan hak gaji menurut BRD.
-   Repair tidak boleh menyebabkan gaji ganda untuk unit yang sama.
-   Keputusan QC dan perubahan status harus dapat ditelusuri.
-   Taksonomi cacat dan aturan eskalasi perlu disahkan Lukla.

## 10.8 Bukti pencatatan

-   Identitas unit/serial.
-   Status Pass/Repair/Reject.
-   Identitas pemeriksa dan waktu jika tersedia di sistem.
-   Alasan/jenis cacat dan riwayat pemeriksaan ulang jika tersedia.
-   Referensi koreksi transaksi jika terjadi salah input.

## 10.9 Eskalasi

Jika serial tidak ditemukan, status tidak dapat disimpan, standar
pemeriksaan tidak jelas, atau hasil diperselisihkan, tahan keputusan
akhir unit dan eskalasikan ke QC Lead/penanggung jawab yang ditunjuk.
**\[PERLU VALIDASI LUKLA\]**: jalur banding, pemeriksaan ulang, dan
otoritas final.

------------------------------------------------------------------------

# 11. SOP-06 --- Payroll Borongan dan Kalkulasi Overhead/COGS

## 11.1 Tujuan

Menyusun rekap upah borongan mingguan, alokasi uang makan, pembagian
bonus QC, dan perhitungan overhead per unit berdasarkan formula dalam
BRD serta data operasional yang tercatat.

## 11.2 PIC

-   **Pelaksana:** Finance & Payroll.
-   **Sumber data:** output produksi, status QC, Rate Card, dan data
    overhead.
-   **Pihak kebijakan:** Owner/Executive untuk Rate Card; pengesahan
    payroll final perlu ditetapkan.

## 11.3 Prasyarat

Sebelum menghitung, pastikan data unit, status QC, tarif komponen, dan
periode yang digunakan jelas. Unit Menunggu QC atau Repair tidak boleh
otomatis diperlakukan sebagai unit Pass yang memenuhi syarat upah.

**\[PERLU VALIDASI LUKLA\]**: aturan cut-off, penanganan transaksi
terlambat, pembekuan data periode, dan pihak yang menyetujui rekap
final.

## 11.4 Upah borongan mingguan

**\[BRD --- EKSPLISIT\]** Perhitungan dilakukan setiap Sabtu.

Formula: **Upah penjahit = jumlah seluruh (unit terverifikasi yang
memenuhi syarat × tarif upah komponen).**

Prosedur: 1. Ambil data unit yang memenuhi syarat berdasarkan status QC
dan aturan sistem. 2. Kelompokkan unit menurut penjahit dan komponen
sesuai data yang tersedia. 3. Cocokkan dengan Rate Card yang berlaku
untuk order/komponen terkait. 4. Hitung upah sebagai unit terverifikasi
dikalikan tarif komponen, lalu jumlahkan untuk setiap penjahit. 5.
Tinjau transaksi yang tidak lengkap, berulang, atau masih
diperselisihkan sebelum rekap disahkan. 6. Simpan rekap dan referensi
data sumber.

**\[PERLU VALIDASI LUKLA\]**: definisi persis "unit terverifikasi",
aturan pembulatan, cut-off waktu, dan proses persetujuan pembayaran.

## 11.5 Uang makan mengambang

**\[BRD --- EKSPLISIT\]** Persentase yang dipilih secara manual berada
pada rentang 10%--15% dari total upah seluruh penjahit.

Formula: **Total uang makan = persentase uang makan × total upah seluruh
penjahit.**

Prosedur: 1. Pastikan total upah seluruh penjahit telah direkonsiliasi.
2. Gunakan persentase yang dipilih secara manual dan berada dalam
rentang 10%--15%. 3. Catat persentase yang dipakai, total upah dasar,
hasil perhitungan, dan periode terkait. 4. Minta pengesahan sesuai
kebijakan Lukla.

**\[PERLU VALIDASI LUKLA\]**: siapa yang memilih persentase, dasar
pemilihan, penerima dan metode pembagian uang makan, serta aturan
pembulatan.

## 11.6 Pool bonus QC

**\[BRD --- EKSPLISIT\]** Total dana QC = jumlah pakaian yang lolos QC ×
tarif bonus per pakaian. Pool dibagi rata kepada dua Mandor dan Kepala
Operasional (tiga pihak); pembagian dibulatkan ke bawah dan sisa masuk
ke cadangan operasional.

Prosedur: 1. Ambil jumlah unit Pass yang memenuhi definisi periode. 2.
Gunakan tarif bonus per pakaian yang berlaku. 3. Hitung total dana QC.
4. Bagi total dana menjadi tiga bagian sama besar dan bulatkan ke bawah
sesuai aturan BRD. 5. Catat sisa pembulatan sebagai cadangan
operasional. 6. Simpan formula, input, hasil, dan persetujuan.

**\[PERLU VALIDASI LUKLA\]**: nilai tarif bonus, identitas resmi
penerima, periode unit Pass, otorisasi, serta cara pencatatan cadangan
operasional.

## 11.7 Overhead pabrik per unit

**\[BRD --- EKSPLISIT\]** Overhead per unit = total biaya operasional
pabrik bulanan dibagi total unit pakaian jadi yang diproduksi pada bulan
tersebut.

Prosedur: 1. Kumpulkan total biaya operasional pabrik bulanan dari
sumber yang ditetapkan. 2. Tentukan jumlah unit pakaian jadi untuk bulan
yang sama sesuai definisi Lukla. 3. Hitung overhead per unit dengan
formula BRD. 4. Simpan input, periode, hasil, dan sumber data. 5. Jika
jumlah unit pembagi nol atau data periode belum lengkap, jangan membuat
hasil perkiraan; eskalasikan untuk keputusan Finance.

**\[PERLU VALIDASI LUKLA\]**: daftar akun overhead, sumber angka biaya,
perlakuan biaya satu kali, definisi "unit pakaian jadi", dan penanganan
bulan dengan produksi nol.

## 11.8 Bukti pencatatan

-   Rekap unit terverifikasi dan status QC.
-   Versi Rate Card yang digunakan.
-   Rekap upah per penjahit dan komponen.
-   Persentase serta perhitungan uang makan.
-   Jumlah unit Pass, tarif bonus, pembagian bonus, dan sisa pembulatan.
-   Total overhead bulanan, jumlah unit pembagi, hasil overhead per
    unit.
-   Catatan pemeriksaan, persetujuan, dan koreksi.

## 11.9 Kontrol dan eskalasi

-   Jangan memasukkan unit yang belum memenuhi syarat sebagai unit Pass.
-   Jangan memakai Rate Card yang belum disetujui atau tidak jelas
    versinya.
-   Pastikan semua hasil dapat ditelusuri ke data sumber.
-   Gunakan mekanisme koreksi ledger yang mempertahankan riwayat.
-   Untuk selisih, data hilang, nilai pembagi nol, atau tarif tidak
    disetujui, tahan pengesahan perhitungan terkait dan eskalasikan
    kepada Finance/Payroll Lead dan pejabat yang ditunjuk.

**\[DI LUAR CAKUPAN\]**: perhitungan dan kepatuhan formal BPJS, PPh 21,
lembur formal, pesangon, serta aspek ketenagakerjaan/pajak lainnya tidak
ditetapkan oleh SOP ini.

------------------------------------------------------------------------

## 12. Matriks ringkas bukti dan titik kontrol

  ----------------------------------------------------------------------------
  Fase                    Titik kontrol utama     Bukti minimum yang
                                                  diharapkan
  ----------------------- ----------------------- ----------------------------
  1\. Gudang              `client_id` +           Transaksi material,
                          `order_id`; guardrail   identitas klien/order, hasil
                          lintas klien            validasi

  2\. Sampel & time study Versi sampel; jejak     Riwayat versi, time study,
                          waktu/spec; Rate Card   Master Spec Sheet, Rate
                          terkunci setelah        Card, status persetujuan
                          persetujuan             

  3\. Cutting             Material dan            Referensi
                          spesifikasi sesuai      order/material/spec, catatan
                          order                   cutting jika tersedia

  4\. Jahit               Input setiap 30 menit;  Catatan output per
                          status awal Menunggu QC penjahit/komponen/interval

  5\. QC                  Status                  Serial/unit, status QC,
                          Pass/Repair/Reject;     alasan/riwayat jika tersedia
                          cegah gaji ganda untuk  
                          Repair                  

  6\. Payroll & costing   Unit memenuhi syarat;   Rekap, Rate Card, input
                          formula sesuai BRD;     formula, hasil, persetujuan
                          sumber data dapat       dan koreksi
                          ditelusuri              
  ----------------------------------------------------------------------------

## 13. Ketentuan untuk Knowledge Base AI

Dokumen ini dapat menjadi sumber KB setelah ditinjau dan disetujui.
Untuk penggunaan AI:

1.  **Jelaskan status sumber.** Jika dokumen masih berstatus Draft, AI
    harus menyebutnya sebagai draft, bukan kebijakan final.
2.  **Bedakan fakta dan usulan.** AI tidak boleh menyajikan label
    \[TURUNAN OPERASIONAL\] atau \[PERLU VALIDASI LUKLA\] seolah-olah
    aturan resmi.
3.  **Jangan mengarang detail.** Jika ditanya tentang toleransi stok,
    standar cacat, otorisasi, tenggat, aturan pembulatan yang belum
    ditetapkan, atau prosedur downtime, AI harus menyatakan bahwa sumber
    yang tersedia belum menetapkannya dan mengarahkan pengguna ke
    pemilik proses.
4.  **Rujuk sumber.** Jika memungkinkan, jawaban harus menyebut
    kode/nama SOP, bagian, dan versi dokumen.
5.  **Lindungi data klien.** Dokumen SOP umum tidak boleh menjadi alasan
    untuk mengungkap data pesanan, stok, biaya, atau informasi khusus
    klien lain. Pembatasan akses harus ditegakkan oleh aplikasi/sistem,
    bukan hanya prompt AI.
6.  **Kendalikan versi.** Saat SOP disahkan atau direvisi, tandai versi
    lama sebagai superseded/arsip dan perbarui sumber KB. Jangan biarkan
    draft yang sudah tidak berlaku tampil sebagai prosedur terkini.
7.  **Uji jawaban.** Uji pertanyaan normal, pertanyaan yang jawabannya
    belum ada, pertanyaan yang bertentangan dengan SOP, dan permintaan
    data klien yang tidak berwenang sebelum digunakan secara
    operasional.

Catatan teknis: Amazon Bedrock Knowledge Bases dapat terhubung ke sumber
data Amazon S3; dokumentasi AWS menjelaskan sinkronisasi konten dan
dukungan metadata. Hak akses dokumen harus dikonfigurasi secara tepat
karena konten yang disinkronkan dapat tersedia bagi principal yang
memiliki izin retrieval pada Knowledge Base. Lihat dokumentasi resmi
AWS:
https://docs.aws.amazon.com/bedrock/latest/userguide/s3-data-source-connector.html

## 14. Daftar keputusan yang harus divalidasi sebelum pengesahan

-   [ ] Nama dan jabatan pemilik setiap SOP.
-   [ ] Pihak yang menyetujui dokumen dan tanggal efektif.
-   [ ] Format formulir, kode transaksi, satuan ukur, dan lokasi
    material.
-   [ ] Prosedur stok selisih, retur, sisa potongan, dan material rusak.
-   [ ] Standar time study dan proses persetujuan Rate Card.
-   [ ] Prosedur cutting, hasil bundel, dan toleransi material.
-   [ ] Prosedur saat terminal/jaringan offline dan sinkronisasi data.
-   [ ] Standar inspeksi QC, taksonomi cacat, inspeksi ulang, dan
    otorisasi Reject.
-   [ ] Definisi unit terverifikasi, cut-off payroll, pembulatan, dan
    persetujuan final.
-   [ ] Pihak yang memilih persentase uang makan 10%--15%.
-   [ ] Tarif bonus QC dan mekanisme pencatatan cadangan operasional.
-   [ ] Definisi biaya overhead dan unit pakaian jadi untuk pembaginya.
-   [ ] Jalur eskalasi, tenggat respons, pengganti PIC, dan format
    insiden.
-   [ ] Persyaratan akses, kerahasiaan, retensi, dan peninjauan berkala
    untuk dokumen KB AI.

## 15. Persetujuan dokumen

  -----------------------------------------------------------------------
  Peran             Nama              Tanda tangan /    Tanggal
                                      persetujuan       
  ----------------- ----------------- ----------------- -----------------
  Owner / Executive \[Diisi Lukla\]   \[Menunggu\]      \[Menunggu\]

  Kepala Pabrik /   \[Diisi Lukla\]   \[Menunggu\]      \[Menunggu\]
  pemilik proses                                        

  Perwakilan        \[Diisi Lukla\]   \[Menunggu\]      \[Menunggu\]
  Warehouse /                                           
  Cutting                                               

  Perwakilan Sample \[Diisi Lukla\]   \[Menunggu\]      \[Menunggu\]
  / Admin                                               

  Perwakilan        \[Diisi Lukla\]   \[Menunggu\]      \[Menunggu\]
  Production / QC                                       

  Perwakilan        \[Diisi Lukla\]   \[Menunggu\]      \[Menunggu\]
  Finance & Payroll                                     
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## Referensi

-   *Lukla Operations Engine --- BRD v2.2.1*, status Draft --- Menunggu
    Persetujuan, 12 Oktober 2026 (dokumen sumber utama).
-   AWS Documentation, "Connect to Amazon S3 for your knowledge base":
    https://docs.aws.amazon.com/bedrock/latest/userguide/s3-data-source-connector.html

**Akhir dokumen --- Draft untuk validasi internal.**
