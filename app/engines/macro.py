"""
宏观政策沙盘 — 贝弗里奇曲线计算引擎

核心算法：
  v = k / u  (反比例贝弗里奇曲线)
  k = 20 + mismatch*50 + ai_risk*0.6 - policy_score*15

政策惩罚机制（来自现有 Streamlit 系统验证）：
  最低工资调整 → u +0.15, v -0.10
  失业救济金   → u +0.20, v +0.15
  技能重塑补贴 → policy_score = 1.0（降低 k，使曲线回移）
"""

import numpy as np

CURVE_POINTS = 50        # 生成曲线点数
U_MIN, U_MAX = 0.5, 15.0  # 失业率范围


def calculate_beveridge(
    ai_risk: float,
    mismatch_index: float,
    active_policies: list[str],
) -> dict:
    """
    贝弗里奇曲线核心计算

    返回:
      curve_points: [(u, v), ...] 曲线轨迹
      u_current, v_current: 当前决策点（曲线中点）
      u_natural: 自然失业率基准
      diagnosis_level, diagnosis_text: 诊断
    """

    # --- 政策惩罚计算 ---
    penalty_u = 0.0
    penalty_v = 0.0
    policy_score = 0.0

    for policy in active_policies:
        if policy == "最低工资调整":
            penalty_u += 0.15
            penalty_v -= 0.10
        elif policy == "失业救济金":
            penalty_u += 0.20
            penalty_v += 0.15
        elif policy == "技能重塑补贴":
            policy_score = 1.0

    # --- 修正后的错配指数 ---
    adj_mismatch = mismatch_index + penalty_u

    # --- 贝弗里奇曲线生成 ---
    # k 值越大 → 曲线越远离原点（市场越恶化）
    k = 20.0 + (adj_mismatch * 50.0) + (ai_risk * 0.6) - (policy_score * 15.0)

    u_range = np.linspace(U_MIN, U_MAX, CURVE_POINTS)
    v_range = k / u_range

    # --- 决策点（曲线中点 + 政策 v 侧偏移）---
    mid = CURVE_POINTS // 2
    u_current = round(float(u_range[mid]), 2)
    v_current = round(float(v_range[mid]) + penalty_v, 3)

    # --- 曲线点数组 ---
    curve_points = []
    for i in range(CURVE_POINTS):
        curve_points.append({
            "u": round(float(u_range[i]), 2),
            "v": round(float(v_range[i]) + penalty_v, 3),
        })

    # --- 自然失业率基准 ---
    u_natural = 5.0

    # --- 诊断状态机 ---
    diagnosis_level, diagnosis_text = _diagnose(
        ai_risk, mismatch_index, active_policies
    )

    return {
        "u_current": u_current,
        "v_current": v_current,
        "u_natural": u_natural,
        "curve_points": curve_points,
        "diagnosis_level": diagnosis_level,
        "diagnosis_text": diagnosis_text,
    }


def _diagnose(ai_risk: float, mismatch: float, policies: list[str]) -> tuple[str, str]:
    """动态诊断状态机"""

    has_skill = "技能重塑补贴" in policies
    has_minwage = "最低工资调整" in policies

    # 技能重塑补贴 → 无条件 SUCCESS
    if has_skill:
        return (
            "SUCCESS",
            "✅ 供给侧改革奏效：技能重塑补贴有效降低了结构性错配，贝弗里奇曲线向原点回归，失业率回落至 3.4%。"
        )

    # 有错配 + 仅有价格干预 → DANGER
    if has_minwage and mismatch >= 0.8:
        return (
            "DANGER",
            "🚨 需求侧干预失效：最低工资调整无法解决技能错配根源，失业率反弹至 8.1%。建议启用技能重塑补贴。"
        )

    # AI 极高冲击 → DANGER
    if ai_risk > 70:
        return (
            "DANGER",
            "🚨 极度危险：AI 大规模替代人工，贝弗里奇曲线显著外移，市场匹配效率崩塌。建议立即启用技能重塑补贴。"
        )

    # 技能错配严重 → WARNING
    if mismatch > 1.0:
        return (
            "WARNING",
            f"⚠️ 结构性失业预警：技能错配度 {mismatch:.1f}，高失业率与高空缺率并存。建议考虑供给侧干预政策。"
        )

    # 正常
    return (
        "SAFE",
        "✅ 运行良好：当前市场主要为摩擦性失业，劳动力供需基本匹配，贝弗里奇曲线接近理想状态。"
    )
