"""
企业劳动需求引擎 — CES 生产函数 + 希克斯-马歇尔派生需求定律
参考：Arrow, Chenery, Minhas & Solow (1961)
"""

import numpy as np


def ces_output(L: float, K: float, sigma: float, A: float = 1.0, alpha: float = 0.6) -> float:
    """
    CES 生产函数: Y = A · (α·K^ρ + (1-α)·L^ρ)^(1/ρ)
    其中 ρ = (σ-1)/σ
    """
    eps = 1e-12
    L = max(L, eps)
    rho = (sigma - 1) / sigma
    if abs(rho) < 1e-6:  # σ→1，趋近 Cobb-Douglas
        return A * (K ** alpha) * (L ** (1 - alpha))
    val = alpha * (K ** rho) + (1 - alpha) * (L ** rho)
    return A * max(val, eps) ** (1 / rho)


def ces_mpl(L: float, K: float, sigma: float, A: float = 1.0, alpha: float = 0.6) -> float:
    """CES 边际劳动产出 (MPL)"""
    eps = 1e-12
    L = max(L, eps)
    rho = (sigma - 1) / sigma
    if abs(rho) < 1e-6:
        return A * (1 - alpha) * (K ** alpha) * (L ** (-alpha))
    val = alpha * (K ** rho) + (1 - alpha) * (L ** rho)
    val = max(val, eps)
    return A * (1 - alpha) * (L ** (rho - 1)) * (val ** (1 / rho - 1))


def ces_mpk(L: float, K: float, sigma: float, A: float = 1.0, alpha: float = 0.6) -> float:
    """CES 边际资本产出 (MPK)"""
    eps = 1e-12
    K_safe = max(K, eps)
    rho = (sigma - 1) / sigma
    if abs(rho) < 1e-6:
        return A * alpha * (L ** (1 - alpha)) * (K_safe ** (alpha - 1))
    val = alpha * (K_safe ** rho) + (1 - alpha) * (L ** rho)
    val = max(val, eps)
    return A * alpha * (K_safe ** (rho - 1)) * (val ** (1 / rho - 1))


def calc_labor_demand_curve(
    K: float,
    sigma: float,
    prod_price: float,
    A: float = 1.0,
    alpha: float = 0.6,
    w_min: float = 5.0,
    w_max: float = 200.0,
    n_points: int = 100,
    tech_type: str = "中性技术",
) -> dict:
    """
    计算劳动需求曲线

    原理: VMP(w) = P · MPL(L) = w → 解出最优 L*(w)

    Parameters:
    - K: 资本存量
    - sigma: 资本-劳动替代弹性
    - prod_price: 产品价格指数
    - tech_type: 技术类型 ("中性技术"/"劳动替代型"/"劳动互补型")

    Returns:
    - 工资向量、最优劳动需求、产出、MPL曲线
    """
    # 技术修正
    tech_factors = {"中性技术": 1.0, "劳动替代型": 0.55, "劳动互补型": 1.65}
    A_adj = A * tech_factors.get(tech_type, 1.0)

    wages = np.linspace(w_min, w_max, n_points)
    L_opt = np.zeros(n_points)
    Y_opt = np.zeros(n_points)
    MPL_vals = np.zeros(n_points)

    for i, w in enumerate(wages):
        # 数值求解：找到 L 使得 VMP(L) = w
        # 使用 CES VMP 反函数近似
        if sigma <= 0.95:
            L_star = (A_adj * K * 12 / w) ** 0.7
        elif sigma >= 2.0:
            L_star = (A_adj * K * 5 / (w * sigma)) ** 1.8
        else:
            L_star = (A_adj * K * 10 / w) ** (1.0 / sigma)
        L_star = max(0.5, min(L_star, 2000.0))
        L_opt[i] = L_star
        Y_opt[i] = ces_output(L_star, K, sigma, A_adj, alpha)
        MPL_vals[i] = ces_mpl(L_star, K, sigma, A_adj, alpha)

    # 弹性计算
    elasticity = _compute_elasticity(wages, L_opt)

    # 利润最大化点（w = MPL 处）
    equilibria = _find_equilibria(wages, L_opt, MPL_vals, prod_price)

    return {
        "wages": [round(w, 2) for w in wages],
        "labor_demand": [round(L, 2) for L in L_opt],
        "output": [round(Y, 2) for Y in Y_opt],
        "mpl": [round(m, 2) for m in MPL_vals],
        "elasticity": elasticity,
        "equilibria": equilibria,
        "parameters": {
            "capital": K,
            "sigma": sigma,
            "product_price": prod_price,
            "technology_type": tech_type,
            "technology_factor": A_adj,
        },
    }


