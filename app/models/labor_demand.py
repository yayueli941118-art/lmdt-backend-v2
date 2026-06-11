"""企业劳动需求请求/响应模型"""
from pydantic import BaseModel, Field
from typing import Literal


class LaborDemandRequest(BaseModel):
    K: float = Field(..., gt=0, description="资本存量", examples=[500])
    sigma: float = Field(..., gt=0, description="替代弹性", examples=[1.2])
    prod_price: float = Field(1.0, gt=0, description="产品价格指数", examples=[1.0])
    A: float = Field(1.0, gt=0, description="全要素生产率", examples=[1.0])
    alpha: float = Field(0.6, ge=0, le=1, description="资本产出弹性 share", examples=[0.6])
    w_min: float = Field(5.0, gt=0)
    w_max: float = Field(200.0, gt=0)
    n_points: int = Field(100, ge=20, le=500)
    tech_type: Literal["中性技术", "劳动替代型", "劳动互补型"] = "中性技术"


class ElasticityPoint(BaseModel):
    wage: float
    elasticity: float


class Equilibrium(BaseModel):
    wage: float
    labor_hours: float
    vmp_wage_ratio: float


class Parameters(BaseModel):
    capital: float
    sigma: float
    product_price: float
    technology_type: str
    technology_factor: float


class LaborDemandResponse(BaseModel):
    wages: list[float]
    labor_demand: list[float]
    output: list[float]
    mpl: list[float]
    elasticity: list[ElasticityPoint]
    equilibria: list[Equilibrium]
    parameters: Parameters


class FactorAllocationRequest(BaseModel):
    L: float = Field(..., gt=0, description="劳动力投入", examples=[100])
    K_values: list[float] = Field(..., min_length=2, description="资本投入序列")
    sigma: float = Field(1.2, gt=0, description="替代弹性")
    A: float = Field(1.0, gt=0)
    alpha: float = Field(0.6, ge=0, le=1)


class FactorAllocationResponse(BaseModel):
    capital: list[float]
    output: list[float]
    mpl: list[float]
    mpk: list[float]
    mrts: list[float]
    capital_labor_ratio: list[float]
    optimal_k_l: float


class IsoquantRequest(BaseModel):
    Y_target: float = Field(..., gt=0, description="目标产出", examples=[500])
    sigma: float = Field(1.2, gt=0)
    A: float = Field(1.0, gt=0)
    alpha: float = Field(0.6, ge=0, le=1)
    n_points: int = Field(50, ge=10, le=200)


class IsoquantResponse(BaseModel):
    labor: list[float]
    capital: list[float]
    target_output: float
