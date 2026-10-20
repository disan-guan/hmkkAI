# hmkkAI

Hitung Masuk Keluar Kendaraan AI

Sistem penghitung kendaraan otomatis berbasis YOLO, OpenCV, dan CCTV streaming HLS. Sistem mendeteksi serta menghitung kendaraan yang melintasi garis sensor virtual, menyimpan data ke SQLite, dan menyediakan REST API untuk integrasi FrontEnd.

## Fitur

- Deteksi kendaraan menggunakan YOLO.
- Tracking kendaraan menggunakan ByteTrack.
- Kategori kendaraan: Mobil, Motor, Bus, dan Truk.
- Penghitungan kendaraan masuk dan keluar.
- Garis sensor virtual dengan posisi, panjang, dan sudut yang dapat diatur.
- Panel counter dengan tanggal dan FPS.
- Penyimpanan riwayat ke database SQLite.
- REST API menggunakan FastAPI.
- Rekap kendaraan harian dan riwayat berdasarkan filter.
- Konfigurasi melalui `config.ini`.

## Struktur Project

```text
hmkkAI/
├── main.py
├── config.ini
├── requirements.txt
├── README.md
├── vehicle_counter.db
├── yolo26n.pt
├── .venv/
└── setup/
    ├── api.py
    ├── config.py
    ├── database.py
    └── ai.py
```

Keterangan:

- `main.py`: menjalankan API dan Vehicle Counter.
- `config.ini`: konfigurasi CCTV, AI, tampilan, dan sensor.
- `setup/api.py`: REST API untuk FrontEnd.
- `setup/config.py`: membaca konfigurasi.
- `setup/database.py`: koneksi dan penyimpanan SQLite.
- `setup/ai.py`: deteksi dan penghitungan kendaraan.
- `vehicle_counter.db`: database yang dibuat otomatis.
- `yolo26n.pt`: file model YOLO yang digunakan.

## Persyaratan

- Windows 10/11 atau sistem operasi yang kompatibel.
- Python 3.10 atau lebih baru yang kompatibel dengan versi package.
- Koneksi internet untuk mengakses stream CCTV.
- File model YOLO sesuai konfigurasi.
- Komputer dengan kemampuan menjalankan inferensi YOLO.

## Instalasi

### 1. Buat virtual environment

```bash
python -m venv .venv
```

### 2. Aktifkan virtual environment

Windows CMD:

```bat
.venv\Scripts\activate
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Instal dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Siapkan model YOLO

Letakkan file model `yolo26n.pt` di folder utama project, atau sesuaikan `MODEL_PATH` pada `config.ini`.

### 5. Konfigurasi aplikasi

Edit file `config.ini` untuk mengatur URL CCTV, model, confidence, FPS, resolusi tampilan, dan garis sensor.

Pastikan URL CCTV dapat diakses dari komputer yang menjalankan aplikasi.

## Menjalankan Aplikasi

Dari folder utama project, jalankan:

```bash
python main.py
```

Launcher akan menjalankan API pada port 8000 dan aplikasi Vehicle Counter.

Tekan `Q` pada jendela video untuk keluar dari aplikasi penghitung kendaraan. Gunakan `CTRL+C` pada terminal launcher untuk menghentikan proses yang masih berjalan.

## REST API

Dokumentasi API:

```text
http://127.0.0.1:8000/docs
```

Status layanan:

```http
GET /api/health
```

Ringkasan hari ini:

```http
GET /api/summary
```

Ringkasan berdasarkan tanggal:

```http
GET /api/summary?date=2026-10-20
```

Riwayat kendaraan:

```http
GET /api/events
```

Riwayat berdasarkan tanggal:

```http
GET /api/events?date=2026-10-20
```

Filter berdasarkan arah:

```http
GET /api/events?direction=Masuk
```

Filter berdasarkan jenis kendaraan:

```http
GET /api/events?vehicle_type=Motor
```

Rekap harian:

```http
GET /api/daily
```

Rekap berdasarkan rentang tanggal:

```http
GET /api/daily?start_date=2026-10-01&end_date=2026-10-20
```

Parameter `limit` dan `offset` tersedia pada endpoint `/api/events` untuk pagination.

## Integrasi FrontEnd

Contoh menggunakan JavaScript Fetch:

```javascript
async function getVehicleSummary() {
  const response = await fetch("http://127.0.0.1:8000/api/summary");

  if (!response.ok) {
    throw new Error("Gagal mengambil data kendaraan");
  }

  return await response.json();
}

getVehicleSummary()
  .then((data) => {
    console.log("Masuk:", data.total_masuk);
    console.log("Keluar:", data.total_keluar);
    console.log("Detail:", data.vehicles);
  })
  .catch(console.error);
```

Jika FrontEnd berjalan di komputer lain, ganti `127.0.0.1` dengan alamat IP komputer server, misalnya `http://192.168.1.10:8000`.

Pastikan firewall mengizinkan koneksi ke port 8000 dan konfigurasi CORS dibatasi sesuai domain FrontEnd saat digunakan di lingkungan produksi.

## Database

SQLite menggunakan file `vehicle_counter.db`.

Setiap kejadian kendaraan yang berhasil dihitung disimpan dengan informasi:

- ID kejadian.
- Tanggal dan waktu.
- Jenis kendaraan.
- Arah: Masuk atau Keluar.
- ID tracking kendaraan.

Database dibuat otomatis oleh aplikasi jika belum tersedia.

## Konfigurasi Garis Sensor

Pengaturan garis sensor tersedia di bagian `[SENSOR]` pada `config.ini`:

- `CENTER_X`: posisi horizontal tengah garis.
- `CENTER_Y`: posisi vertikal tengah garis.
- `LENGTH`: panjang relatif terhadap lebar video.
- `ANGLE`: sudut garis dalam derajat.

Nilai posisi menggunakan rentang relatif terhadap dimensi video. Perubahan konfigurasi diterapkan setelah aplikasi dijalankan ulang.

## Catatan

- Akurasi penghitungan dipengaruhi kualitas stream, pencahayaan, posisi kamera, dan hasil tracking.
- `TARGET_FPS` merupakan target pembatas laju pemrosesan, bukan jaminan FPS aktual.
- SQLite cocok untuk penggunaan awal atau satu proses penulis. Untuk banyak kamera atau beban tinggi, pertimbangkan database server.
- Jangan mengekspos API ke internet tanpa autentikasi, pembatasan akses, dan konfigurasi keamanan yang memadai.

## Lisensi

Tambahkan informasi lisensi sesuai kebutuhan proyek.
