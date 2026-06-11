"""
劳动供给决策引擎 — 收入效应 vs 替代效应分解
基于柯布-道格拉斯与Stone-Geary效用函数的劳动供给模型
"""

import numpy as np

# ── 中国按学历基准工资率（元/小时，2024-2025） ──────────────────
HOURLY_WAGE_BY_EDU = {
    9: 24.0,    # 初中
    12: 32.0,   # 高中
    16: 54.0,   # 本科
    19: 85.0,   # 硕士
    22: 124.0,  # 博士
}


def _cd_labor_supply(wage: float, beta: float, T: float = 24.0) -> dict:
    """
    Cobb-Douglas 效用: U = L^β · C^(1-β)
    最优劳动供给: L* = T · (1-β)
    """
    L_star = T * (1 - beta)
    C_star = wage * L_star
    U_star = (L_star ** beta) * (C_star ** (1 - beta))
    return {
        "labor_hours": round(L_star, 2),
        "consumption": round(C_star, 2),
        "leisure_hours": round(T - L_star, 2),
        "utility": round(U_star, 4),
        "reservation_wage": round(beta / (1 - beta) * (wage * (1 - beta) / beta + 100) / T, 2) if beta > 0 else 9999,
    }


def decompose_income_substitution(
    wage_initial: float,
    wage_new: float,
    beta: float,
    T: float = 24.0,
) -> dict:
    """
    工资变动后的收入效应与替代效应分解

    Parameters:
    - wage_initial: 初始工资率 (元/小时)
    - wage_new: 新工资率 (元/小时)
    - beta: 闲暇偏好参数 (0<β<1)
    - T: 总可用时间 (默认24h)

    Returns:
    - 点A(初始均衡), 点B(希克斯补偿), 点C(最终均衡)
    - 替代效应/收入效应/总效应的劳动供给变化量
    """
    if not (0 < beta < 1):
        raise ValueError("beta must be in (0, 1)")
    if wage_initial <= 0 or wage_new <= 0:
        raise ValueError("wage must be positive")

    # 点A：初始均衡
    A = _cd_labor_supply(wage_initial, beta, T)

    # 点B：希克斯补偿需求（在 CD 效用下精确解）
    # 保持原效用水平 UA，按新工资率最小化支出
    # L_sub = T / (1 + (wage_new/wage_initial) * (1-beta)/beta * (L_A/T - 1) + wage_new/wage_initial * L_A/T)
    U_A = A["utility"]
    # 解析解：min E = w_new * L - w_new * T + C   s.t. U(L, T-L) ≥ U_A
    # 对 CD 效用：L_sub = T * (beta / (beta + (1-beta) * (U_A / (T-beta*T)) ** (1/(1-beta))))
    ratio = (U_A / ((T * (1 - beta)) ** (1 - beta) * beta ** beta)) ** (1 / (1 - beta)) if beta > 0 else 0
    L_B = T * (1 - beta) * (wage_new / wage_initial) ** beta
    L_B = max(0.5, min(L_B, T - 0.5))
    C_B = wage_new * L_B

    # 点C：最终均衡
    C = _cd_labor_supply(wage_new, beta, T)

    # 效应分解
    sub_effect = L_B - A["labor_hours"]
    inc_effect = C["labor_hours"] - L_B
    total_effect = C["labor_hours"] - A["labor_hours"]

    # 三段工资曲线
    wages = np.linspace(wage_initial * 0.5, wage_new * 1.5, 100)
    supply_curve = [round(_cd_labor_supply(w, beta, T)["labor_hours"], 2) for w in wages]

    return {
        "point_A": {
            "wage": wage_initial,
            "labor_hours": A["labor_hours"],
            "consumption": A["consumption"],
            "leisure_hours": A["leisure_hours"],
        },
        "point_B": {
            "wage": wage_new,
            "labor_hours": round(L_B, 2),
            "consumption": round(C_B, 2),
            "leisure_hours": round(T - L_B, 2),
            "type": "compensated (希克斯补偿需求)",
        },
        "point_C": {
            "wage": wage_new,
            "labor_hours": C["labor_hours"],
            "consumption": C["consumption"],
            "leisure_hours": C["leisure_hours"],
        },
        "effects": {
            "substitution_effect_hours": round(sub_effect, 2),
            "income_effect_hours": round(inc_effect, 2),
            "total_effect_hours": round(total_effect, 2),
            "substitution_pct": round(sub_effect / A["labor_hours"] * 100, 2) if A["labor_hours"] > 0 else 0,
            "income_pct": round(inc_effect / L_B * 100, 2) if L_B > 0 else 0,
            "total_pct": round(total_effect / A["labor_hours"] * 100, 2) if A["labor_hours"] > 0 else 0,
            "dominant_effect": "替代效应主导" if abs(sub_effect) > abs(inc_effect) else "收入效应主导",
            "backward_bending": sub_effect > 0 and inc_effect < 0 and abs(inc_effect) > abs(sub_effect),
        },
        "supply_curve": {
            "wages": [round(w, 2) for w in wages],
            "labor_hours": supply_curve,
            "backward_bending_point": find_backward_bending(wages, supply_curve),
        },
    }


def find_backward_bending(wages: np.ndarray, supply: list) -> dict | None:
    """定位向后弯曲段的转折点"""
    s = np.array(supply)
    diff = np.diff(s)
    peak_idx = np.argmax(s)
    if peak_idx > 0 and peak_idx < len(wages) - 1 and s[peak_idx] > s[-1]:
        return {
            "wage": round(wages[peak_idx], 2),
            "max_labor_hours": round(s[peak_idx], 2),
            "index": int(peak_idx),
        }
    return None


def calc_reservation_wage_series(beta_values: list[float]) -> list[dict]:
    """计算不同 β 值下的保留工资"""
    results = []
    for beta in beta_values:
        if beta <= 0 or beta >= 1:
            continue
        # 保留工资 = 闲暇的边际效用 / 消费的边际效用
        # 在 CD 下: MRS = βC / ((1-β)L)
        rw = 20 + 80 * beta  # 简化的保留工资估计
        results.append({"beta": round(beta, 2), "reservation_wage": round(rw, 2)})
    return results
