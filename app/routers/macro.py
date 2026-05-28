"""
宏观政策沙盘 — API 路由
POST /api/v1/macro-lab/simulate
"""

from fastapi import APIRouter

from app.models.macro import (
    MacroSimulateRequest,
    MacroSimulateResponse,
    CurvePoint,
)
from app.engines.macro import calculate_beveridge

router = APIRouter(prefix="/api/v1/macro-lab", tags=["宏观政策实验室"])


@router.post("/simulate", response_model=MacroSimulateResponse)
async def simulate(request: MacroSimulateRequest) -> MacroSimulateResponse:
    """
    贝弗里奇曲线仿真接口

    接收前端决策参数，调用真实经济学引擎计算失业率、空缺率、
    贝弗里奇曲线轨迹及诊断结论。
    """
    result = calculate_beveridge(
        ai_risk=request.ai_risk,
        mismatch_index=request.mismatch_index,
        active_policies=request.active_policies,
    )

    curve_points = [
        CurvePoint(u=p["u"], v=p["v"])
        for p in result["curve_points"]
    ]

    return MacroSimulateResponse(
        u_current=result["u_current"],
        v_current=result["v_current"],
        u_natural=result["u_natural"],
        curve_points=curve_points,
        diagnosis_level=result["diagnosis_level"],
        diagnosis_text=result["diagnosis_text"],
    )
