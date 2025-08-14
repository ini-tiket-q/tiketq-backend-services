# Trains Service

## Deskripsi
Trains Service adalah microservice untuk TiketQ platform yang menangani pencarian jadwal kereta, manajemen stasiun, dan pemesanan tiket kereta. Service ini terintegrasi dengan provider eksternal seperti KAI Access.

## Arsitektur
Menggunakan pola Ports and Adapters (Hexagonal Architecture):
- **Domain Layer**: Model, service, dan repository interface
- **Adapters Layer**: Integrasi API eksternal dan database
- **Routes Layer**: REST API endpoint

## Definitions of Done
1. Branch `train-service` sudah dibuat
2. Environment variables dikonfigurasi (`.env.example` tersedia)
3. Dependencies terinstall (`pip install -r requirements.txt`)
4. Database PostgreSQL berjalan dan dapat diakses
5. Service dapat dijalankan tanpa error
6. Endpoint `/health` berfungsi
7. README berisi instruksi setup dan penggunaan

## Setup & Instalasi

### 1. Konfigurasi Environment
Salin `.env.example` ke `.env` dan isi sesuai kebutuhan:
```
TRAINS_DB_URL=postgresql://postgres:postgres@localhost:5432/tiketq_db
KAI_API_KEY=your_kai_api_key_here
KAI_API_BASE_URL=https://api.kai.id
PORT=8000
ENV=development
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Jalankan Database
Pastikan PostgreSQL sudah berjalan di host (atau gunakan Docker Compose jika ingin lebih mudah integrasi antar service).

### 4. Build & Run Service (Docker)
```bash
docker build -t trains-service .
docker run -d -p 8000:8000 --env-file .env trains-service
```

### 5. Test Endpoint
```bash
curl http://localhost:8000/health
```
Respon yang diharapkan:
```json
{
  "status": "healthy",
  "service": "trains-service",
  "environment": "development",
  "db_url_present": true,
  "api_key_present": true
}
```

### 6. Troubleshooting
- Jika koneksi database gagal, cek `TRAINS_DB_URL` dan pastikan host/database aktif.
- Untuk Docker Compose, gunakan host `postgres`.
- Untuk docker run manual, gunakan host `localhost` atau IP host.
- Cek log container dengan `docker logs <container_id>` jika service crash.

## API Endpoints

### Train Stations
```http
GET /trains/stations - Get all train stations
GET /trains/stations?search=query - Search stations by name/city
```

### Train Search
```http
POST /trains/search - Search for available trains
```

**Request Body:**
```json
{
  "origin_code": "GMR",
  "destination_code": "BD",
  "departure_date": "2025-01-15",
  "adult_count": 1,
  "infant_count": 0
}
```

### Train Booking
```http
POST /trains/booking - Create a new booking
GET /trains/booking/{booking_id} - Get booking details
POST /trains/booking/{booking_id}/cancel - Cancel a booking
```

## Pengembangan & Testing

- Untuk pengembangan lokal, pastikan environment dan database sudah siap.
- Untuk testing endpoint, gunakan Postman/curl sesuai contoh di atas.
- Untuk integrasi antar service, gunakan Docker Compose agar semua service saling terhubung.

## Catatan
- Untuk deployment/production, pastikan environment variable dan host database sudah disesuaikan.
- Dokumentasi lebih lanjut tersedia di masing-masing folder service.