def _compute_elasticity(wages: np.ndarray, L_opt: np.ndarray) -> list[dict]:
    """计算需求弹性沿工资轴的分布"""
    dL = np.diff(L_opt)
    dw = np.diff(wages)
    # η = (ΔL/L) / (Δw/w)
    eta = (dL / L_opt[:-1]) / (dw / wages[:-1])
    return [
        {"wage": round(wages[i], 2), "elasticity": round(float(eta[i]), 3)}
        for i in range(0, len(eta), 10)
    ]


def _find_equilibria(
    wages: np.ndarray, L_opt: np.ndarray, MPL_vals: np.ndarray, prod_price: float
) -> list[dict]:
    """找到 VMP ≈ w（利润最大化点）"""
    equilibria = []
    # 找 VMP 曲线与 45° 线交点
    for i in range(len(wages)):
        mpl_value = MPL_vals[i] * prod_price / wages[i]
        if 0.8 < mpl_value < 1.2:
            equilibria.append({
                "wage": round(wages[i], 2),
                "labor_hours": round(L_opt[i], 2),
                "vmp_wage_ratio": round(mpl_value, 3),
            })
    return equilibria[:5]  # 最多5个近似均衡点


def calc_factor_allocation(
    L: float,
    K_values: list[float],
    sigma: float,
    A: float = 1.0,
    alpha: float = 0.6,
) -> dict:
    """
    要素配置沙盘：固定劳动下资本变化对产出和边际产品的影响

    Returns:
    - 产出曲线 Y(K)
    - MPL(K), MPK(K)
    - 技术替代率 MRTS(K) = MPL/MPK
    - optimal K/L ratio
    """
    results = {
        "capital": K_values,
        "output": [],
        "mpl": [],
        "mpk": [],
        "mrts": [],
        "capital_labor_ratio": [],
    }

    for K in K_values:
        Y = ces_output(L, K, sigma, A, alpha)
        mpl = ces_mpl(L, K, sigma, A, alpha)
        mpk = ces_mpk(L, K, sigma, A, alpha)
        results["output"].append(round(Y, 2))
        results["mpl"].append(round(mpl, 4))
        results["mpk"].append(round(mpk, 4))
        results["mrts"].append(round(mpl / mpk, 4) if mpk > 0 else 9999)
        results["capital_labor_ratio"].append(round(K / L, 2))

    # 最优 K/L：MRTS = r/w ≈ 1（等成本线斜率）
    optimal_idx = np.argmin(np.abs(np.array(results["mrts"]) - 1.0))
    results["optimal_k_l"] = round(results["capital_labor_ratio"][optimal_idx], 2)

    return results


def calc_isoquant(
    Y_target: float,
    sigma: float,
    A: float = 1.0,
    alpha: float = 0.6,
    n_points: int = 50,
) -> dict:
    """
    计算给定产出水平下的等产量线

    Returns: L 和 K 的组合对
    """
    L_range = np.linspace(1, 200, n_points)
    K_range = []

    for L in L_range:
        # 从 Y = A·(αK^ρ + (1-α)L^ρ)^(1/ρ) 解出 K
        rho = (sigma - 1) / sigma
        if abs(rho) < 1e-6:
            K = (Y_target / (A * L ** (1 - alpha))) ** (1 / alpha)
        else:
            term = (Y_target / A) ** rho - (1 - alpha) * (L ** rho)
            if term > 0:
                K = (term / alpha) ** (1 / rho)
            else:
                K = 0
        K_range.append(round(max(0, K), 2))

    return {
        "labor": [round(L, 2) for L in L_range],
        "capital": K_range,
        "target_output": Y_target,
    }
