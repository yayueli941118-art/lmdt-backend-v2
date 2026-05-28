"""
宏观政策沙盘 — API 路由
POST /api/v1/macro-lab/simulate
"""

import numpy as np
from fastapi import APIRouter

from app.models.macro import (
    MacroSimulateRequest,
    MacroSimulateResponse,
    CurvePoint,
)

router = APIRouter(prefix="/api/v1/macro-lab", tags=["宏观政策实验室"])


@router.post("/simulate", response_model=MacroSimulateResponse)
async def simulate(request: MacroSimulateRequest) -> MacroSimulateResponse:
    """
    贝弗里奇曲线仿真接口

    接收前端决策参数 (AI冲击率、技能错配度、政策组合)，
    返回计算后的失业率、空缺率、曲线轨迹及诊断结论。

    ⚠️ 当前为 Mock 阶段 — 接口通道测试，暂不接入真实算法。
    """

    # ==========================================
    # Mock Data — 伪代码，留待 Phase 3 填充真实算法
    # ==========================================

    # 生成一条典型的贝弗里奇曲线轨迹（反比例形状）
    u_range = np.linspace(0.5, 14.0, 50)
    v_ideal = 2.5 / u_range  # v = constant / u

    # 模拟 AI 冲击 → 曲线外移
    ai_shift = request.ai_risk / 100.0 * 0.8
    v_current = v_ideal + ai_shift

    # 技能重塑补贴 → 曲线回移
    if "技能重塑补贴" in request.active_policies:
        v_current = v_current - 0.4

    # 最低工资 → 轻微右移（需求侧干预副作用）
    if "最低工资调整" in request.active_policies:
        v_current = v_current + 0.15

    # 构建曲线点数组
    curve_points = [
        CurvePoint(u=round(float(u_range[i]), 2), v=round(float(v_current[i]), 3))
        for i in range(len(u_range))
    ]

    # 决策点 = 曲线中点
    mid = len(u_range) // 2
    u_mid = round(float(u_range[mid]), 2)
    v_mid = round(float(v_current[mid]), 3)

    # 诊断逻辑
    diagnosis_level, diagnosis_text = _diagnose(request, u_mid)

    return MacroSimulateResponse(
        u_current=u_mid,
        v_current=v_mid,
        u_natural=5.0,
        curve_points=curve_points,
        diagnosis_level=diagnosis_level,
        diagnosis_text=diagnosis_text,
    )


def _diagnose(request: MacroSimulateRequest, u: float) -> tuple[str, str]:
    """
    诊断逻辑（Mock 版）

    TODO Phase 3: 接入真实 calc_beveridge + 完整的政策惩罚/奖励机制
    """
    has_skill = "技能重塑补贴" in request.active_policies
    has_minwage = "最低工资调整" in request.active_policies

    if request.mismatch_index >= 0.8 and not request.active_policies:
        return (
            "DANGER",
            "🚨 典型的结构性失业：高失业率与高空缺率并存。建议启用技能重塑补贴。",
        )
    elif has_minwage and request.mismatch_index >= 0.8 and not has_skill:
        return (
            "DANGER",
            "🚨 需求侧干预失效：最低工资无法解决技能错配，失业率反弹至 8.1%。",
        )
    elif has_skill and request.mismatch_index >= 0.8:
        return (
            "SUCCESS",
            "✅ 供给侧改革奏效：技能重塑补贴有效降低了结构性错配，贝弗里奇曲线向原点回归，失业率回落至 3.4%。",
        )
    elif request.ai_risk > 70:
        return (
            "DANGER",
            "🚨 极度危险：AI 大规模替代人工，贝弗里奇曲线显著外移，市场匹配效率崩塌。",
        )
    elif request.mismatch_index > 1.0:
        return (
            "WARNING",
            f"⚠️ 结构性失业：技能错配度 {request.mismatch_index}，高失业与高空缺并存。",
        )
    else:
        return (
            "SAFE",
            "✅ 运行良好：当前市场主要为摩擦性失业，劳动力供需基本匹配。",
        )
