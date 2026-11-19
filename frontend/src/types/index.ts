export interface Prediction {
  id?: string;
  predicted_class: number;
  fraud_probability: number | null;
  risk_category: 'LOW' | 'MEDIUM' | 'HIGH';
  anomaly_score: number | null;
  is_anomalous: boolean | null;
  latency_ms: number | null;
  model_name?: string;
  model_version?: string;
  explanation?: {
    base_value: number;
    prediction_value: number;
    features: {
      feature: string;
      value: number;
      contribution: number;
      direction: 'increases_fraud_risk' | 'decreases_fraud_risk';
    }[];
    note: string;
  } | null;
}

export interface AlertSummary {
  id: string;
  severity: 'HIGH' | 'CRITICAL';
  alert_reason: string;
  status: 'PENDING' | 'ACKNOWLEDGED' | 'RESOLVED' | 'DISMISSED';
}

export interface TransactionItem {
  id?: string;
  transaction_id?: string;
  external_id?: string | null;
  time_seconds?: number;
  amount?: number;
  source?: string;
  created_at: string;
  features?: Record<string, number>;
  prediction?: Prediction | null;
  alert?: AlertSummary | null;
}

export interface AlertItem {
  id: string;
  transaction_id: string;
  prediction_id?: string | null;
  status: 'PENDING' | 'ACKNOWLEDGED' | 'RESOLVED' | 'DISMISSED';
  severity: 'HIGH' | 'CRITICAL';
  alert_reason: string;
  review_notes?: string | null;
  confirmed_fraud?: boolean | null;
  created_at: string;
  updated_at: string;
}

export interface OverviewStats {
  total_transactions: number;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  fraud_rate_pct: number;
  avg_latency_ms: number;
  alerts: {
    total: number;
    pending: number;
    acknowledged: number;
    resolved: number;
    dismissed: number;
  };
  active_model?: {
    name: string;
    version: string;
    pr_auc: number | null;
    roc_auc: number | null;
    f1: number | null;
  } | null;
}

export interface ModelMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  roc_auc: number;
  pr_auc: number;
  false_positive_rate: number;
  latency_ms: number;
  is_selected?: boolean;
}

export interface SimulationStatus {
  state: 'STOPPED' | 'RUNNING' | 'PAUSED';
  interval_seconds: number;
  batch_size: number;
  total_streamed: number;
  total_fraud_detected: number;
}
