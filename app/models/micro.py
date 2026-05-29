"""
个体职业实验室 — Pydantic 数据模型
明瑟工资方程 + 迁移 NPV
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class IndividualSimulateRequest(BaseModel):
    edu: int = Field(default=16, ge=9, le=22, description="受教育年限：9=初中,12=高中,16=本科,19=硕士,22=博士")
    exp_peak: int = Field(default=40, ge=5, le=40, description="职业生涯观察年限")
    train_type: str = Field(default="无额外培训", description="培训类型：无额外培训 / 一般培训 (通用技能) / 特殊培训 (企业专属技能)")
    disc: float = Field(default=10.0, ge=0.0, le=50.0, description="劳动力市场歧视折损率(%)")
    migrate: bool = Field(default=False, description="是否考虑城市迁移")
    migrate_age: int = Field(default=22, ge=18, le=60, description="迁移发生年龄")
    w_diff: float = Field(default=10.0, description="大城市月薪相较于家乡的溢价(k/月)")
    c_move: float = Field(default=25.0, description="一次性搬迁阵痛成本(k)")
    c_psych: float = Field(default=8.0, description="年度心理与适应成本(k/年)")
    family_migrate: bool = Field(default=False, description="是否考虑家庭联合迁移")
    spouse_loss: float = Field(default=3.0, ge=2.0, le=15.0, description="配偶月薪损失(k/月)")

    class Config:
        json_schema_extra = {
            "example": {
                "edu": 16,
                "exp_peak": 40,
                "train_type": "一般培训 (通用技能)",
                "disc": 10.0,
                "migrate": True,
                "w_diff": 10.0,
                "c_move": 25.0,
                "c_psych": 8.0,
            }
        }


class MetricsResponse(BaseModel):
    lifetime_premium_pct: float
    discrimination_loss_pct: float
    vs_china_baseline_pct: float
    china_baseline_value: float
    breakeven_age: Optional[int] = None
    crossover_age: Optional[int] = None
    irr_pct: float = 0.0


class ChartsResponse(BaseModel):
    age_years: List[int]
    wage_curve_selected: List[float]
    wage_curve_baseline: List[float]
    wage_curve_disc: List[float]
    wage_curve_selected_gross: List[float] = []


class MigrationResponse(BaseModel):
    is_calculated: bool = False
    years: List[int] = []
    cumulative_npv: List[float] = []
    is_worth_it: bool = False


class IndividualSimulateResponse(BaseModel):
    status: str = "success"
    metrics: MetricsResponse
    charts: ChartsResponse
    migration: MigrationResponse
