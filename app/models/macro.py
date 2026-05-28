"""
宏观政策沙盘 — Pydantic 数据模型
Request: 前端决策参数 → Response: 后端计算结果
"""

from pydantic import BaseModel, Field
from typing import List


# ==========================================
# Request Schema
# ==========================================
class MacroSimulateRequest(BaseModel):
    """前端传入的决策参数"""

    ai_risk: float = Field(
        default=30.0,
        ge=0.0,
        le=100.0,
        description="AI 技术替代冲击率 (%), 0=无替代 100=全面替代",
    )
    mismatch_index: float = Field(
        default=0.8,
        ge=0.0,
        le=2.0,
        description="技能错配指数, 0=完美匹配 2.0=严重错配",
    )
    active_policies: List[str] = Field(
        default_factory=list,
        description="当前激活的政策列表, 如 ['最低工资调整', '技能重塑补贴', '失业救济金']",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "ai_risk": 30.0,
                "mismatch_index": 0.8,
                "active_policies": ["技能重塑补贴"],
            }
        }


# ==========================================
# Response Schema
# ==========================================
class CurvePoint(BaseModel):
    """贝弗里奇曲线上的单个点"""
    u: float = Field(description="失业率 (U, %)")
    v: float = Field(description="岗位空缺率 (V, %)")


class MacroSimulateResponse(BaseModel):
    """后端返回的渲染数据"""

    u_current: float = Field(description="当前即时失业率 (%)")
    v_current: float = Field(description="当前岗位空缺率 (%)")
    u_natural: float = Field(default=5.0, description="自然失业率基准值 (%)")

    curve_points: List[CurvePoint] = Field(
        description="贝弗里奇曲线轨迹点数组, 用于前端绘制曲线"
    )

    diagnosis_level: str = Field(
        description="诊断级别: SAFE | WARNING | DANGER | SUCCESS",
    )
    diagnosis_text: str = Field(description="经济学诊断结论")

    class Config:
        json_schema_extra = {
            "example": {
                "u_current": 3.4,
                "v_current": 2.56,
                "u_natural": 5.0,
                "curve_points": [
                    {"u": 0.5, "v": 19.2},
                    {"u": 2.0, "v": 6.8},
                    {"u": 5.0, "v": 2.9},
                ],
                "diagnosis_level": "SUCCESS",
                "diagnosis_text": "供给侧改革奏效：技能重塑补贴有效降低了结构性错配，贝弗里奇曲线向原点回归。",
            }
        }
