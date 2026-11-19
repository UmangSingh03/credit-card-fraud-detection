# Academic Research Grounding & Comparative Analysis

AegisGuard directly implements and validates the empirical methodologies described in contemporary financial machine learning literature.

---

## 1. Paper 1: Borketey (2024)
**Citation:** Borketey, B. (2024). *Real-Time Fraud Detection Using Machine Learning.* Journal of Data Analysis and Information Processing (JDAIP), 12, 189–209. DOI: 10.4236/jdaip.2024.122011.

### Key Contributions & Implementation in AegisGuard:
1. **Benchmark Superiority**:
   - Compares Logistic Regression, Linear Discriminant Analysis, KNN, Decision Tree, Naive Bayes, SVM, Random Forest, XGBoost, and LightGBM.
   - Concludes that **Random Forest** delivers the optimal combination of minority class recovery and low false-alarm frequency.
2. **Metric Prioritization (PR-AUC vs ROC-AUC)**:
   - For severe class imbalance (0.17% fraud prevalence), ROC-AUC is overly optimistic due to large True Negative counts.
   - **Precision-Recall AUC (PR-AUC)** is the primary objective function for champion model selection in AegisGuard.
3. **SMOTE Oversampling**:
   - Synthetic Minority Oversampling Technique creates synthetic fraud vectors along minority class nearest-neighbor lines.
   - AegisGuard enforces strict containment of SMOTE to the training split, preventing validation and test leakage.

---

## 2. Paper 2: Data Leakage Prevention in Imbalanced Learning
**Key Finding:** Many credit card fraud detection benchmarks suffer from methodological flaws, notably fitting scalers or oversamplers across the entire dataset prior to splitting.
- **AegisGuard Solution**:
  1. Split first: 70% train, 10% validation, 20% test.
  2. Fit `StandardScaler` only on training split.
  3. Apply SMOTE exclusively on scaled training features.
  4. Evaluate validation and test sets strictly on natural, unmanipulated distributions.

---

## 3. Paper 3: Hybrid Supervised-Unsupervised Anomaly Defense
**Key Finding:** Supervised models are blind to unprecedented, zero-day fraud vectors.
- **AegisGuard Solution**:
  - Couples the supervised champion model (Random Forest) with an unsupervised **Isolation Forest**.
  - Transactions exhibiting both elevated fraud probability and extreme anomaly scores receive `CRITICAL` triage priority with instant analyst notification.
