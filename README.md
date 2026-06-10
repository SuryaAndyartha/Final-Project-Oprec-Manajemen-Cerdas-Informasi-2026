# DustiniaDelixia Groceria

## Overview

Proyek ini merupakan pipeline **ETL (Extract, Transform, Load)** berbasis data
e-commerce dari **Dustinia Groceria**, yang bertujuan untuk menganalisis **performa
pengiriman** secara menyeluruh. Mulai dari rata-rata waktu pengiriman, tingkat
keterlambatan, hingga analisis per wilayah, seller, dan kategori produk — semua
divisualisasikan melalui **dashboard interaktif Metabase**.

Pipeline dibangun menggunakan **Apache Airflow** sebagai orkestrator, **Pandas** untuk
transformasi data, dan **ClickHouse** sebagai data warehouse analitik. EDA awal dilakukan
menggunakan **Apache Spark** di Google Colab untuk memahami kualitas data sebelum
proses transformasi.

---

## Struktur Proyek

```text
.
├── Dockerfile                      # Image Airflow dengan dependensi tambahan
├── docker-compose.yml              # Orkestrasi seluruh service (Airflow, ClickHouse, Metabase)
├── requirements.txt                # Dependensi Python
├── data/                           # Dataset CSV sumber (tidak di-commit ke repo)
├── data_lake/                      # Output pipeline (raw, clean, rejected parquet)
└── src/
    ├── pipeline.py                 # Definisi DAG Airflow
    ├── dags/
    │   ├── extract_data.py         # Tahap Extract: CSV → Parquet
    │   ├── transform_data.py       # Tahap Transform: validasi & pembersihan data
    │   └── load_data.py            # Tahap Load: Parquet → ClickHouse
    ├── eda/
    │   └── DustiniaDelixia_Groceria_EDA.ipynb   # Exploratory Data Analysis (Spark)
    └── sql/                        # Query SQL untuk Metabase dashboard
        ├── 1a.sql – 1d.sql         # Statistik dasar performa pengiriman
        ├── 2a.sql – 2f.sql         # Tren bulanan pengiriman
        ├── 3a.sql – 3b.sql         # Dampak keterlambatan terhadap review
        ├── 4a.sql – 4b.sql         # Analisis lead time per tahap fulfillment
        ├── 5a.sql – 5c.sql         # Analisis geografis per state
        ├── 6a.sql – 6c.sql         # Performa seller
        ├── 7a.sql – 7c.sql         # Analisis per kategori & berat produk
        └── 8a.sql – 8b.sql         # Korelasi biaya pengiriman & keterlambatan
```

---

## Penjelasan Teknis

### Arsitektur

CSV Files → [Extract] → Raw Parquet → [Transform] → Clean Parquet + Rejected Parquet → [Load] → ClickHouse → [Metabase] → Dashboard

Seluruh tahapan dijalankan sebagai DAG harian di **Apache Airflow**.

<img width="1403" height="711" alt="Screenshot 2026-06-10 at 20 40 33" src="https://github.com/user-attachments/assets/ee94dc02-fd57-4b67-8633-68882adf0cef" />


---

### 1. Exploratory Data Analysis (EDA)

Sebelum pipeline dibuat, dilakukan EDA menggunakan **Apache Spark** di Google Colab
terhadap 11 tabel dataset. Temuan utama yang menjadi panduan transformasi:

| Temuan | Tindakan |
|---|---|
| Kolom zip code bertipe integer, bisa kehilangan leading zero | Konversi ke string + zero-fill 5 digit |
| `review_score` bertipe string | Konversi ke integer |
| Terdapat 261.831 baris duplikat di tabel `geolocation` | Drop duplikat |
| 29 koordinat geolokasi di luar wilayah Brazil | Drop baris anomali |
| 1.359 order: `order_delivered_carrier_date < order_approved_at` | Drop sebagai anomali logis |
| 23 order: `order_delivered_customer_date < order_delivered_carrier_date` | Drop sebagai anomali logis |
| Banyak nilai NULL yang wajar (review tanpa komentar, order belum selesai) | Pertahankan apa adanya |

---

### 2. Extract

Seluruh file CSV dibaca menggunakan Pandas dengan semua kolom diperlakukan sebagai string (`dtype=str`) untuk konsistensi, lalu disimpan ke format **Parquet** di data lake.

```python
df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
df.to_parquet(os.path.join(parquet_path, "part-0.parquet"), index=False)
```

---

### 3. Transform

Transformasi dilakukan per tabel dengan logika spesifik masing-masing:

