# 📦 ML-Powered Dispatch & Storage Optimization API

A production-ready **Django + DRF-based REST API** that uses Machine Learning to automate and optimize **product dispatch, vehicle assignment, and warehouse SOP planning**. Built for logistics-heavy workflows like pharmaceutical or retail warehouse operations.

---

## 🚀 Core Features

- 🔍 **Priority Scoring** using ML models trained on expiry, fragility, temperature sensitivity, and urgency
- 🧠 **Clustering & Load Classification** to determine optimal dispatch strategies
- 🚚 **Vehicle Assignment Engine** that simulates real-world truck capacity and property constraints
- 📊 **SOP Zone Assignment** with Q-learning logic (Reinforcement Learning)
- 🧼 **Automatic Data Cleaning & Enrichment** (expiry days, volume/weight, etc.)
- 🔄 **Master Product File Management** for reusable warehouse-wide context

---

## 🧩 Tech Stack

- **Backend**: Django, Django REST Framework
- **ML**: Scikit-learn (joblib + pickle models), KMeans, LabelEncoder
- **Utils**: Pandas, NumPy
- **API Middleware**: CORS, JSON-only API, Modular Views
- **Deployment**: WSGI-ready, Docker-ready architecture

---

## 📂 Folder & File Structure

```
.
├── core/
│   ├── dispatch.py           # 🚚 Vehicle assignment using ML logic
│   ├── ml_utils.py           # 🧠 Load model + predict priority
│   ├── file_handler.py       # 📄 File I/O + preprocessing logic
│   ├── views.py              # 🎯 API endpoint logic
│   ├── urls.py               # 🔗 Route registration
│   └── templates/            # 📄 Frontend (optional)
├── mlserver/
│   ├── settings.py           # ⚙️ Core config
│   ├── urls.py               # 🔗 App-level route mount
│   └── wsgi.py               # 🔥 WSGI server entrypoint
├── models/
│   └── Dispatch/             # 🧠 ML models: Priority + Clustering
├── assets/
│   └── products.csv          # 📦 Master product file
```

---

## 🔁 API Endpoints

### `/api/dispatch/`  
📦 **Assigns vehicles to product batches based on clustering and ML scoring.**

**Input JSON:**
```json
{
  "columns": [...],
  "data": [...]
}
```

**Response:**
- Cluster ID
- ML Priority Score
- Load Type (N, F, T, TF)
- Assignment Status
- Assigned Vehicle ID

---

### `/api/sop/`  
🧠 **RL-based SOP zone optimizer for warehouse layout.**

- **POST**: Submit product layout data for SOP optimization
- **GET**: Retrieve last processed SOP result

---

### `/api/upload-master/`  
📥 Upload master CSV containing metadata for products (used to enrich predictions).

---

### `/api/data/`  
🎯 Unified handler for:
- Direct JSON payloads
- React-formatted table submissions
- Uploaded CSVs

Performs auto-enrichment, expiry computation, urgency tagging, ML prediction.

---

## 🧠 ML Logic Deep Dive

### 1. **Priority Score Model (`priority_score_model.pkl`)**
Predicts a score based on:
- Expiry days left
- Urgent flag
- Fragile and temperature sensitivity

Used for clustering and sorting priority dispatch.

### 2. **Clustering Model (`knn_model.pkl`)**
Groups orders based on:
- Weight, Volume
- ML score
- Fragile/Temperature tag

Helps in grouping and dispatch bucket creation.

### 3. **Vehicle Assignment**
- Simulates truck pool with different capacities
- Tags load type:
  - `TF`: Temp + Fragile
  - `F`: Fragile only
  - `T`: Temp only
  - `N`: Normal
- Filters and assigns from available pool (based on capacity & flags)

---

## 📐 Sample Workflow

1. **Upload master** via `/api/upload-master/`
2. Send enriched data to `/api/data/`
3. Output contains:
   - Predicted Priority
   - Weight, Volume
   - Load Type classification
4. Send enriched + cleaned payload to `/api/dispatch/`
5. Receive vehicle assignments with dispatch optimization

---

## ✅ Requirements

Install required packages with:

```bash
pip install -r requirements.txt
```

Basic stack:
- `Django`
- `djangorestframework`
- `pandas`
- `scikit-learn`
- `joblib`
- `corsheaders`

---

## ⚙️ Run Locally

```bash
# Start Django server
python manage.py runserver
```

Backend will be live at:  
`http://127.0.0.1:8000/api/dispatch/`  
`http://127.0.0.1:8000/api/data/`  
`http://127.0.0.1:8000/api/sop/`

---

## 🧪 Testing

Use **Postman** or your React frontend to test the endpoints.
