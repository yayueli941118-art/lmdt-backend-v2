"""
个体职业实验室 — API 路由
POST /api/v1/individual-lab/simulate
"""

from fastapi import APIRouter, HTTPException

from app.models.micro import (
    IndividualSimulateRequest,
    IndividualSimulateResponse,
    MetricsResponse,
    ChartsResponse,
    MigrationResponse,
)
from app.engines.micro import calculate_individual

router = APIRouter(prefix="/api/v1/individual-lab", tags=["个体职业实验室"])


@router.post("/simulate", response_model=IndividualSimulateResponse)
async def simulate(request: IndividualSimulateRequest) -> IndividualSimulateResponse:
    try:
        result = calculate_individual(
            edu=request.edu,
            exp_peak=request.exp_peak,
            train_type=request.train_type,
            disc=request.disc,
            migrate=request.migrate,
            migrate_age=request.migrate_age,
            w_diff=request.w_diff,
            c_move=request.c_move,
            c_psych=request.c_psych,
            family_migrate=request.family_migrate,
            spouse_loss=request.spouse_loss,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Core calculation broken: {str(e)}")

    return IndividualSimulateResponse(
        status="success",
        metrics=MetricsResponse(**result["metrics"]),
        charts=ChartsResponse(**result["charts"]),
        migration=MigrationResponse(**result["migration"]),
    )
