"""企业劳动需求路由"""
from fastapi import APIRouter
from app.models.labor_demand import (
    LaborDemandRequest, LaborDemandResponse,
    ElasticityPoint, Equilibrium, Parameters,
    FactorAllocationRequest, FactorAllocationResponse,
    IsoquantRequest, IsoquantResponse,
)
from app.engines.labor_demand import (
    calc_labor_demand_curve, calc_factor_allocation, calc_isoquant,
)

router = APIRouter(prefix="/api/v2/demand", tags=["劳动需求"])


@router.post("/curve", response_model=LaborDemandResponse)
async def demand_curve(request: LaborDemandRequest) -> LaborDemandResponse:
    """CES 劳动需求曲线"""
    result = calc_labor_demand_curve(
        K=request.K, sigma=request.sigma, prod_price=request.prod_price,
        A=request.A, alpha=request.alpha,
        w_min=request.w_min, w_max=request.w_max, n_points=request.n_points,
        tech_type=request.tech_type,
    )
    return LaborDemandResponse(
        wages=result["wages"], labor_demand=result["labor_demand"],
        output=result["output"], mpl=result["mpl"],
        elasticity=[ElasticityPoint(**e) for e in result["elasticity"]],
        equilibria=[Equilibrium(**e) for e in result["equilibria"]],
        parameters=Parameters(**result["parameters"]),
    )


@router.post("/factor-allocation", response_model=FactorAllocationResponse)
async def factor_allocation(request: FactorAllocationRequest) -> FactorAllocationResponse:
    """要素配置沙盘"""
    result = calc_factor_allocation(
        L=request.L, K_values=request.K_values,
        sigma=request.sigma, A=request.A, alpha=request.alpha,
    )
    return FactorAllocationResponse(**result)


@router.post("/isoquant", response_model=IsoquantResponse)
async def isoquant(request: IsoquantRequest) -> IsoquantResponse:
    """等产量线"""
    result = calc_isoquant(
        Y_target=request.Y_target, sigma=request.sigma,
        A=request.A, alpha=request.alpha, n_points=request.n_points,
    )
    return IsoquantResponse(**result)
