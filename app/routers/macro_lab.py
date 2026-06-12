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


@router.post("/dmp")
async def dmp_matching(request: dict):
    """DMP 搜寻匹配模型：用匹配函数解释职位空缺、失业与匹配效率。"""
    unemployed = max(float(request.get("unemployed", 120.0)), 1.0)
    vacancies = max(float(request.get("vacancies", 80.0)), 1.0)
    matching_efficiency = max(float(request.get("matching_efficiency", 0.65)), 0.05)
    separation_rate = max(float(request.get("separation_rate", 0.025)), 0.001)
    alpha = min(max(float(request.get("alpha", 0.5)), 0.1), 0.9)

    matches = matching_efficiency * (unemployed ** alpha) * (vacancies ** (1 - alpha))
    job_finding_rate = min(matches / unemployed, 1.0)
    vacancy_filling_rate = min(matches / vacancies, 1.0)
    steady_unemployment = separation_rate / (separation_rate + job_finding_rate)
    theta = vacancies / unemployed

    curve = []
    for efficiency in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
        m = efficiency * (unemployed ** alpha) * (vacancies ** (1 - alpha))
        finding = min(m / unemployed, 1.0)
        steady = separation_rate / (separation_rate + finding)
        curve.append({
            "matching_efficiency": round(efficiency, 2),
            "job_finding_rate": round(finding * 100, 2),
            "steady_unemployment_rate": round(steady * 100, 2),
        })

    if matching_efficiency < 0.45:
        diagnosis = "匹配效率偏低：应强化就业服务、职业培训和岗位信息平台。"
    elif theta < 0.5:
        diagnosis = "岗位空缺不足：需求侧扩岗和产业吸纳能力是重点。"
    elif theta > 1.5:
        diagnosis = "岗位空缺较多但失业仍在：技能错配可能是主要矛盾。"
    else:
        diagnosis = "搜寻匹配状态较均衡：重点是保持岗位质量与劳动者技能更新。"

    return {
        "matches": round(matches, 2),
        "theta": round(theta, 3),
        "job_finding_rate": round(job_finding_rate * 100, 2),
        "vacancy_filling_rate": round(vacancy_filling_rate * 100, 2),
        "steady_unemployment_rate": round(steady_unemployment * 100, 2),
        "diagnosis": diagnosis,
        "curve": curve,
        "parameters": {
            "unemployed": unemployed,
            "vacancies": vacancies,
            "matching_efficiency": matching_efficiency,
            "separation_rate": separation_rate,
            "alpha": alpha,
        },
    }
