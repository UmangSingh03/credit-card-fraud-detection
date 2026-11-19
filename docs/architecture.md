# AegisGuard Architecture & Technical Specification

## 1. System Overview

AegisGuard is an enterprise-grade, real-time credit card fraud detection system designed to deliver sub-10ms inference latencies, explainable AI diagnostics (SHAP), and proactive anomaly detection on massive transaction streams.

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

## 2. Machine Learning Architecture

### 2.1 Preprocessing & Data Leakage Prevention
- **Split Timing**: Stratified split (70% train, 10% validation, 20% test) is performed **before** any transformations.
- **Scaling**: `StandardScaler` is fitted strictly on the training partition and applied to validation and test partitions.
- **SMOTE Balancing**: Applied exclusively to training fold features and labels. The test set retains the pristine 0.17% natural fraud prevalence.

### 2.2 Supervised Classifier Benchmarking
The system evaluates 5 algorithms:
1. **Random Forest Classifier**: Champion model as established in Paper 1 (Borketey 2024), achieving highest PR-AUC and robust ensemble stability across PCA features.
2. **XGBoost Classifier**: Fast gradient-boosted decision tree baseline with sub-millisecond inference.
3. **HistGradientBoosting**: Scikit-learn's modern histogram-based boosting algorithm.
4. **Decision Tree Classifier**: Interpretable single-tree baseline.
5. **Logistic Regression**: Linear baseline with balanced class weights.

### 2.3 Unsupervised Anomaly Detection
- **Isolation Forest**: Trained strictly on legitimate (`Class == 0`) transactions.
- Provides orthogonal signal: measures whether a transaction deviates from typical consumer behaviors even if historical labeled fraud patterns have not observed it before.

---

## 3. Explainability Engine (SHAP)
- Local feature explanations are computed via `TreeExplainer`.
- Deconstructs fraud probabilities into additive contributions:
  $$\hat{f}(x) = \phi_0 + \sum_{i=1}^{M} \phi_i$$
- Identifies features driving risk upward (e.g. extreme negative values in V14, positive spikes in V4) versus features neutralizing suspicion.

---

## 4. Alert Lifecycle & Triage
- **PENDING**: New alert emitted by model engine.
- **ACKNOWLEDGED**: Analyst claims the case for manual investigation.
- **RESOLVED**: Verified outcome recorded (`confirmed_fraud: true | false`) with investigator notes.
- **DISMISSED**: Inconsequential or duplicate alert closed.