- **`orders`**: Parse timestamp, deteksi & reject anomali urutan waktu (carrier date < approved at, customer date < carrier date).
- **`geolocation`**: Konversi zip code ke string, drop duplikat, drop koordinat di luar batas geografis Brazil (lat: -35 s/d 5, lng: -75 s/d -30).
- **`customers` & `sellers`**: Zero-fill zip code menjadi 5 digit.
- **`products`**: Konversi kolom panjang karakter dari float ke integer.

- **`order_reviews`**: Parse kolom timestamp review.

Data yang tidak lolos validasi disimpan terpisah di folder `rejected_parquet` untuk audit.

```python
# Contoh: reject anomali urutan waktu pada tabel orders
anomaly = carrier_before_approved | customer_before_carrier
rejected = df[anomaly].copy()
df_clean = df[~anomaly].reset_index(drop=True)
```

---

### 4. Load

Data bersih dari `clean_parquet` dimuat ke **ClickHouse** dalam dua fase: pertama membuat/mereset semua tabel, kemudian insert data secara batch.

```python
# Fase 1: Siapkan semua tabel
for name in FILES:
    client.execute(f"CREATE TABLE IF NOT EXISTS groceria.{name} ...")
    client.execute(f"TRUNCATE TABLE groceria.{name}")

# Fase 2: Insert data
for name in FILES:
    df = pq.read_table(parquet_path).to_pandas()
    client.execute(f"INSERT INTO groceria.{name} VALUES", data_tuples)
```

---

## Hasil Analisis & Dashboard

Visualisasi dilakukan melalui **Metabase** yang terhubung ke ClickHouse, menghasilkan dashboard komprehensif dengan beberapa bagian utama:

---

### Performa Pengiriman Secara Keseluruhan

- **Rata-rata waktu pengiriman: 12,62 hari** (median: 10,44 hari)
- **90% pesanan selesai dalam 23,33 hari**
- Distribusi terbesar ada pada rentang **6–10 hari** (~32.000 order)
- Dari 95.097 total order: **87.304 on-time (91,81%)**, **7.793 terlambat (8,19%)**

> Secara keseluruhan performa pengiriman cukup baik, namun masih ada ruang perbaikan terutama pada order dengan waktu >15 hari.

<img width="964" height="832" alt="Screenshot 2026-06-10 at 20 42 49" src="https://github.com/user-attachments/assets/9df4694e-9dd1-4c0e-adfd-ee7ec22b0de7" />

---

### Tren Operasional (2017–2018)

- Rata-rata waktu pengiriman **menurun signifikan** dari ~12 hari (awal 2017) menjadi **~7,67 hari** (Agustus 2018), turun 16,54% dalam 2 bulan terakhir.
- Tingkat on-time delivery **meningkat ke 89,51%** per Agustus 2018, naik 13,84% dibanding titik terendah (Maret 2018: 78,63%).
- **Estimasi pengiriman rata-rata 24,38 hari**, jauh lebih panjang dari aktual 12,56 hari. Gap 11,83 hari menunjukkan **estimasi yang terlalu konservatif**, yang justru bisa menjadi keunggulan (underpromise, overdeliver).

> **Keputusan bisnis**: Estimasi pengiriman dapat diperketat untuk meningkatkan kepercayaan pelanggan tanpa mengorbankan kepuasan.

<img width="962" height="830" alt="Screenshot 2026-06-10 at 20 43 31" src="https://github.com/user-attachments/assets/07e4d25b-91f8-415a-86d3-d87ac0203a21" />

---

### Dampak Keterlambatan terhadap Kepuasan Pelanggan

- Order **on-time**: rata-rata review **4,2/5**
- Order **terlambat**: rata-rata review hanya **2,5/5**

> **Keputusan bisnis**: Keterlambatan pengiriman berdampak besar pada kepuasan pelanggan. Investasi dalam mempercepat pengiriman akan berdampak langsung pada rating dan retensi pelanggan.

<img width="968" height="753" alt="Screenshot 2026-06-10 at 20 44 03" src="https://github.com/user-attachments/assets/423d50f7-69a9-4eaf-936e-257463e194a1" />

---

### Analisis Tahap Fulfillment

Bottleneck utama ada pada tahap **pengiriman ke pelanggan (9,36 hari)**, bukan pada approval (0,4 hari) atau pemrosesan seller (2,85 hari).

Pada order yang **terlambat**, tahap pengiriman ke pelanggan mencapai **25,68 hari** vs hanya 7,91 hari pada order on-time — hampir **3,25× lebih lambat**.

