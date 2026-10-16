# SmartAgroGuard - Backend API

High-performance AI & Agronomic Intelligence backend built with FastAPI, PyTorch, MongoDB Atlas, and Motor. Powers real-time crop disease diagnosis, phenological growth tracking, agro-climatic weather radar, and actionable agronomic prescriptions.

---

## 🌟 Key Features

1. **AI Disease Diagnosis & Growth Stage Classification**:
   - PyTorch deep learning models for maize/corn foliar pathology and stage detection.
   - Fallback and multimodal analysis pipelines.

2. **Agronomic Decision Engine**:
   - Rule-based diagnostic triage for moisture deficit, nutrient deficiency, and pathology.
   - Dynamic chemical & fertilizer dilution calculator with safety intervals.

3. **Temporal Lifecycle Analytics (Module 4)**:
   - Longitudinal crop growth curves (height vs. DAS benchmark).
   - Pathology timeline tracking, recovery indexing, and persistence verification.

4. **Weather & Agro-Climatic Intelligence**:
   - 5-day agro-meteorological forecasting with safe spraying window computation.
   - Agro-climatic normal comparison by district and agro-climatic zone.

5. **MongoDB Atlas Integration**:
   - High-throughput asynchronous persistence using `motor` with automated indexing.

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10+ (tested with Python 3.10 - 3.14)
- MongoDB instance (Local or MongoDB Atlas)

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/vivekdesai306-oss/smartagroguard-backend.git
cd smartagroguard-backend

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env` and fill in your MongoDB Atlas connection details:
```bash
cp .env.example .env
```

Edit `.env`:
```env
MONGODB_URL=mongodb+srv://<username>:<password>@cluster0.l1e0rzy.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=agroguard
JWT_SECRET_KEY=your_secret_key_here
```

### 4. Database Seeding & Initialization
To initialize benchmark rules, agro-climatic normals, and required indexes:
```bash
python seed_db.py
```

### 5. Running the Backend Server
```bash
uvicorn app.main:main --reload --port 8000
```

- API Base: `http://localhost:8000`
- Interactive Swagger Documentation: `http://localhost:8000/docs`
- Redoc Documentation: `http://localhost:8000/redoc`

---

## 📂 Project Architecture

```
backend/
├── app/
│   ├── main.py               # FastAPI entrypoint, middleware, routers
│   ├── config.py             # App settings and environment loading
│   ├── database.py           # Async Motor MongoDB connection pool
│   ├── weather_config.py     # Weather and agro-climatic constants
│   ├── ml_models/            # PyTorch model weights (.pt)
│   ├── routers/              # API Route handlers (auth, farms, scans, weather, history)
│   ├── schemas/              # Pydantic validation models
│   ├── services/             # Core business logic, ML inference, triage engine
│   └── data/                 # Seed datasets and static reference charts
├── uploads/                  # Temporary image scan cache
├── seed_db.py                # Database seeder and index manager
├── verify_backend.py         # Healthcheck script
└── requirements.txt          # Python dependencies
```

---

## 🔒 Security
Sensitive database credentials, JWT secrets, and local user uploads are excluded from version control via `.gitignore`.
