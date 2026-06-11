"""劳动供给决策路由"""
from fastapi import APIRouter
from app.models.labor_supply import (
    LaborSupplyRequest, LaborSupplyResponse,
    PointDetail, Effects, SupplyCurve,
)
from app.engines.labor_supply import decompose_income_substitution

router = APIRouter(prefix="/api/v2/supply", tags=["劳动供给"])


@router.post("/decompose", response_model=LaborSupplyResponse)
async def decompose_effects(request: LaborSupplyRequest) -> LaborSupplyResponse:
    """收入效应 vs 替代效应分解"""
    result = decompose_income_substitution(
        wage_initial=request.wage_initial,
        wage_new=request.wage_new,
        beta=request.beta,
        T=request.T,
    )
    return LaborSupplyResponse(
        point_A=PointDetail(**result["point_A"], type="initial"),
        point_B=PointDetail(**result["point_B"]),
        point_C=PointDetail(**result["point_C"], type="final"),
        effects=Effects(**result["effects"]),
        supply_curve=SupplyCurve(**result["supply_curve"]),
    )
