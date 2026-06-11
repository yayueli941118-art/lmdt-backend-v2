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


def simulate_unemployment(
    natural_rate: float = 5.0,
    min_wage: float = 25.0,
    unemployment_benefit: float = 2000.0,
    skill_mismatch: float = 0.5,
    ai_risk: float = 20.0,
    labor_demand_shock: float = 0.0,
) -> dict:
    """
    失业率仿真模拟

    考虑因素：
    - 自然失业率 (NAIRU)
    - 最低工资的就业效应 (Card & Krueger, 1994)
    - 失业救济的搜寻效应
    - 技能错配的结构性失业
    - AI 冲击的技术性失业
    - 劳动需求外生冲击

    Returns:
    - 总失业率分解
    - 各因素贡献
    - 时间序列模拟
    """
    # 摩擦性失业（基准 + 救济效应）
    benefit_effect = max(0, (unemployment_benefit - 1500) / 10000)
    frictional = natural_rate + benefit_effect

    # 结构性失业（技能错配）
    structural = skill_mismatch * 4.0

    # 制度性失业（最低工资）
    # 参考：最低工资每提高10%，就业减少0.1-0.3%（弹性 -0.15）
    base_min_wage = 20.0
    min_wage_effect = max(0, (min_wage / base_min_wage - 1) * 3.0)

    # 技术性失业（AI）
    tech_unemployment = ai_risk * 0.05

    # 周期性失业（需求冲击）
    cyclical = max(0, labor_demand_shock * 0.5)

    # 总失业率
    total = frictional + structural + min_wage_effect + tech_unemployment + cyclical
    total = min(total, 25.0)

    # 时间序列模拟（48个月）
    months = list(range(1, 49))
    u_series = []
    for m in months:
        # 逐步收敛
        convergence = 1 - np.exp(-m / 6)
        um = total * convergence
        u_series.append(round(um, 2))

    return {
        "total_rate": round(total, 2),
        "breakdown": {
            "frictional": round(frictional, 2),
            "structural": round(structural, 2),
            "minimum_wage_effect": round(min_wage_effect, 2),
            "technological": round(tech_unemployment, 2),
            "cyclical": round(cyclical, 2),
        },
        "time_series": {
            "months": months,
            "unemployment_rate": u_series,
        },
        "parameters": {
            "natural_rate": natural_rate,
            "min_wage": min_wage,
            "unemployment_benefit": unemployment_benefit,
            "skill_mismatch": skill_mismatch,
            "ai_risk": ai_risk,
            "labor_demand_shock": labor_demand_shock,
        },
    }


def simulate_minimum_wage_impact(
    min_wage: float,
    avg_wage: float,
    employment: float,
    elasticity: float = -0.15,
) -> dict:
    """
    最低工资对就业的影响 (Card & Krueger 型分析)

    Parameters:
    - min_wage: 最低工资 (元/小时)
    - avg_wage: 当前平均工资 (元/小时)
    - employment: 当前就业人数 (万)
    - elasticity: 就业对最低工资的弹性

    Returns:
    - 就业变化预测
    - Kaitz 指数 (min_wage / median_wage)
    - 受影响的工人比例
    """
    kaitz_index = min_wage / avg_wage if avg_wage > 0 else 0

    # 就业变化
    emp_change_pct = elasticity * (kaitz_index - 0.5) * 100 if kaitz_index > 0.5 else 0
    emp_change = employment * emp_change_pct / 100
    new_employment = employment + emp_change

    # 受影响工人（工资在最低工资附近的）
    affected_share = min(100, max(0, (1 - kaitz_index + 0.3) * 50))

    # 不同弹性假设下的影响
    scenarios = []
    for e in [-0.05, -0.10, -0.15, -0.20, -0.30]:
        change = elasticity_to_pct(kaitz_index, e)
        scenarios.append({
            "elasticity": e,
            "employment_change_pct": round(change, 2),
            "employment_change": round(employment * change / 100, 1),
        })

    return {
        "kaitz_index": round(kaitz_index, 3),
        "current_employment": employment,
        "predicted_employment": round(new_employment, 1),
        "employment_change_pct": round(emp_change_pct, 2),
        "affected_worker_pct": round(affected_share, 2),
        "scenarios": scenarios,
        "benchmarks": {
            "US_kaitz_2024": 0.33,
            "China_kaitz_estimate": 0.45,
            "France_kaitz_2024": 0.62,
        },
    }


def elasticity_to_pct(kaitz: float, elasticity: float) -> float:
    """弹性 → 就业变化百分比"""
    return elasticity * (kaitz - 0.5) * 100 if kaitz > 0.5 else 0
