"""
工资决定与收入差距引擎
覆盖：明瑟方程扩展、工资分布、基尼系数、分位数分析
"""

import numpy as np


# ── 中国 2024-2025 分行业工资基准（月薪，元） ──────────────────
INDUSTRY_WAGE_BASELINE = {
    "信息技术": 14500,
    "金融业": 13800,
    "制造业": 7200,
    "建筑业": 6500,
    "批发零售": 5800,
    "住宿餐饮": 4200,
    "教育": 8500,
    "医疗": 9200,
    "交通运输": 7800,
    "农业": 3800,
}

# 地区系数
REGION_MULTIPLIER = {
    "一线城市": 1.35,
    "新一线城市": 1.10,
    "二线城市": 0.85,
    "三线及以下": 0.65,
}


def simulate_wage_distribution(
    edu_years: int,
    exp_years: int,
    industry: str,
    region: str,
    n_simulations: int = 1000,
    baseline_noise: float = 0.15,
) -> dict:
    """
    模拟个体工资分布（考虑异质性随机扰动）

    明瑟方程 + 行业溢价 + 地区调整 + 随机异质性

    Returns:
    - 工资分布统计 (均值, 中位数, 标准差, 分位数)
    - 直方图区间
    - 基尼系数
    """
    # 基准明瑟预测
    ln_w_base = 7.5 + 0.085 * edu_years + 0.05 * exp_years - 0.0006 * (exp_years ** 2)

    # 行业溢价
    industry_wage = INDUSTRY_WAGE_BASELINE.get(industry, 6500)
    industry_premium = np.log(industry_wage) - np.log(6500)

    # 地区调整
    region_mult = REGION_MULTIPLIER.get(region, 1.0)
    region_adj = np.log(region_mult)

    # 模拟异质性扰动
    np.random.seed(42)
    random_shocks = np.random.normal(0, baseline_noise, n_simulations)
    ln_wages = ln_w_base + industry_premium + region_adj + random_shocks
    wages = np.exp(ln_wages)

    # 统计
    mean_wage = float(np.mean(wages))
    median_wage = float(np.median(wages))
    std_wage = float(np.std(wages))
    gini = _calc_gini(wages)
    deciles = _calc_deciles(wages)

    # 直方图
    hist, bin_edges = np.histogram(wages, bins=20)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

    # P90/P10 和 P50/P10 比率
    p10 = float(np.percentile(wages, 10))
    p50 = float(np.percentile(wages, 50))
    p90 = float(np.percentile(wages, 90))

    return {
        "statistics": {
            "mean": round(mean_wage, 2),
            "median": round(median_wage, 2),
            "std": round(std_wage, 2),
            "cv": round(std_wage / mean_wage, 4),
            "min": round(float(np.min(wages)), 2),
            "max": round(float(np.max(wages)), 2),
            "p10_p90_ratio": round(p90 / p10, 2),
            "p90_p10_ratio": round(p90 / p10, 2),
            "p50_p10_ratio": round(p50 / p10, 2),
            "gini": round(gini, 4),
        },
        "distribution": {
            "bins": [round(b, 2) for b in bin_centers],
            "frequencies": [int(h) for h in hist],
        },
        "deciles": deciles,
        "parameters": {
            "education_years": edu_years,
            "experience_years": exp_years,
            "industry": industry,
            "region": region,
        },
    }


