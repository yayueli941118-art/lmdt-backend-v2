"""工资决定请求/响应模型"""
from pydantic import BaseModel, Field
from typing import Literal


class WageDistributionRequest(BaseModel):
    edu_years: int = Field(..., ge=6, le=22, description="受教育年限", examples=[16])
    exp_years: int = Field(..., ge=0, le=45, description="工作经验", examples=[5])
    industry: str = Field("制造业", description="行业")
    region: str = Field("二线城市", description="地区")
    n_simulations: int = Field(1000, ge=100, le=10000)
    baseline_noise: float = Field(0.15, ge=0.01, le=0.5)


class WageStatistics(BaseModel):
    mean: float
    median: float
    std: float
    cv: float
    min: float
    max: float
    p10_p90_ratio: float
    p90_p10_ratio: float
    p50_p10_ratio: float
    gini: float


class Distribution(BaseModel):
    bins: list[float]
    frequencies: list[int]


class Decile(BaseModel):
    percentile: int
    value: float


class WageParameters(BaseModel):
    education_years: int
    experience_years: int
    industry: str
    region: str


class WageDistributionResponse(BaseModel):
    statistics: WageStatistics
    distribution: Distribution
    deciles: list[Decile]
    parameters: WageParameters


class IncomeGapRequest(BaseModel):
    group_a: dict = Field(..., description="A组参数: {edu_years, exp_years, industry, region}")
    group_b: dict = Field(..., description="B组参数: {edu_years, exp_years, industry, region}")
    n_simulations: int = Field(1000, ge=100, le=10000)


class MincerControlRequest(BaseModel):
    edu_years: int = Field(..., ge=6, le=22)
    exp_years: int = Field(..., ge=0, le=45)
    gender: Literal["male", "female", "all"] = "all"
    ownership: Literal["state", "foreign", "private", "all"] = "private"
    union_member: bool = False


class DecompositionItem(BaseModel):
    base: float
    education_contribution: float
    experience_contribution: float
    gender_effect: float
    ownership_effect: float
    union_effect: float


class MincerControlResponse(BaseModel):
    predicted_monthly_wage: float
    ln_wage: float
    decomposition: DecompositionItem
    parameters: dict
