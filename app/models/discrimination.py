"""歧视经济学请求/响应模型"""
from pydantic import BaseModel, Field


class OaxacaBlinderRequest(BaseModel):
    group_a_wages: list[float] = Field(..., min_length=3, description="A组月薪")
    group_b_wages: list[float] = Field(..., min_length=3, description="B组月薪")
    group_a_edu: list[float] = Field(..., min_length=3, description="A组受教育年限")
    group_b_edu: list[float] = Field(..., min_length=3, description="B组受教育年限")
    group_a_exp: list[float] = Field(..., min_length=3, description="A组工龄")
    group_b_exp: list[float] = Field(..., min_length=3, description="B组工龄")


class VariableDecomp(BaseModel):
    variable: str
    endowment: float
    coefficient: float
    interaction: float
    total: float


class CoefficientInfo(BaseModel):
    group_a: list[float]
    group_b: list[float]
    coefficient_names: list[str]
    r_squared_a: float
    r_squared_b: float


class GroupStats(BaseModel):
    mean_wage: float
    median_wage: float
    std_wage: float
    mean_edu: float
    mean_exp: float
    sample_size: int


class DecompositionResult(BaseModel):
    total_gap_ln: float
    total_gap_pct: float
    endowment_effect: float
    coefficient_effect: float
    interaction_effect: float
    explained_pct: float
    unexplained_pct: float
    gap_direction: str


class OaxacaBlinderResponse(BaseModel):
    decomposition: DecompositionResult
    by_variable: list[VariableDecomp]
    coefficients: CoefficientInfo
    group_a: GroupStats
    group_b: GroupStats