def compare_income_gap(
    group_a: dict,
    group_b: dict,
    n_simulations: int = 1000,
) -> dict:
    """
    两组收入差距对比分析

    Parameters:
    - group_a, group_b: 各含 edu_years, exp_years, industry, region
    """
    result_a = simulate_wage_distribution(
        group_a["edu_years"], group_a["exp_years"],
        group_a.get("industry", "制造业"), group_a.get("region", "二线城市"),
        n_simulations,
    )
    result_b = simulate_wage_distribution(
        group_b["edu_years"], group_b["exp_years"],
        group_b.get("industry", "制造业"), group_b.get("region", "二线城市"),
        n_simulations,
    )

    # 均值差异分解
    mean_diff = result_a["statistics"]["mean"] - result_b["statistics"]["mean"]
    mean_diff_pct = mean_diff / result_b["statistics"]["mean"] * 100

    # Kolmogorov-Smirnov 检验近似
    ks_stat = round(abs(result_a["statistics"]["median"] - result_b["statistics"]["median"]) /
                    max(result_a["statistics"]["std"], result_b["statistics"]["std"], 1), 4)

    return {
        "group_a": {**group_a, **result_a["statistics"]},
        "group_b": {**group_b, **result_b["statistics"]},
        "gap": {
            "mean_difference": round(mean_diff, 2),
            "mean_difference_pct": round(mean_diff_pct, 2),
            "ratio_a_to_b": round(result_a["statistics"]["mean"] / result_b["statistics"]["mean"], 3)
            if result_b["statistics"]["mean"] > 0 else 0,
            "ks_statistic": ks_stat,
        },
        "distributions": {
            "group_a": result_a["distribution"],
            "group_b": result_b["distribution"],
        },
        "deciles_comparison": {
            "group_a": result_a["deciles"],
            "group_b": result_b["deciles"],
        },
    }


def _calc_gini(wages: np.ndarray) -> float:
    """基尼系数（快速向量化）"""
    sorted_w = np.sort(wages)
    n = len(sorted_w)
    cum_w = np.cumsum(sorted_w)
    # G = (2 * Σ i*w_i - (n+1) * Σ w_i) / (n * Σ w_i)
    total = cum_w[-1]
    if total <= 0:
        return 0.0
    return float((2 * np.sum(np.arange(1, n + 1) * sorted_w) - (n + 1) * total) / (n * total))


def _calc_deciles(wages: np.ndarray) -> list[dict]:
    """十分位数计算"""
    deciles = []
    for d in range(10, 101, 10):
        deciles.append({
            "percentile": d,
            "value": round(float(np.percentile(wages, d)), 2),
        })
    return deciles


def mincer_with_controls(
    edu_years: int,
    exp_years: int,
    gender: str = "all",
    ownership: str = "private",
    union_member: bool = False,
) -> dict:
    """
    带控制变量的明瑟方程扩展

    额外控制：
    - 性别溢价/惩罚
    - 所有制溢价（国企/外企/民营）
    - 工会溢价
    """
    ln_w = 7.5 + 0.085 * edu_years + 0.05 * exp_years - 0.0006 * (exp_years ** 2)

    # 性别
    gender_mult = {"male": 1.08, "female": 0.89, "all": 1.0}
    ln_w += np.log(gender_mult.get(gender, 1.0))

    # 所有制
    ownership_mult = {"state": 1.12, "foreign": 1.18, "private": 0.92, "all": 1.0}
    ln_w += np.log(ownership_mult.get(ownership, 1.0))

    # 工会
    if union_member:
        ln_w += np.log(1.06)

    predicted_wage = np.exp(ln_w)

    return {
        "predicted_monthly_wage": round(float(predicted_wage), 2),
        "ln_wage": round(float(ln_w), 4),
        "decomposition": {
            "base": round(7.5, 2),
            "education_contribution": round(0.085 * edu_years, 3),
            "experience_contribution": round(0.05 * exp_years - 0.0006 * (exp_years ** 2), 3),
            "gender_effect": round(np.log(gender_mult.get(gender, 1.0)), 4),
            "ownership_effect": round(np.log(ownership_mult.get(ownership, 1.0)), 4),
            "union_effect": round(np.log(1.06), 4) if union_member else 0,
        },
        "parameters": {
            "education_years": edu_years,
            "experience_years": exp_years,
            "gender": gender,
            "ownership": ownership,
            "union_member": union_member,
        },
    }
