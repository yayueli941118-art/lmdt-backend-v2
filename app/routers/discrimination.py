"""歧视经济学路由 — Oaxaca-Blinder 分解"""
from fastapi import APIRouter
from app.models.discrimination import (
    OaxacaBlinderRequest, OaxacaBlinderResponse,
    DecompositionResult, VariableDecomp, CoefficientInfo, GroupStats,
)
from app.engines.discrimination import oaxaca_blinder_decompose

router = APIRouter(prefix="/api/v2/discrimination", tags=["歧视经济学"])


@router.post("/decompose", response_model=OaxacaBlinderResponse)
async def decompose(request: OaxacaBlinderRequest) -> OaxacaBlinderResponse:
    """Oaxaca-Blinder 工资歧视分解"""
    result = oaxaca_blinder_decompose(
        group_a_wages=request.group_a_wages,
        group_b_wages=request.group_b_wages,
        group_a_edu=request.group_a_edu,
        group_b_edu=request.group_b_edu,
        group_a_exp=request.group_a_exp,
        group_b_exp=request.group_b_exp,
    )
    return OaxacaBlinderResponse(
        decomposition=DecompositionResult(**result["decomposition"]),
        by_variable=[VariableDecomp(**v) for v in result["by_variable"]],
        coefficients=CoefficientInfo(**result["coefficients"]),
        group_a=GroupStats(**result["group_a"]),
        group_b=GroupStats(**result["group_b"]),
    )
