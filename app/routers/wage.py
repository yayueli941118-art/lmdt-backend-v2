"""工资决定路由"""
from fastapi import APIRouter
from app.models.wage import (
    WageDistributionRequest, WageDistributionResponse,
    WageStatistics, Distribution, Decile, WageParameters,
    IncomeGapRequest,
    MincerControlRequest, MincerControlResponse,
    DecompositionItem,
)
from app.engines.wage import (
    simulate_wage_distribution, compare_income_gap, mincer_with_controls,
)

router = APIRouter(prefix="/api/v2/wage", tags=["工资决定"])


@router.post("/distribution", response_model=WageDistributionResponse)
async def wage_distribution(request: WageDistributionRequest) -> WageDistributionResponse:
    """工资分布模拟（含基尼系数）"""
    result = simulate_wage_distribution(
        edu_years=request.edu_years, exp_years=request.exp_years,
        industry=request.industry, region=request.region,
        n_simulations=request.n_simulations, baseline_noise=request.baseline_noise,
    )
    return WageDistributionResponse(
        statistics=WageStatistics(**result["statistics"]),
        distribution=Distribution(**result["distribution"]),
        deciles=[Decile(**d) for d in result["deciles"]],
        parameters=WageParameters(**result["parameters"]),
    )


@router.post("/compare")
async def compare_income(request: IncomeGapRequest):
    """两组收入差距对比"""
    result = compare_income_gap(
        group_a=request.group_a, group_b=request.group_b,
        n_simulations=request.n_simulations,
    )
    return result


@router.post("/mincer", response_model=MincerControlResponse)
async def mincer_extended(request: MincerControlRequest) -> MincerControlResponse:
    """扩展明瑟方程（含性别、所有制、工会控制变量）"""
    result = mincer_with_controls(
        edu_years=request.edu_years, exp_years=request.exp_years,
        gender=request.gender, ownership=request.ownership,
        union_member=request.union_member,
    )
    return MincerControlResponse(
        predicted_monthly_wage=result["predicted_monthly_wage"],
        ln_wage=result["ln_wage"],
        decomposition=DecompositionItem(**result["decomposition"]),
        parameters=result["parameters"],
    )
