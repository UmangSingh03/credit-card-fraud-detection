import { useState, useEffect, useRef, useCallback } from 'react';
import { TransactionItem, AlertItem } from '../types';

interface WebSocketHookReturn {
  isConnected: boolean;
  transactions: TransactionItem[];
  alerts: AlertItem[];
  trainingProgress: { run_id: string; progress_percent: number; current_stage: string } | null;
  clearTransactions: () => void;
  addOptimisticAlert: (alert: AlertItem) => void;
  updateAlertStatus: (alertId: string, status: string, notes?: string, confirmedFraud?: boolean | null) => void;
}

export function useWebSocket(): WebSocketHookReturn {
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [transactions, setTransactions] = useState<TransactionItem[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [trainingProgress, setTrainingProgress] = useState<{
    run_id: string;
    progress_percent: number;
    current_stage: string;
  } | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<any>(null);

  const connect = useCallback(() => {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      // In dev Vite proxies /ws to backend ws://127.0.0.1:8000/ws
      const wsUrl = `${protocol}//${window.location.host}/ws`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          const { type, data } = msg;

          if (type === 'new_transaction') {
            setTransactions((prev) => [data, ...prev.slice(0, 99)]);
          } else if (type === 'new_alert') {
            setAlerts((prev) => [data, ...prev.filter((a) => a.id !== data.id).slice(0, 49)]);
          } else if (type === 'alert_updated') {
            setAlerts((prev) =>
              prev.map((a) => (a.id === data.id ? { ...a, ...data } : a))
            );
          } else if (type === 'training_progress') {
            setTrainingProgress(data);
          } else if (type === 'training_completed') {
            setTrainingProgress(null);
          } else if (type === 'training_failed') {
            setTrainingProgress(null);
          }
        } catch (err) {
          console.error('Error parsing WS message', err);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        reconnectTimeoutRef.current = setTimeout(connect, 2000);
      };

      ws.onerror = () => {
        ws.close();
      };

      wsRef.current = ws;
    } catch (e) {
      setIsConnected(false);
      reconnectTimeoutRef.current = setTimeout(connect, 3000);
    }
  }, []);

  useEffect(() => {
    connect();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connect]);

  const clearTransactions = useCallback(() => {
    setTransactions([]);
  }, []);

  const addOptimisticAlert = useCallback((alert: AlertItem) => {
    setAlerts((prev) => [alert, ...prev]);
  }, []);

  const updateAlertStatus = useCallback(
    (alertId: string, status: string, notes?: string, confirmedFraud?: boolean | null) => {
      setAlerts((prev) =>
        prev.map((a) =>
          a.id === alertId
            ? {
                ...a,
                status: status as any,
                review_notes: notes !== undefined ? notes : a.review_notes,
                confirmed_fraud: confirmedFraud !== undefined ? confirmedFraud : a.confirmed_fraud,
              }
            : a
        )
      );
    },
    []
  );

  return {
    isConnected,
    transactions,
    alerts,
    trainingProgress,
    clearTransactions,
    addOptimisticAlert,
    updateAlertStatus,
  };
}
