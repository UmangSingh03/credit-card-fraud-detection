# AegisGuard | Real-Time Credit Card Fraud Detection System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61dafb.svg)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-6-646CFF.svg)](https://vitejs.dev)
[![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.4%2B-orange.svg)](https://scikit-learn.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An enterprise-grade, real-time AI credit card fraud detection system designed for high-throughput financial environments. AegisGuard implements a dual-engine architecture combining supervised ensemble learning (Random Forest champion) and unsupervised behavioral anomaly detection (Isolation Forest), paired with sub-10ms inference latencies, SHAP local explainability, and full human-in-the-loop alert triage workflows.

---

## 🌟 Key Features

1. **Dual-Engine Detection Pipeline**:
   - **Supervised Champion**: Random Forest classifier trained on SMOTE-balanced training folds (val PR-AUC: 0.749, test PR-AUC: 0.821, recall: 82.65%, false-alarm rate: 0.058%).
   - **Unsupervised Anomaly Detector**: Isolation Forest fitted exclusively on legitimate transactions to catch zero-day and outlier spending patterns.

2. **Sub-10ms Real-Time Inference**:
   - Optimized scoring with sub-millisecond feature validation and transformation.
   - Real-time WebSocket broadcasting for live transaction streams and alert feeds.

3. **Local Explainability (SHAP)**:
   - Automated local feature attribution for all elevated-risk transactions via `TreeExplainer`.
   - Visualizes positive and negative feature pushes that explain why a transaction was flagged.

4. **Human-in-the-Loop Triage Workflow**:
   - Alert lifecycle: `PENDING` &rarr; `ACKNOWLEDGED` &rarr; `RESOLVED` / `DISMISSED`.
   - Auditing notes and fraud outcome confirmation (`confirmed_fraud: true | false`).

5. **Multi-Algorithm Model Benchmark & Retraining Studio**:
   - Automated benchmarking across 5 algorithms: Random Forest, XGBoost, HistGradientBoosting, Decision Tree, and Logistic Regression.
   - Diagnostic curve gallery: Precision-Recall (PR) curves, ROC curves, confusion matrices, and feature importance bar charts.
   - One-click background model retraining with live progress tracking over WebSockets.

6. **Transaction Simulation & CSV Batch Testing**:
   - Built-in transaction streamer that replays Kaggle credit card events at adjustable speeds (1 to 20+ tx/sec).
   - Drag-and-drop CSV batch upload for instant tabular scoring.

---

## 🔬 Research Foundations

The design and objective metrics of AegisGuard directly implement methodologies established in leading academic publications:

- **Paper 1: Borketey (2024)**  
  *Real-Time Fraud Detection Using Machine Learning.* Journal of Data Analysis and Information Processing, 12, 189–209. [DOI: 10.4236/jdaip.2024.122011](https://doi.org/10.4236/jdaip.2024.122011)  
  *Adoption:* Empirically establishes Random Forest superiority for class-imbalanced credit card datasets and prioritizes **PR-AUC** over ROC-AUC.
- **Paper 2: Data Leakage Prevention in Imbalanced Learning**  
  *Adoption:* Strictly isolates preprocessing scalers and SMOTE oversampling to training folds only, maintaining natural 0.17% fraud prevalence on test data.
- **Paper 3: Dual-Engine Defense**  
  *Adoption:* Combines supervised pattern matching with unsupervised anomaly detection to catch uncataloged fraud vectors.

---

## 🏗️ System Architecture

```
                                  [ Incoming Transactions ]
                                   (Live Stream / CSV / API)
                                              │
                                              ▼
                                 ┌─────────────────────────┐
                                 │     FastAPI Ingress     │
                                 │    Payload Validation   │
                                 └────────────┬────────────┘
                                              │
                     ┌────────────────────────┴────────────────────────┐
                     ▼                                                 ▼
        ┌─────────────────────────┐                       ┌─────────────────────────┐
        │  Supervised Classifier  │                       │   Anomaly Detector      │
        │  (Champion: Random      │                       │   (Isolation Forest     │
        │   Forest / XGBoost)     │                       │    Unsupervised)        │
        └────────────┬────────────┘                       └────────────┬────────────┘
                     │                                                 │
            Fraud Probability (0-1)                            Anomaly Score (Unusualness)
                     │                                                 │
                     └────────────────────────┬────────────────────────┘
                                              │
                                              ▼
                                 ┌─────────────────────────┐
                                 │  Risk Threshold Engine  │
                                 │  • LOW:    prob < 0.30  │
                                 │  • MEDIUM: 0.30 - 0.70  │
                                 │  • HIGH:   prob >= 0.70 │
                                 └────────────┬────────────┘
                                              │
                       ┌──────────────────────┴──────────────────────┐
                       │ (If Elevated Risk or Anomaly)               │
                       ▼                                             ▼
        ┌─────────────────────────┐                     ┌─────────────────────────┐
        │    SHAP Local Engine    │                     │   Alert Triage Engine   │
        │  Feature Contributions  │                     │   (CRITICAL / HIGH)     │
        └────────────┬────────────┘                     └────────────┬────────────┘
                     │                                               │
                     └────────────────────────┬──────────────────────┘
                                              │
                     ┌────────────────────────┴────────────────────────┐
                     ▼                                                 ▼
        ┌─────────────────────────┐                       ┌─────────────────────────┐
        │   SQLite Audit Store    │                       │   WebSocket Broadcast   │
        │ (Transactions, Alerts,  │                       │   (To Analyst UI &      │
        │  Predictions)           │                       │    Live Dashboards)     │
        └─────────────────────────┘                       └─────────────────────────┘
```

---

## ⚡ Quick Start

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.10, 3.11, 3.12, 3.14)
- Node.js 18+ and npm

### 2. Installation
```bash
# Clone and enter directory
cd fraud-detection-system

# Install Python dependencies
pip install -r requirements.txt

# Install Frontend dependencies
cd frontend
npm install
npm run build
cd ..
```

### 3. Model Training (Pre-Trained Artifacts Included)
Model artifacts and evaluation curves are already generated and saved in `backend/models/` and `backend/reports/`. To retrain anytime:
```bash
python -m backend.ml.train
```

### 4. Run the Full Application
Start the backend server (which automatically hosts both the API and the compiled React UI):
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser!

*(Optional)* Run the Vite development server independently:
```bash
cd frontend
npm run dev
# Accessible at http://localhost:5173
```

---

## 🧪 Testing

Execute the comprehensive test suite:
```bash
python -m pytest backend/tests/ -v
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/transactions` | Score single transaction in real-time |
| `POST` | `/api/transactions/batch` | Score JSON array of transactions |
| `POST` | `/api/transactions/upload-csv` | Upload and score CSV batch |
| `GET` | `/api/transactions` | List transaction audit history |
| `GET` | `/api/transactions/{id}` | Inspect transaction details & SHAP explanation |
| `GET` | `/api/alerts` | List alerts with status/severity filters |
| `PATCH` | `/api/alerts/{id}` | Update triage status, notes, or fraud confirmation |
| `GET` | `/api/models/active` | Get active model metrics and global feature importances |
| `GET` | `/api/models/comparison` | Get multi-model benchmark evaluation JSON |
| `POST` | `/api/models/train` | Trigger background model training |
| `GET` | `/api/models/reports/{file}` | Fetch evaluation charts (ROC, PR, confusion matrix) |
| `POST` | `/api/simulation/start` | Start live transaction streaming |
| `POST` | `/api/simulation/pause` | Pause transaction stream |
| `POST` | `/api/simulation/stop` | Stop transaction stream |
| `GET` | `/api/dashboard/stats` | Aggregated KPI metrics |
| `WS` | `/ws` | Real-time WebSocket event connection |
