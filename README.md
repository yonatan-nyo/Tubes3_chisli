# CV Matching System - Tubes 3 Strategi dan Algoritma

Sistem pencarian dan pencocokan CV menggunakan algoritma string matching dengan antarmuka GUI yang user-friendly.

## Algoritma yang Diimplementasikan

### 1. Knuth-Morris-Pratt (KMP)

Algoritma pencarian string yang efisien dengan kompleksitas waktu O(n+m). KMP menggunakan failure function untuk menghindari perbandingan karakter yang tidak perlu ketika terjadi mismatch, sehingga tidak perlu mundur ke awal pattern.

**Keunggulan:**

- Kompleksitas waktu linear O(n+m)
- Tidak pernah mundur pada teks input
- Cocok untuk pencarian pattern yang memiliki prefix yang berulang

### 2. Boyer-Moore (BM)

Algoritma pencarian string yang melakukan pencocokan dari kanan ke kiri pada pattern. Menggunakan dua heuristik: bad character rule dan good suffix rule untuk melompati karakter yang tidak mungkin cocok.

**Keunggulan:**

- Rata-rata lebih cepat dari KMP pada teks besar
- Dapat melompati banyak karakter sekaligus
- Efektif untuk pattern yang panjang

### 3. Aho-Corasick (AC)

Algoritma untuk pencarian multiple pattern secara simultan dalam satu kali pass. Menggunakan struktur data trie dengan failure links.

### 4. Fuzzy Matching

Implementasi pencarian fuzzy menggunakan similarity ratio untuk menangani typo dan variasi penulisan.

## Requirements

### Software Requirements

- Python 3.8+
- MySQL Server 8.0+
- pip (Python package manager)

*Note: Python dependencies terdaftar di `requirements.txt`*

## Instalasi dan Setup

### 1. Clone Repository

```bash
git clone [repository-url]
cd Tubes3_chisli
```

### 2. Setup Virtual Environment dan Install Dependencies

**Aktivasi Virtual Environment:**

```bash
# Windows
python -m venv env
env\Scripts\activate

# Linux/Mac
python3 -m venv env
source env/bin/activate
```

**Install Dependencies:**

```bash
pip install -r requirements.txt
```

### 3. Database Setup

1. Buat database MySQL baru:

```sql
CREATE DATABASE cv_matching_db;
```

2. Import seeding data:

```bash
mysql -u [username] -p cv_matching_db < src/seeding/tubes3_seeding.sql
```

3. Buat file `.env` di direktori root:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=cv_matching_db
```

### 4. Persiapan Data

Pastikan folder berikut ada di dalam direktori `src`:

```
storage/
└── data/
    ├── cv_files/
    └── extracted_text/
```

## Cara Menjalankan Program

**PENTING: Pastikan virtual environment sudah diaktifkan sebelum menjalankan program!**

```bash
# Aktifkan environment terlebih dahulu
env\Scripts\activate  # Windows
# atau
source env/bin/activate  # Linux/Mac

# Jalankan program
flet run src/main.py
```

## Struktur Program

```
src/
├── main.py                 # Entry point aplikasi
├── algorithms/             # Implementasi algoritma string matching
│   ├── kmp.py             # Algoritma KMP
│   ├── boyer_moore.py     # Algoritma Boyer-Moore
│   ├── aho_corasick.py    # Algoritma Aho-Corasick
│   └── fuzzy_matcher.py   # Fuzzy matching
├── core/                   # Core business logic
│   ├── cv_processor.py    # Pengolahan file CV
│   ├── search_engine.py   # Engine pencarian utama
│   └── search_utils.py    # Utility fungsi pencarian
├── gui/                    # Antarmuka pengguna
│   ├── main_window.py     # Window utama
│   ├── components/        # Komponen UI
│   └── pages/            # Halaman aplikasi
├── database/              # Database models dan koneksi
└── seeding/              # Data seeding SQL
```

## Fitur Utama

1. **Manajemen Applicant**: Tambah, edit, dan kelola profil pelamar
2. **Upload CV**: Upload file PDF dan ekstraksi otomatis informasi
3. **Pencarian Cerdas**: Pencarian menggunakan berbagai algoritma string matching
4. **Fuzzy Search**: Toleransi terhadap typo dan variasi penulisan
5. **Multi-threading**: Pencarian parallel untuk dataset besar
6. **Enkripsi Data**: Opsi enkripsi untuk data sensitif

## Cara Penggunaan

1. **Jalankan aplikasi** menggunakan salah satu method di atas
2. **Tambah Applicant** melalui tab "Applicants"
3. **Upload CV** melalui tab "Applications"
4. **Lakukan Pencarian** melalui tab "Search" dengan memilih:
   - Keywords pencarian
   - Algoritma yang diinginkan (KMP/BM/AC/Fuzzy)
   - Parameter pencarian lainnya

## Troubleshooting

### Error Database Connection

- Pastikan MySQL server berjalan
- Periksa kredensial di file `.env`
- Pastikan database sudah dibuat dan di-seed

### Error File Not Found

- Periksa folder `storage/data/cv_files/` sudah ada
- Pastikan file CV yang direferensikan di database tersedia

### Performance Issues

- Untuk dataset besar, aktifkan multiprocessing
- Sesuaikan parameter `max_results` untuk membatasi hasil

### Error ModuleNotFoundError

- Pastikan virtual environment sudah diaktifkan
- Jalankan `pip install -r requirements.txt` dalam environment yang aktif

## Authors

**Kelompok Chisli - Tubes 3 Strategi dan Algoritma**

| Nama | NIM |
|------|-----|
| Yonatan Edward Njoto | 13523036 |
| Benedict Presley | 13523067 |
| Daniel Pedrosa Wu | 13523099 |

Teknik Informatika - Institut Teknologi Bandung

---

*Dibuat sebagai tugas besar mata kuliah Strategi dan Algoritma*