> **Keputusan bisnis**: Optimasi logistik last-mile adalah prioritas utama. Seller processing pada order terlambat (5,35 hari vs 2,63 hari) juga perlu diperhatikan sebagai faktor kontribusi kedua.

<img width="966" height="746" alt="Screenshot 2026-06-10 at 20 44 37" src="https://github.com/user-attachments/assets/0ccd6447-2e85-4e1e-bf55-78a845a5a827" />

---

### Analisis Geografis

- **Waktu pengiriman terlama**: Amazonas (AM) dan Alagoas (AL), masing-masing >24 hari.
- **Waktu pengiriman tercepat**: São Paulo (SP), ~8 hari (volume terbesar, ~40.000 order).
- **Tingkat keterlambatan tertinggi**: Alagoas (AL) 23,7%, Maranhão (MA) 20,2%.
- **Ongkos kirim tertinggi**: Paraíba (PB) dan Rondônia (RO), rata-rata >42 unit.

> **Keputusan bisnis**: Wilayah Timur Laut dan Amazon membutuhkan strategi distribusi khusus — baik melalui gudang regional, kemitraan kurir lokal, atau penyesuaian estimasi pengiriman.

<img width="861" height="919" alt="Screenshot 2026-06-10 at 20 45 10" src="https://github.com/user-attachments/assets/9023b6e7-a480-4ad8-8151-3b9123f3da61" />

---

### Performa Seller

- Sebagian besar seller memiliki **late delivery rate 5–15%** dengan volume order di bawah 300.
- Seller dengan volume tinggi (>500 order) cenderung memiliki **late rate lebih rendah**, menunjukkan efek skala/pengalaman.
- Beberapa seller menunjukkan **seller processing time hingga 10–11 hari**, jauh di atas rata-rata 2,85 hari.

> **Keputusan bisnis**: Perlu program pembinaan atau penalti/reward berbasis SLA untuk seller dengan late rate tinggi dan processing time berlebihan.

<img width="861" height="921" alt="Screenshot 2026-06-10 at 20 45 39" src="https://github.com/user-attachments/assets/8bf49e38-71e3-4b77-90d2-1f3e07e89213" />
<img width="862" height="454" alt="Screenshot 2026-06-10 at 20 45 44" src="https://github.com/user-attachments/assets/c23377fc-a480-481e-9796-c10ead754cee" />

---

### Analisis Produk

- **Furniture kantor (office_furniture)** memiliki waktu pengiriman terpanjang (~21 hari).
- **Kategori dengan late rate tertinggi**: audio, fashion_underwear_beach, christmas_supplies (~13%).
- **Produk berat (>5 kg)** rata-rata butuh ~14 hari, hanya sedikit lebih lama dari produk ringan (<0,5 kg: ~12 hari) — perbedaan tidak terlalu signifikan.

> **Keputusan bisnis**: Kategori dengan late rate tinggi seperti audio dan fashion perlu dievaluasi dari sisi rantai pasok atau pemilihan seller.

<img width="862" height="775" alt="Screenshot 2026-06-10 at 20 46 25" src="https://github.com/user-attachments/assets/823a7887-2b81-44a1-9a39-99139006a730" />
<img width="858" height="370" alt="Screenshot 2026-06-10 at 20 46 33" src="https://github.com/user-attachments/assets/f318e1a3-f6ae-4573-8bfe-e22f0ef33dfa" />

---


## Cara Menjalankan

### Prasyarat
- Docker & Docker Compose

### Langkah

```bash
# 1. Clone repository
git clone <repo-url>
cd <repo-folder>

# 2. Letakkan file CSV dataset di folder data/

# 3. Jalankan seluruh service
docker-compose up -d

# 4. Buka Airflow UI
# http://localhost:8080 (user: admin, pass: admin)

# 5. Trigger DAG: groceria_etl_pipeline

# 6. Buka Metabase
# http://localhost:3000
# Koneksikan ke ClickHouse: host=clickhouse-server, port=8123
# user=admin, pass=rahasia, database=groceria
```

---

## Teknologi yang Digunakan

| Teknologi | Fungsi |
|---|---|
| Apache Airflow | Orkestrasi pipeline ETL |
| Apache Spark | Exploratory Data Analysis |
| Pandas + PyArrow | Transformasi data |
| ClickHouse | Data warehouse analitik |
| Metabase | Visualisasi & dashboard |
| Docker Compose | Manajemen infrastruktur |

--- 

~Terima kasih

```
docker-compose down
```
