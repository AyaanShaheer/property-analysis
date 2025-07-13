---

# 🏭 Industrial Property Analysis System

A robust and intelligent platform for analyzing **industrial properties** and discovering **comparable assets** across **Cook County**, **Dallas County**, and **Los Angeles County**.

<img width="1917" height="977" alt="Screenshot 2025-07-12 230947" src="https://github.com/user-attachments/assets/b4fa1ed9-d875-4d3d-a243-769c85283aa2" />


---

## 🚀 Key Features

### 🔍 API Discovery Engine

* Auto-discovers & maps property data fields
* Intelligent rate-limit handling
* Multi-county API architecture

### 🏗️ Industrial Property Extraction

* Validates property data schema
* Cleans and standardizes fields
* Filters by industrial zoning types (M1, M2, I-1, etc.)

### 📊 Comparable Analysis Engine

* Advanced similarity scoring
* Weighted factor-based comparison
* Generates confidence levels (High, Medium, Low)

---

## 📦 Tech Stack

### Backend

* Python 3.8+
* Flask + Flask-CORS
* aiohttp
* pandas, numpy
* geopy

### Frontend

* Node.js >= 14
* Next.js
* Tailwind CSS

---

## 🛠️ Installation Guide

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/AyaanShaheer/property-analysis.git
cd property-analysis
```

### 2️⃣ Set Up the Backend

```bash
cd backend
python -m venv venv
# Windows
.\venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3️⃣ Set Up the Frontend

```bash
cd frontend
npm install
```

---

## 🚀 Running the Application

### 🖥️ Start the Backend API

```bash
cd backend
.\venv\Scripts\activate  # or source venv/bin/activate
python app.py
```

Backend runs on: [http://localhost:5000](http://localhost:5000)

### 🌐 Start the Frontend

```bash
cd frontend
npm run dev
```

Frontend runs on: [http://localhost:3000](http://localhost:3000)

---

## 📊 API Endpoints

### 🔎 Properties

* `GET /api/properties` → List all properties
* `GET /api/properties/{id}` → Get property by ID

### 🧠 Comparable Analysis

```http
POST /api/analyze/comparables
```

#### Sample Request:

```json
{
  "property_id": "CO0001"
}
```

**OR**

```json
{
  "property_data": {
    "address": "123 Test St",
    "city": "Chicago",
    "county": "Cook County",
    // ... other fields
  }
}
```

---

## ⚖️ Comparable Scoring Criteria

| Factor        | Weight |
| ------------- | ------ |
| Building Area | 30%    |
| Lot Size      | 20%    |
| Age           | 15%    |
| Zoning        | 25%    |
| Location      | 10%    |

### ✅ Confidence Levels

* **High**: score > 0.8
* **Medium**: 0.6 ≤ score ≤ 0.8
* **Low**: score < 0.6

---

## 🧪 Mock Data (Development Mode)

We use mock data by default for:

✅ Offline development
✅ Consistent testing
✅ API rate limit avoidance
✅ Legal compliance (no real PII)

---

## 🔐 Switching to Real APIs (Advanced Setup)

To switch from mock to live APIs:

### 1. Get Access

Apply for API keys from each county's data portal.

```python
API_KEYS = {
    'cook_county': 'your_api_key_here',
    'dallas_county': 'your_api_key_here',
    'los_angeles': 'your_api_key_here'
}
```

### 2. Update API Endpoints

Inside the `APIDiscoveryAgent`:

```python
self.api_endpoints = {
    'cook_county': {
        'url': 'https://datacatalog.cookcountyil.gov/resource/tx8h-7rnu.json',
        'headers': {
            'Authorization': f'Bearer {API_KEYS["cook_county"]}',
            'Content-Type': 'application/json'
        }
    }
    # ... and other counties
}
```

### 3. Respect Rate Limits

Implement retries, exponential backoff, and proper error handling.

### 4. Follow Legal Guidelines

* Review data licensing
* Ensure compliance with terms of service
* Avoid usage of sensitive or restricted data

---

## 🤝 Contributing

1. Fork the repo
2. Create your branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -m "Add awesome feature"`
4. Push to GitHub: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📝 License

Licensed under the [MIT License](./LICENSE.md).

---

## 👨‍💻 Authors

* **Ayaan Shaheer**
  📧 [gfever252@gmail.com](mailto:gfever252@gmail.com)

---

## 🙏 Acknowledgments

* Public Data Portals (Cook County, DCAD, LA County)
* Open Source Contributors
* Python, Flask, Next.js & Tailwind communities

---

