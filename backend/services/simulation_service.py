"""
Simulation service for streaming real-time credit card transactions.
Streams rows from the credit card dataset or synthetic test stream at configurable intervals.
"""
from __future__ import annotations

import asyncio
from typing import Any, Optional
import pandas as pd

from backend.core.config import settings
from backend.core.logging_config import get_logger
from backend.db.database import SessionLocal
from backend.services.transaction_service import TransactionService
from backend.services.websocket_manager import ws_manager

logger = get_logger(__name__)


class SimulationService:
    """Manages the background transaction simulation worker."""

    def __init__(self) -> None:
        self.is_running: bool = False
        self.is_paused: bool = False
        self.interval_seconds: float = settings.default_sim_interval_seconds
        self.batch_size: int = settings.default_sim_batch_size
        self._task: Optional[asyncio.Task] = None
        self._df_cache: Optional[pd.DataFrame] = None
        self._current_index: int = 0
        self.total_streamed: int = 0
        self.total_fraud_detected: int = 0

    def load_dataset(self) -> bool:
        """Load a sample of transactions to stream."""
        if self._df_cache is not None:
            return True

        path = settings.data_raw_path
        if not path.exists():
            logger.warning(f"Dataset path {path} not found for simulation.")
            return False

        try:
            logger.info(f"Loading simulation dataset from {path}...")
            df = pd.read_csv(path)
            fraud_rows = df[df["Class"] == 1]
            legit_rows = df[df["Class"] == 0].sample(n=min(len(df) - len(fraud_rows), 5000), random_state=settings.random_seed)
            combined = pd.concat([legit_rows, fraud_rows]).sample(frac=1.0, random_state=settings.random_seed).reset_index(drop=True)
            self._df_cache = combined
            logger.info(f"Loaded {len(combined)} transactions ({len(fraud_rows)} fraudulent) for simulation pool.")
            return True
        except Exception as e:
            logger.error(f"Error loading simulation dataset: {e}")
            return False

    async def start(self, interval: Optional[float] = None, batch_size: Optional[int] = None) -> dict[str, Any]:
        """Start streaming transactions."""
        if interval is not None:
            self.interval_seconds = max(0.05, float(interval))
        if batch_size is not None:
            self.batch_size = max(1, int(batch_size))

        if self.is_running:
            if self.is_paused:
                self.is_paused = False
                logger.info("Simulation resumed.")
                await ws_manager.broadcast("simulation_status", self.get_status())
                return {"status": "resumed", **self.get_status()}
            return {"status": "already_running", **self.get_status()}

        if not self.load_dataset():
            return {"status": "error", "message": "Failed to load dataset for simulation."}

        self.is_running = True
        self.is_paused = False
        self._task = asyncio.create_task(self._simulation_loop())
        logger.info(f"Simulation started. Interval: {self.interval_seconds}s, Batch: {self.batch_size}")
        await ws_manager.broadcast("simulation_status", self.get_status())
        return {"status": "started", **self.get_status()}

    async def pause(self) -> dict[str, Any]:
        """Pause simulation streaming."""
        if not self.is_running:
            return {"status": "not_running", **self.get_status()}
        self.is_paused = True
        logger.info("Simulation paused.")
        await ws_manager.broadcast("simulation_status", self.get_status())
        return {"status": "paused", **self.get_status()}

    async def stop(self) -> dict[str, Any]:
        """Stop simulation streaming."""
        self.is_running = False
        self.is_paused = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None
        logger.info("Simulation stopped.")
        await ws_manager.broadcast("simulation_status", self.get_status())
        return {"status": "stopped", **self.get_status()}

    def get_status(self) -> dict[str, Any]:
        """Get current simulation state."""
        state = "STOPPED"
        if self.is_running:
            state = "PAUSED" if self.is_paused else "RUNNING"
        return {
            "state": state,
            "interval_seconds": self.interval_seconds,
            "batch_size": self.batch_size,
            "total_streamed": self.total_streamed,
            "total_fraud_detected": self.total_fraud_detected,
        }

    async def _simulation_loop(self) -> None:
        """Background loop continuously sending transactions."""
        try:
            while self.is_running:
                if self.is_paused:
                    await asyncio.sleep(0.5)
                    continue

                if self._df_cache is None or len(self._df_cache) == 0:
                    break

                batch_records = []
                for _ in range(self.batch_size):
                    row = self._df_cache.iloc[self._current_index].to_dict()
                    self._current_index = (self._current_index + 1) % len(self._df_cache)
                    features = {k: v for k, v in row.items() if k != "Class"}
                    batch_records.append(features)

                with SessionLocal() as session:
                    for feat in batch_records:
                        try:
                            result = await TransactionService.process_transaction(
                                session=session,
                                features=feat,
                                source="simulation",
                                explain=False,
                            )
                            self.total_streamed += 1
                            if result.get("prediction", {}).get("risk_category") == "HIGH":
                                self.total_fraud_detected += 1
                        except Exception as e:
                            logger.error(f"Error processing simulated transaction: {e}")

                await asyncio.sleep(self.interval_seconds)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Unhandled error in simulation loop: {e}")
            self.is_running = False


# Module singleton
simulation_service = SimulationService()
