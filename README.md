# LostLink

Aplikasi desktop lokal untuk mencatat barang hilang dan ditemukan, mencari pasangan laporan, memverifikasi klaim, serta melihat statistik operasional kampus.

## Fitur

- Dashboard dengan ringkasan laporan dan aktivitas terbaru.
- Pengelolaan kategori serta laporan barang hilang/temuan.
- Unggah satu foto JPG, PNG, atau WebP per laporan (maksimal 5 MB).
- Pencarian dan filter laporan berdasarkan nama, jenis, kategori, lokasi, status, dan tanggal.
- Smart Matching yang menampilkan rincian kontribusi atribut dan kemiripan foto.
- Pencatatan klaim, keputusan admin, serta penyelesaian dua laporan dalam satu transaksi.
- Statistik berbasis Pandas dan ekspor CSV tanpa data kontak atau bukti klaim.
- Data disimpan di MySQL lokal dan foto di folder `uploads/`.

## Kebutuhan

- Windows 10/11.
- Python 3.10 atau lebih baru.
- MySQL Server 8.0 atau lebih baru.
- Microsoft Edge atau Chrome untuk jendela Eel.
- Akses internet untuk memuat Google Fonts dan Chart.js dari CDN.

## Instalasi dan konfigurasi

1. Buat database dan tabel dengan menjalankan `database/schema.sql` melalui MySQL Workbench.
2. Buat dan aktifkan virtual environment dari PowerShell:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Pasang dependensi:

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Salin `.env.example` menjadi `.env`, lalu isi konfigurasi MySQL (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, dan `DB_PASSWORD`). Jangan masukkan `.env` ke Git.
5. Jalankan aplikasi:

   ```powershell
   python main.py
   ```

Jika MySQL Anda memakai user tanpa password, biarkan `DB_PASSWORD` kosong. Skema database hanya perlu dibuat sekali.

## Alur penggunaan

1. Buka **Laporan Barang** dan catat barang hilang atau ditemukan. Foto bersifat opsional.
2. Gunakan tombol cari kecocokan pada laporan terbuka untuk melihat rekomendasi pasangannya.
3. Periksa skor dan atribut yang berkontribusi. Skor adalah heuristik kesamaan, bukan probabilitas bahwa dua laporan merujuk barang yang sama.
4. Jika ada klaim kepemilikan, catat identitas dan bukti yang disampaikan. Admin harus memeriksa bukti dan memutuskan klaim secara manual.
5. Klaim yang disetujui menandai kedua laporan selesai. Ekspor CSV tersedia di halaman Statistik.

## Cara kerja Smart Matching

Kandidat harus memiliki kategori sama dan tanggal barang ditemukan berada pada hari kehilangan hingga 30 hari setelahnya. Skor atribut dasar menggunakan kategori 30%, nama 25% (kemiripan teks), warna 20%, lokasi 15%, dan tanggal 10%.

Jika kedua laporan memiliki foto valid, perceptual hash gambar menambahkan bonus hingga 35 poin; skor akhir dibatasi maksimal 100. Foto yang berbeda tidak mengurangi skor atribut. Jika foto tidak tersedia atau tidak bisa dibaca, skor atribut dasar tetap dipakai. Pasangan dengan skor minimal 60 ditampilkan. Perbedaan crop atau sudut pengambilan gambar dapat memengaruhi kemiripan foto.

## Data lokal dan privasi

- `.env` berisi kredensial database dan tidak boleh diunggah.
- Foto laporan berada di `uploads/`; folder ini dikecualikan dari Git.
- File ekspor berada di `exports/`; folder ini juga dikecualikan dari Git.
- CSV standar tidak menyertakan kontak atau uraian bukti klaim.
- Sebelum demo atau pemindahan komputer, backup database dan folder `uploads/`.

Contoh backup database:

```powershell
mysqldump -u root -p lostlink_db > backup.sql
```

## Troubleshooting

- **Koneksi database gagal:** pastikan service MySQL aktif, `database/schema.sql` sudah dijalankan, dan nilai di `.env` benar.
- **Port aplikasi sudah digunakan:** ubah `APP_PORT` di `.env`.
- **Grafik kosong:** grafik akan terisi setelah laporan dibuat; Chart.js memerlukan akses internet.
- **Foto ditolak:** gunakan JPG, PNG, atau WebP dengan ukuran maksimal 5 MB.
- **Data laporan hilang setelah pindah komputer:** pastikan database yang dikonfigurasi sama dan salin backup database serta folder `uploads/`.

## Struktur proyek

```text
LostLink/
├── backend/          # Laporan, kategori, matching, klaim, dan analitik
├── config/           # Koneksi database
├── database/         # Skema MySQL
├── web/              # UI HTML, CSS, JavaScript, dan logo
├── uploads/          # Foto lokal, tidak diunggah ke Git
├── main.py           # Bootstrap Eel
├── requirements.txt
└── .env.example      # Contoh konfigurasi tanpa kredensial
```
