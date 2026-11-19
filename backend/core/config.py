"""
Application configuration using Pydantic Settings.
Reads from environment variables and .env file.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


BASE_DIR = Path(__file__).resolve().parent.parent.parent  # project root


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_env: str = Field(default="development")
    log_level: str = Field(default="INFO")

    # --- Server ---
    backend_host: str = Field(default="0.0.0.0")
    backend_port: int = Field(default=8000)
    frontend_origin: str = Field(default="http://localhost:5173")

    # --- Database ---
    database_url: str = Field(default="sqlite:///./fraud_detection.db")

    # --- ML Paths ---
    data_raw_path: Path = Field(default=BASE_DIR / "data" / "raw" / "creditcard.csv")
    model_dir: Path = Field(default=BASE_DIR / "backend" / "models")
    reports_dir: Path = Field(default=BASE_DIR / "backend" / "reports")

    # --- Simulation ---
    default_sim_interval_seconds: float = Field(default=1.0)
    default_sim_batch_size: int = Field(default=1)

    # --- Risk Thresholds (fraud probability 0.0–1.0) ---
    # Transactions below low_threshold are LOW risk.
    # Transactions above high_threshold are HIGH risk.
    # Between them is MEDIUM risk.
    # These are project-defined policy thresholds, not scientific boundaries.
    risk_low_threshold: float = Field(default=0.30)
    risk_high_threshold: float = Field(default=0.70)

    # --- Training ---
    random_seed: int = Field(default=42)
    max_concurrent_training_jobs: int = Field(default=1)

    # --- Dataset ---
    expected_dataset_rows_min: int = Field(default=280000)
    expected_feature_columns: list[str] = Field(
        default=[
            "Time", "V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9",
            "V10", "V11", "V12", "V13", "V14", "V15", "V16", "V17", "V18",
            "V19", "V20", "V21", "V22", "V23", "V24", "V25", "V26", "V27",
            "V28", "Amount", "Class"
        ]
    )

    def get_model_path(self, filename: str) -> Path:
        return self.model_dir / filename

    def get_report_path(self, filename: str) -> Path:
        return self.reports_dir / filename


# Singleton instance
settings = Settings()

# Ensure model and reports directories exist
settings.model_dir.mkdir(parents=True, exist_ok=True)
settings.reports_dir.mkdir(parents=True, exist_ok=True)
