"""
个体职业实验室 — Pydantic 数据模型
明瑟方程 + 迁移 NPV
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class TrainType(str, Enum):
    NONE = "NONE"
    GENERAL = "GENERAL"
    SPECIAL = "SPECIFIC"


class MigrationInput(BaseModel):
    is_migrate: bool = Field(default=False)
    wage_diff: float = Field(default=10.0, ge=2.0, le=30.0)
    cost_move: float = Field(default=25.0, ge=5.0, le=80.0)
    cost_psych: float = Field(default=8.0, ge=0.0, le=30.0)


class IndividualSimulateRequest(BaseModel):
    edu_years: int = Field(default=16, ge=9, le=22, description="受教育年限")
    exp_peak: int = Field(default=40, ge=5, le=40, description="职业生涯观察年限")
    train_type: TrainType = Field(default=TrainType.NONE, description="培训类型")
    disc_rate: float = Field(default=10.0, ge=0.0, le=40.0, description="市场歧视折损 %")
    migrate: MigrationInput = Field(default_factory=MigrationInput)

    class Config:
        json_schema_extra = {
            "example": {
                "edu_years": 16,
                "exp_peak": 40,
                "train_type": "GENERAL",
                "disc_rate": 10.0,
                "migrate": {
                    "is_migrate": True,
                    "wage_diff": 10.0,
                    "cost_move": 25.0,
                    "cost_psych": 8.0,
                },
            }
        }


class WageCurves(BaseModel):
    exp_years: List[float] = Field(description="工龄 X 轴数组（≥120 点）")
    w_exp: List[float] = Field(description="实验组工资指数")
    w_base: List[float] = Field(description="对照组工资指数（高中）")
    w_disc: Optional[List[float]] = Field(default=None, description="歧视后工资指数（disc_rate > 0 时）")


class Metrics(BaseModel):
    premium_pct: float = Field(description="一生总收入提升百分比")
    breakeven_year: Optional[int] = Field(default=None, description="投资回本年限，未回本为 null")
    real_wage_dev: Optional[float] = Field(default=None, description="vs 中国实际基准偏离度 %")


class MigrationNPV(BaseModel):
    years: List[int]
    npv_cumulative: List[float]
    is_worth: bool
    breakeven_year: Optional[int] = None


class IndividualSimulateResponse(BaseModel):
    wage_curves: WageCurves
    metrics: Metrics
    migration_npv: Optional[MigrationNPV] = None

    class Config:
        json_schema_extra = {
            "example": {
                "wage_curves": {
                    "exp_years": [0, 1, 2],
                    "w_exp": [3.2, 3.4, 3.6],
                    "w_base": [2.1, 2.2, 2.3],
                    "w_disc": [2.8, 3.0, 3.2],
                },
                "metrics": {"premium_pct": 52.3, "breakeven_year": 8, "real_wage_dev": 15.2},
                "migration_npv": {
                    "years": [1, 2, 3],
                    "npv_cumulative": [-15, -2, 11],
                    "is_worth": True,
                    "breakeven_year": 3,
                },
            }
        }
