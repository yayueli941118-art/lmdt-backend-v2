"""
个体职业实验室 — API 路由
POST /api/v1/individual-lab/simulate
"""

from fastapi import APIRouter

from app.models.micro import (
    IndividualSimulateRequest,
    IndividualSimulateResponse,
    WageCurves,
    Metrics,
    MigrationNPV,
)
from app.engines.micro import calculate_individual

router = APIRouter(prefix="/api/v1/individual-lab", tags=["个体职业实验室"])


@router.post("/simulate", response_model=IndividualSimulateResponse)
async def simulate(request: IndividualSimulateRequest) -> IndividualSimulateResponse:
    result = calculate_individual(
        edu_years=request.edu_years,
        exp_peak=request.exp_peak,
        train_type=request.train_type.value,
        disc_rate=request.disc_rate,
        migrate=request.migrate.model_dump(),
    )

    wc = result["wage_curves"]
    mt = result["metrics"]
    mn = result["migration_npv"]

    return IndividualSimulateResponse(
        wage_curves=WageCurves(**wc),
        metrics=Metrics(**mt),
        migration_npv=MigrationNPV(**mn) if mn else None,
    )
