# Dashboard Eksekutif Pemantauan Fluktuasi Harga Pangan & Deteksi Dini Inflasi Daerah

**Studi Kasus:** Dinas Ketahanan Pangan Provinsi Bengkulu
**Mata Kuliah:** Human-Computer Interaction (HCI) & Data Visualization
**Teknologi:** Python · Streamlit · Pandas · NumPy · Plotly

> Dashboard interaktif yang dirancang dengan pendekatan *User-Centered Design* agar pimpinan bidang distribusi pangan dapat mengenali komoditas dan wilayah bermasalah dalam hitungan menit, bukan jam.
>
> **Catatan:** seluruh data pada proyek ini adalah **data simulasi (sintetis)** untuk keperluan akademik. Nilai HET dan nama pasar bersifat ilustratif.

**Referensi teori:** materi kuliah praktisi Dr. Arafat Febriandirza (BRIN).

---

## Daftar Isi

1. [Latar Belakang Studi Kasus](#1-latar-belakang-studi-kasus)
2. [Dokumen User Persona](#2-dokumen-user-persona)
3. [Skenario Penggunaan](#3-skenario-penggunaan)
4. [Fitur Utama](#4-fitur-utama)
5. [Pemetaan Teori HCI & Visualisasi Data ke Dalam Kode](#5-pemetaan-teori-hci--visualisasi-data-ke-dalam-kode)
6. [Dataset Simulasi](#6-dataset-simulasi)
7. [Struktur Proyek](#7-struktur-proyek)
8. [Cara Menjalankan Aplikasi](#8-cara-menjalankan-aplikasi)
9. [Kustomisasi](#9-kustomisasi)
10. [Keterbatasan](#10-keterbatasan)
11. [Referensi](#11-referensi)

---

## 1. Latar Belakang Studi Kasus

Harga pangan strategis seperti beras, cabai merah, bawang merah, minyak goreng, telur ayam, dan daging ayam adalah penyumbang utama inflasi daerah. Di Provinsi Bengkulu, lonjakan harga komoditas hortikultura (terutama cabai dan bawang) dapat terjadi cepat dan tidak merata antar kabupaten/kota karena perbedaan pasokan, jarak distribusi, dan musim.

Dinas Ketahanan Pangan perlu memantau harga harian terhadap **Harga Eceran Tertinggi (HET)** dan memutuskan intervensi seperti **operasi pasar** sebelum lonjakan merembet ke inflasi. Dalam praktiknya, tantangan yang sering muncul adalah:

- data harga dan stok tersebar di banyak spreadsheet dan laporan pesan singkat;
- tampilan data yang padat memaksa pengambil keputusan menghitung dan membandingkan sendiri;
- tidak ada penanda otomatis untuk harga yang sudah melewati batas;
- waktu pengambilan keputusan sangat terbatas (misalnya sebelum rapat koordinasi pagi).

Proyek ini menjawab masalah tersebut dengan sebuah **dashboard eksekutif** yang menekankan kemudahan penggunaan (HCI) dan kejujuran visualisasi (Data Visualization): ringkasan dulu, rincian kemudian, dan perhatian pengguna diarahkan otomatis ke hal yang benar-benar kritis.

**Ambang keputusan yang digunakan**

| Status | Kriteria harga terhadap HET |
|---|---|
| Normal | ≤ +5% |
| Waspada | > +5% s.d. +15% |
| **Kritis** | **> +15%** (ditandai merah menyala) |

---

## 2. Dokumen User Persona

> Persona bersifat **fiktif** dan disusun untuk keperluan akademik.

### Ibu Ratna Kusumawati, S.P., M.Si. — Kepala Bidang Distribusi Pangan

| Aspek | Uraian |
|---|---|
| **Demografi** | Perempuan, 47 tahun; pendidikan S2 Agribisnis; 21 tahun sebagai ASN; berkantor di Kota Bengkulu; Kepala Bidang Distribusi Pangan, Dinas Ketahanan Pangan Provinsi Bengkulu. |
| **Literasi digital** | Menengah: nyaman dengan WhatsApp, e-mail, dan Excel dasar; belum terbiasa dengan analisis data lanjutan. |
| **Perangkat** | Laptop kantor (utama) dan smartphone Android. |

**Goals**
- Mengetahui dalam kurang dari 5 menit komoditas dan wilayah mana yang melampaui HET.
- Menentukan prioritas lokasi operasi pasar secara cepat dan berbasis data.
- Menyiapkan bahan paparan ringkas untuk rapat koordinasi pengendalian inflasi daerah.
- Mendeteksi dini potensi kenaikan inflasi sebelum rilis resmi bulanan.

**Pain Points**
- Data tersebar di banyak spreadsheet dan laporan WhatsApp petugas pasar.
- Grafik yang padat membuatnya sulit menemukan masalah utama.
- Tidak ada penanda otomatis untuk harga yang melewati batas.
- Waktu terbatas dan khawatir salah membaca angka di depan pimpinan.

**Behavior**
- Membuka laporan pada pagi hari sebelum rapat.
- Menyukai tampilan ringkas dengan angka besar dan penanda warna.
- Sering mengirim tangkapan layar ke grup koordinasi.
- Mendelegasikan analisis mendalam kepada staf.

---

## 3. Skenario Penggunaan

| Unsur | Uraian |
|---|---|
| **Context** | Senin pagi, 30 menit sebelum rapat koordinasi pengendalian inflasi daerah. Ibu Ratna membuka dashboard di laptop kantor. |
| **Trigger** | Kepala Dinas mengirim pesan WhatsApp tentang keluhan kenaikan harga cabai di pasar. |
| **Action** | (1) Membaca 4 KPI Card di bagian atas; (2) melihat kartu *Wilayah Prioritas Operasi Pasar*; (3) memilih komoditas fokus **Cabai Merah**; (4) mengamati titik-titik merah pada grafik tren; (5) mengarahkan kursor ke titik merah untuk membaca rekomendasi tindakan; (6) membuka tabel rincian komoditas kritis; (7) mengambil tangkapan layar untuk paparan. |
| **Outcome** | Dalam kurang dari 5 menit ia memutuskan menggelar operasi pasar di wilayah prioritas dan memiliki bahan paparan yang siap dipakai, sehingga keputusan didasarkan pada data, bukan perkiraan. |

---

## 4. Fitur Utama

- **4 KPI Card** pada bagian paling atas: Komoditas Status Kritis, Rata-rata Perubahan Harga, Wilayah Prioritas Operasi Pasar, dan Status Ketersediaan Stok.
- **Sidebar filter interaktif**: wilayah/pasar, komoditas, rentang tanggal, dan tombol **Reset Filter**.
- **Komoditas fokus** yang otomatis memilih komoditas paling jauh di atas HET.
- **Tiga grafik Plotly**:
  - *Line chart* tren harga harian terhadap garis HET dan ambang kritis;
  - *Horizontal bar chart* selisih harga terhadap HET antar wilayah;
  - *Scatter plot* hubungan stok pasokan (ton) dengan harga (Rp), lengkap dengan garis tren dan koefisien korelasi.
- **Tooltip kaya informasi** (harga presisi, selisih HET, stok, rekomendasi tindakan) yang hanya muncul saat hover/klik.
- **Pewarnaan otomatis**: biru/abu lembut untuk data normal, **merah menyala** untuk data > +15% di atas HET.
- **Tab "Dokumentasi Prinsip HCI & User Persona"** di dalam aplikasi.
- **Tabel rincian dan unduhan CSV** dalam panel yang tertutup secara bawaan.

---

## 5. Pemetaan Teori HCI & Visualisasi Data ke Dalam Kode

### 5.1 Cognitive Load Theory

| Jenis beban | Wujud implementasi | Lokasi pada kode |
|---|---|---|
| **Intrinsic** (kompleksitas inheren data: 6 komoditas × 5 wilayah × 90 hari) | *Chunking*: 4 KPI Card sebagai ringkasan; satu komoditas fokus untuk grafik detail. | `hitung_kpi()`, `render_kpi()`, selectbox `fokus_komoditas` |
| **Extraneous** (beban akibat desain buruk) | Tanpa grid, tanpa legenda terpisah, tanpa dekorasi; detail disembunyikan dalam tooltip dan expander; hanya satu warna alarm. | `_tata_letak_dasar()`, `HOVER_TEMPLATE`, `st.expander` |
| **Germane** (beban yang membantu belajar) | Urutan baca konsisten (Overview → Zoom & Filter → Details), kalimat ringkasan di atas grafik, kode warna konsisten. | `render_dashboard()` |

### 5.2 Preattentive Attributes

| Atribut | Implementasi | Lokasi pada kode |
|---|---|---|
| **Hue (warna)** | Biru/abu untuk normal; merah `#FF1F1F` otomatis hanya untuk `selisih_pct > 15`. | `WARNA_*`, `grafik_tren()`, `grafik_selisih()`, `grafik_scatter()` |
| **Ukuran & intensitas** | Titik kritis lebih besar dan lebih pekat daripada titik normal. | `grafik_scatter()` |
| **Panjang & posisi** | Bar diurutkan dari selisih tertinggi sehingga prioritas langsung terlihat. | `grafik_selisih()` |
| **Pola garis** | Garis putus-putus untuk HET, garis titik-titik untuk ambang kritis. | `add_hline()` pada `grafik_tren()` |

### 5.3 Psikologi Gestalt

| Hukum | Implementasi |
|---|---|
| **Proximity** | KPI Card berdekatan sebagai satu kelompok; grafik bar dan scatter berdampingan. |
| **Similarity** | Warna yang sama untuk kategori yang sama (biru = normal, merah = kritis) di seluruh grafik. |
| **Figure-ground** | Garis tiap wilayah abu-abu sebagai latar; rata-rata biru tebal dan titik merah sebagai figur. |
| **Continuity** | Garis tren dan garis HET horizontal memandu mata mengikuti alur data. |
| **Closure** | Grafik tanpa kotak/bingkai; otak melengkapi batas area plot. |
| **Common region** | Border pada kartu KPI dan kartu persona mengelompokkan isi. |

### 5.4 Edward Tufte: Data-Ink Ratio & Anti-Chartjunk

| Prinsip | Implementasi | Lokasi pada kode |
|---|---|---|
| Maksimalkan data-ink | Template `simple_white`, `showgrid=False`, latar transparan. | `_tata_letak_dasar()` |
| Hapus chartjunk | Tanpa 3D, gradien, atau ornamen; tombol modebar yang tidak perlu dihapus. | `PLOT_CONFIG` |
| Label langsung | Anotasi pada garis HET/ambang dan nilai di ujung bar; legenda dimatikan. | `add_hline()`, `text=` pada `go.Bar` |
| Integritas grafis (*lie factor*) | Bar chart berbasis garis nol = HET sehingga panjang bar proporsional. | `grafik_selisih()` |
| Pemilihan grafik tepat | Line untuk tren waktu, horizontal bar untuk perbandingan kategori, scatter untuk korelasi dua variabel. | `grafik_tren()`, `grafik_selisih()`, `grafik_scatter()` |

### 5.5 Shneiderman's Visual Information Seeking Mantra

| Tahap | Implementasi | Lokasi pada kode |
|---|---|---|
| **Overview first** | 4 KPI Card di bagian paling atas. | `render_kpi()` dan `hitung_kpi()` |
| **Zoom and filter** | Sidebar filter (wilayah, komoditas, rentang tanggal), Reset Filter, komoditas fokus. | `render_sidebar()` |
| **Details-on-demand** | Tooltip hover/klik berisi angka presisi, selisih HET, stok, dan rekomendasi; tabel rincian di dalam expander. | `HOVER_TEMPLATE`, `st.expander` |

### 5.6 Sepuluh Heuristik Usability Jakob Nielsen

| # | Heuristik | Implementasi |
|---|---|---|
| 1 | Visibility of system status | Baris status filter aktif dan tanggal data terakhir; KPI status stok (Aman / Menipis / Defisit). |
| 2 | Match between system and the real world | Bahasa Indonesia, istilah dinas (HET, operasi pasar), format Rupiah dan angka Indonesia (`fmt_rp`, `fmt_num`). |
| 3 | User control and freedom | Tombol **Reset Filter** (`reset_filter`); filter dapat diubah kapan saja. |
| 4 | Consistency and standards | Kartu KPI seragam; merah selalu berarti kritis; jenis grafik sesuai konvensi. |
| 5 | Error prevention | Rentang tanggal dibatasi min/max; kasus tanggal belum lengkap dan filter kosong ditangani. |
| 6 | Recognition rather than recall | Label langsung pada grafik, semua opsi filter terlihat, tooltip `help=` pada kontrol. |
| 7 | Flexibility and efficiency of use | Komoditas fokus default ke yang paling kritis; pengguna mahir bebas memfilter dan mengunduh CSV. |
| 8 | Aesthetic and minimalist design | Data-ink ratio tinggi; detail disembunyikan sampai diminta. |
| 9 | Help users recognize, diagnose, and recover from errors | Pesan peringatan jelas disertai solusi (pilih minimal satu opsi atau klik Reset Filter). |
| 10 | Help and documentation | Panduan singkat di sidebar dan tab dokumentasi di dalam aplikasi. |

---

## 6. Dataset Simulasi

Dataset dibangkitkan otomatis oleh fungsi `generate_dataset()` setiap aplikasi dijalankan (di-*cache* per hari).

| Dimensi | Isi |
|---|---|
| **Komoditas (6)** | Beras, Cabai Merah, Bawang Merah, Minyak Goreng, Telur Ayam, Daging Ayam |
| **Wilayah (5)** | Kota Bengkulu, Rejang Lebong, Bengkulu Utara, Bengkulu Selatan, Kepahiang (dengan pasar acuan ilustratif) |
| **Periode** | 90 hari terakhir (harian) |
| **Kolom utama** | `tanggal`, `wilayah`, `pasar`, `komoditas`, `satuan`, `harga` (Rp), `het` (Rp), `stok_ton` |

Cara pembangkitan:

1. Harga = HET × faktor wilayah × (rasio dasar + fluktuasi *autoregressive* AR(1) + lonjakan skenario).
2. Beberapa kombinasi wilayah-komoditas diberi **lonjakan terskenario** (misalnya cabai di Kota Bengkulu dan Bengkulu Utara) agar cerita data realistis dan fitur deteksi dini dapat didemonstrasikan; sebagian kecil lainnya mendapat lonjakan kecil acak.
3. Stok turun mengikuti lonjakan harga sehingga hubungan pasokan–harga dapat diamati pada scatter plot.
4. Seed acak tetap (`SEED = 2026`) sehingga hasil dapat direproduksi.

---

## 7. Struktur Proyek

```
.
├── app_dashboard_hci.py   # Aplikasi Streamlit (data, KPI, grafik, dokumentasi)
├── requirements.txt       # Daftar dependensi
└── README.md              # Dokumentasi proyek
```

Ringkasan fungsi utama pada `app_dashboard_hci.py`:

| Fungsi | Peran |
|---|---|
| `generate_dataset()` / `enrich()` | Membangkitkan dan memperkaya dataset sintetis |
| `hitung_kpi()` / `render_kpi()` | Menghitung dan menampilkan 4 KPI Card |
| `render_sidebar()` / `reset_filter()` | Filter interaktif dan tombol Reset |
| `grafik_tren()` / `grafik_selisih()` / `grafik_scatter()` | Tiga grafik Plotly |
| `render_dashboard()` | Menyusun alur Overview → Zoom & Filter → Details |
| `render_dokumentasi()` | Tab Dokumentasi Prinsip HCI & User Persona |

---

## 8. Cara Menjalankan Aplikasi

**Prasyarat:** Python 3.9 atau lebih baru.

```bash
# 1. Clone repositori
git clone https://github.com/<username>/<nama-repositori>.git
cd <nama-repositori>

# 2. (Opsional) Buat virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Pasang dependensi
pip install -r requirements.txt

# 4. Jalankan aplikasi
streamlit run app_dashboard_hci.py
```

Aplikasi akan terbuka otomatis di peramban pada `http://localhost:8501`.

---

## 9. Kustomisasi

Semua parameter penting berada di bagian atas `app_dashboard_hci.py`:

| Konstanta | Fungsi |
|---|---|
| `KRITIS_PCT`, `WASPADA_PCT` | Ambang status kritis dan waspada (% di atas HET) |
| `KOMODITAS` | Daftar komoditas, satuan, HET, volatilitas, dan stok dasar |
| `WILAYAH` | Daftar wilayah/pasar, faktor harga, dan skala stok |
| `SKENARIO_LONJAKAN` | Lonjakan harga terskenario per wilayah-komoditas |
| `WARNA_*` | Palet warna (hanya `WARNA_KRITIS` yang berwarna alarm) |

Untuk memakai data nyata, ganti pemanggilan `generate_dataset()` dengan pembacaan CSV yang memiliki kolom yang sama, lalu panggil `enrich()` pada hasilnya.

---

## 10. Keterbatasan

- Data bersifat simulasi; nilai HET dan nama pasar bersifat ilustratif dan perlu disesuaikan dengan regulasi serta data resmi bila dipakai di dunia nyata.
- Korelasi stok–harga pada scatter plot menggabungkan beberapa wilayah dengan skala stok berbeda, sehingga nilai *r* dapat lebih lemah daripada korelasi di dalam satu wilayah. Korelasi juga bukan bukti sebab-akibat.
- Persona dan skenario adalah rekaan akademik, belum divalidasi lewat wawancara atau uji kebergunaan (*usability testing*) dengan pengguna nyata.

---

## 11. Referensi

- Materi kuliah praktisi Dr. Arafat Febriandirza (BRIN): User-Centered Design, Cognitive Load, Preattentive Attributes, Gestalt, Tufte, Heuristik Nielsen, dan Mantra Shneiderman.
- Cooper, A. (1999). *The Inmates Are Running the Asylum*. Sams. (User persona)
- Sweller, J. (1988). Cognitive load during problem solving: Effects on learning. *Cognitive Science, 12*(2), 257–285.
- Treisman, A. M., & Gelade, G. (1980). A feature-integration theory of attention. *Cognitive Psychology, 12*(1), 97–136.
- Wertheimer, M. (1923). Untersuchungen zur Lehre von der Gestalt II. *Psychologische Forschung, 4*, 301–350.
- Tufte, E. R. (1983). *The Visual Display of Quantitative Information*. Graphics Press.
- Nielsen, J. (1994). *10 Usability Heuristics for User Interface Design*. Nielsen Norman Group.
- Shneiderman, B. (1996). The eyes have it: A task by data type taxonomy for information visualizations. *Proceedings of the IEEE Symposium on Visual Languages*, 336–343.

---

**Disusun oleh:** `<Nama Mahasiswa>` · `<NIM>` · `<Program Studi / Universitas>`
