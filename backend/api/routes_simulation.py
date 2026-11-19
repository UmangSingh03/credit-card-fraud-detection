"""
Simulation control endpoints.
"""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter

from backend.api.schemas import SimulationConfigRequest, SimulationStatusResponse
from backend.services.simulation_service import simulation_service

router = APIRouter(prefix="/simulation", tags=["Simulation"])


@router.post("/start", response_model=dict[str, Any])
async def start_simulation(payload: SimulationConfigRequest = SimulationConfigRequest()) -> Any:
    """Start or resume streaming simulated transactions."""
    return await simulation_service.start(
        interval=payload.interval_seconds,
        batch_size=payload.batch_size,
    )


@router.post("/pause", response_model=dict[str, Any])
async def pause_simulation() -> Any:
    """Pause streaming transactions."""
    return await simulation_service.pause()


@router.post("/stop", response_model=dict[str, Any])
async def stop_simulation() -> Any:
    """Stop the simulation."""
    return await simulation_service.stop()


@router.post("/configure", response_model=dict[str, Any])
async def configure_simulation(payload: SimulationConfigRequest) -> Any:
    """Update simulation streaming interval or batch size without stopping."""
    if payload.interval_seconds is not None:
        simulation_service.interval_seconds = max(0.05, payload.interval_seconds)
    if payload.batch_size is not None:
        simulation_service.batch_size = max(1, payload.batch_size)
    return simulation_service.get_status()


@router.get("/status", response_model=SimulationStatusResponse)
def get_simulation_status() -> Any:
    """Get the current simulation state."""
    return simulation_service.get_status()
