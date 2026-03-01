# 🌿 Green Habitat Certification

> AI-powered environmental livability certification for any residential area in India.
> One location input → real-time data → Peace Index Score → Satellite View.

---

## 🛰️ What is Green Habitat?

Green Habitat evaluates how peaceful and environmentally healthy a neighbourhood is by fetching real-time data from 6 parallel services and returning a **Peace Index Score (0–100)** with a certification tier and **Sentinel-2A/2B satellite imagery**.

Just type a location name. Get a full environmental report in under 3 seconds.

---

## ✅ Example API Response

> Works with **any location** — area name, society name, city, or pincode anywhere in the world.

**Try these examples:**
```
http://127.0.0.1:8000/rate-area?location=Sector 62 Noida
http://127.0.0.1:8000/rate-area?location=Koramangala Bangalore
http://127.0.0.1:8000/rate-area?location=Bandra Mumbai
http://127.0.0.1:8000/rate-area?location=Connaught Place Delhi
http://127.0.0.1:8000/rate-area?location=400001
```

**Sample response:**
```json
{
  "location": "Sector 62 Noida",
  "coordinates": { "lat": 28.6211, "lon": 77.3643 },
  "peace_score": 77.87,
  "certification": "Green Certified",
  "parameters": {
    "greenery_score": 100.0,
    "aqi_score": 39.2,
    "traffic_score": 82.0,
    "crowd_density_score": 88.5,
    "noise_score": 83.95
  },
  "data_sources": {
    "greenery": "overpass_osm",
    "aqi": "waqi",
    "traffic": "overpass_osm",
    "crowd_density": "overpass_osm",
    "noise": "derived",
    "satellite": "sentinel-2_2024-11-15"
  },
  "satellite_image_url": "https://...",
  "ndvi_value": 0.52,
  "satellite_source": "sentinel-2_2024-11-15"
}
```

---

## 🏅 Certification Tiers

| Score | Certification |
|-------|--------------|
| 85–100 | 🥇 Platinum Peace Zone |
| 70–84 | 🌿 Green Certified |
| 55–69 | 🟡 Moderate Living |
| < 55 | 🔴 Urban Stress Area |

---

## 📁 Project Structure

```
green_habitat/
├── main.py                        # Uvicorn entry point
├── requirements.txt
├── .env                           # API keys (never commit this)
├── .env.example                   # Template for .env
├── index.html                     # Frontend dashboard
├── tests/
│   └── test_scoring.py
└── app/
    ├── main.py                    # FastAPI app + CORS middleware
    ├── routers/
    │   └── rating.py              # GET /rate-area endpoint
    ├── services/
    │   ├── geocoding.py           # OSM Nominatim → lat/lon
    │   ├── aqi.py                 # WAQI API → air quality score
    │   ├── greenery.py            # Overpass API → green cover score
    │   ├── traffic.py             # Overpass API → road density score
    │   ├── crowd_density.py       # Overpass API → POI density score
    │   ├── noise.py               # Derived from traffic + crowd
    │   └── satellite.py           # Copernicus Dataspace → Sentinel-2A/2B
    ├── models/
    │   └── schemas.py             # Pydantic response models
    └── utils/
        └── scoring.py             # Peace score formula + certification
```

---

## 🚀 Quickstart (Windows)

### 1. Clone the repo

```cmd
git clone https://github.com/your-username/green-habitat.git
cd green-habitat
```

### 2. Create virtual environment

```cmd
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```cmd
pip install -r requirements.txt
pip install python-dotenv
```

### 4. Set up environment variables

Create a `.env` file in the root folder:

```
WAQI_API_TOKEN=your_waqi_token_here
OPENAQ_API_KEY=your_openaq_key_here
GOOGLE_MAPS_KEY=your_google_maps_key_here
```

> All keys are optional but recommended for live data.
> Get WAQI token free at: https://aqicn.org/data-platform/token/
> Get Google Maps key free at: https://console.cloud.google.com/

### 5. Run the API server

```cmd
uvicorn app.main:app --reload
```

Server starts at: `http://127.0.0.1:8000`

### 6. Open the frontend

Double click `index.html` in the project folder — opens in browser.

---

## 📡 API Reference

### `GET /rate-area`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| location | string | ✅ | Area name, society, pincode, or city |

#### Example Request

```
GET http://127.0.0.1:8000/rate-area?location=Sector 62 Noida
```

#### Interactive Docs

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

---

## 🧮 Scoring Formula

```
Peace Score =
  0.30 × greenery_score
+ 0.25 × aqi_score
+ 0.20 × traffic_score
+ 0.15 × crowd_density_score
+ 0.10 × noise_score
```

**Noise** is derived (no external API):
```
noise_score = 0.70 × traffic_score + 0.30 × crowd_density_score
```

---

## 🛰️ Satellite & NDVI

Sentinel-2A (2015) and Sentinel-2B (2017) are ESA satellites providing:
- 13-band multispectral imagery
- 10 m/pixel resolution
- 5-day revisit cycle over any location

**Bands used:**
- B4 — Red (665 nm)
- B8 — Near-Infrared (842 nm)

**NDVI Formula:**
```
NDVI = (B8 - B4) / (B8 + B4)
```

| NDVI Value | Meaning |
|------------|---------|
| > 0.6 | Dense vegetation 🌿 |
| 0.2 – 0.6 | Sparse / moderate greenery |
| < 0.2 | Urban / bare land 🏙️ |

Source: **Copernicus Dataspace API** (ESA) — free, no account needed.

---

## 🔌 Data Sources

| Parameter | Primary Source | Fallback |
|-----------|---------------|---------|
| Geocoding | OSM Nominatim | 404 error |
| AQI | WAQI API | OpenAQ v3 → Mock |
| Greenery | Overpass API (OSM) | Mock (seeded) |
| Traffic | Overpass API (OSM) | Mock (seeded) |
| Crowd Density | Overpass API (OSM) | Mock (seeded) |
| Noise | Derived | — |
| Satellite | Copernicus Dataspace (Sentinel-2A/2B) | Google Maps → OSM |

> All mock fallbacks are **deterministically seeded** from coordinates — same location always returns same mock score.

---

## 🔧 Environment Variables

| Variable | Description | Get it free at |
|----------|-------------|---------------|
| `WAQI_API_TOKEN` | Live AQI for India | aqicn.org/data-platform/token |
| `OPENAQ_API_KEY` | AQI fallback | explore.openaq.org/register |
| `GOOGLE_MAPS_KEY` | Satellite image | console.cloud.google.com |

---

## 🧪 Running Tests

```cmd
pytest tests/ -v
```

---

## 🗺️ Future Roadmap

- Phase 2 — AI satellite scoring using CNN on all 13 Sentinel-2 bands (AMD ROCm)
- Phase 3 — Real-time IoT sensor fusion (AMD Xilinx Alveo FPGAs)
- Phase 4 — Consumer mobile app (React Native)
- Phase 5 — B2B API for 99acres, MagicBricks, NoBroker
- Phase 6 — Historical trend analysis with 5-year NDVI tracking

---

## 👨‍💻 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI, Uvicorn |
| Async HTTP | HTTPX, asyncio.gather() |
| Validation | Pydantic v2 |
| Geocoding | OSM Nominatim |
| Air Quality | WAQI API, OpenAQ v3 |
| Spatial Data | Overpass API (OpenStreetMap) |
| Satellite | Sentinel-2A/2B via Copernicus Dataspace API |
| Frontend | Vanilla HTML/CSS/JS |
| Testing | Pytest |

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

*Built with 💚 for AMD Slingshot Hackathon*
