"""宏观政策扩展路由"""
from fastapi import APIRouter
from app.models.macro import (
    MacroSimulateRequest, MacroSimulateResponse,
    CurvePoint,
)
from app.engines.macro import (
    calculate_beveridge, simulate_unemployment, simulate_minimum_wage_impact,
)

router = APIRouter(prefix="/api/v2/macro", tags=["宏观政策"])


@router.post("/beveridge", response_model=MacroSimulateResponse)
async def beveridge(request: MacroSimulateRequest) -> MacroSimulateResponse:
    """贝弗里奇曲线计算"""
    result = calculate_beveridge(
        ai_risk=request.ai_risk,
        mismatch_index=request.mismatch_index,
        active_policies=request.active_policies,
    )
    return MacroSimulateResponse(
        u_current=result["u_current"],
        v_current=result["v_current"],
        u_natural=result["u_natural"],
        curve_points=[CurvePoint(**p) for p in result["curve_points"]],
        diagnosis_level=result["diagnosis_level"],
        diagnosis_text=result["diagnosis_text"],
    )


@router.post("/unemployment")
async def unemployment(request: dict):
    """失业率仿真模拟"""
    result = simulate_unemployment(
        natural_rate=request.get("natural_rate", 5.0),
        min_wage=request.get("min_wage", 25.0),
        unemployment_benefit=request.get("unemployment_benefit", 2000.0),
        skill_mismatch=request.get("skill_mismatch", 0.5),
        ai_risk=request.get("ai_risk", 20.0),
        labor_demand_shock=request.get("labor_demand_shock", 0.0),
    )
    return result


@router.post("/min-wage-impact")
async def min_wage_impact(request: dict):
    """最低工资对就业的影响"""
    result = simulate_minimum_wage_impact(
        min_wage=request.get("min_wage", 25.0),
        avg_wage=request.get("avg_wage", 54.0),
        employment=request.get("employment", 870.0),
        elasticity=request.get("elasticity", -0.15),
    )
    return result
