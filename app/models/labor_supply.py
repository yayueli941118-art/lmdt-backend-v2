"""劳动供给决策请求/响应模型"""
from pydantic import BaseModel, Field


class LaborSupplyRequest(BaseModel):
    wage_initial: float = Field(..., gt=0, description="初始工资率 (元/小时)", examples=[32.0])
    wage_new: float = Field(..., gt=0, description="新工资率 (元/小时)", examples=[54.0])
    beta: float = Field(..., gt=0, lt=1, description="闲暇偏好参数", examples=[0.4])
    T: float = Field(24.0, gt=0, description="总可用时间 (小时)", examples=[24.0])


class PointDetail(BaseModel):
    wage: float
    labor_hours: float
    consumption: float
    leisure_hours: float
    type: str | None = None


class Effects(BaseModel):
    substitution_effect_hours: float
    income_effect_hours: float
    total_effect_hours: float
    substitution_pct: float
    income_pct: float
    total_pct: float
    dominant_effect: str
    backward_bending: bool


class SupplyCurve(BaseModel):
    wages: list[float]
    labor_hours: list[float]
    backward_bending_point: dict | None


class LaborSupplyResponse(BaseModel):
    point_A: PointDetail
    point_B: PointDetail
    point_C: PointDetail
    effects: Effects
    supply_curve: SupplyCurve
