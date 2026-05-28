"""
个体职业实验室 — 明瑟方程 + 迁移 NPV 计算引擎
"""

import numpy as np

# 中国工资基准（分学历，2024年）
CHINA_WAGE_BY_EDU = {
    9: 3500,
    12: 4200,
    15: 5200,
    16: 6200,
    19: 8500,
    22: 11000,
}

EDUCATION_LABELS = {9: "初中", 12: "高中", 15: "大专", 16: "本科", 19: "硕士", 22: "博士"}

CURVE_RESOLUTION = 120  # 至少 120 个平滑点


def calc_mincer(edu: int, exp_peak: int, gen_t: float, spec_t: float, disc: float):
    """
    明瑟收入方程
    edu: 受教育年限
    exp_peak: 工龄峰值（生成 0 到 exp_peak 的向量）
    gen_t: 一般培训投入 (0 或 5)
    spec_t: 特殊培训投入 (0 或 3)
    disc: 歧视系数 (%)
    返回: (exp_vec, wage, wage_disc)
    """
    exp_vec = np.linspace(0, exp_peak, CURVE_RESOLUTION)
    base = 7.0
    r = 0.08 + (0.004 * gen_t) + (0.002 * spec_t)
    ln_w = base + r * edu + 0.05 * exp_vec - 0.0006 * (exp_vec ** 2)
    wage = np.exp(ln_w)
    wage_disc = wage * (1 - disc / 100) if disc > 0 else None
    return exp_vec, wage, wage_disc


def calc_migration_npv(w_home: float, w_city_diff: float,
                        cost_move: float, cost_psych: float, years: int = 20):
    """
    迁移 NPV
    w_home: 家乡月薪(k)
    w_city_diff: 城市月薪优势(k)
    返回: dict {years, npv_cumulative, is_worth, breakeven_year}
    """
    t = np.arange(1, years + 1)
    benefit = w_city_diff * 12
    costs = np.array([cost_move + cost_psych] + [cost_psych] * (years - 1))
    net = benefit - costs
    cum_npv = np.cumsum(net / (1.05 ** t))

    # 找盈亏平衡年
    be_arr = np.where(cum_npv > 0)[0]
    be_yr = int(be_arr[0] + 1) if len(be_arr) > 0 else None
    is_worth = be_yr is not None

    return {
        "years": t.tolist(),
        "npv_cumulative": [round(float(v), 2) for v in cum_npv],
        "is_worth": is_worth,
        "breakeven_year": be_yr,
    }


def calculate_individual(edu_years: int, exp_peak: int, train_type: str,
                          disc_rate: float, migrate: dict) -> dict:
    """
    个体实验室完整计算
    """
    # 培训映射
    gen_t = 5 if train_type == "GENERAL" else 0
    spec_t = 3 if train_type == "SPECIFIC" else 0

    # 明瑟方程
    exp_vec, w_exp, w_disc = calc_mincer(edu_years, exp_peak, gen_t, spec_t, disc_rate)
    _, w_base, _ = calc_mincer(12, exp_peak, 0, 0, 0)

    # 一生总收入积分
    lifetime_edu = np.trapezoid(w_exp, exp_vec)
    lifetime_base = np.trapezoid(w_base, exp_vec)
    premium_pct = round(float((lifetime_edu / lifetime_base - 1) * 100), 1)

    # 盈亏平衡点
    cum_edu = np.cumsum(w_exp)
    cum_base = np.cumsum(w_base)
    diff_cum = cum_edu - cum_base
    be_yr = None
    for i in range(1, len(diff_cum)):
        if diff_cum[i] > 0 and diff_cum[i-1] <= 0:
            be_yr = int(round(exp_vec[i]))
            break

    # 中国实际基准偏离
    real_wage = CHINA_WAGE_BY_EDU.get(edu_years)
    real_wage_dev = round(float((w_exp[0] / real_wage - 1) * 100), 1) if real_wage else None

    # 迁移 NPV
    migration_npv = None
    if migrate.get("is_migrate") and migrate.get("wage_diff", 0) > 0:
        home_base = 5.0  # 家乡基准月薪(k)
        migration_npv = calc_migration_npv(
            w_home=home_base,
            w_city_diff=migrate["wage_diff"],
            cost_move=migrate["cost_move"],
            cost_psych=migrate["cost_psych"],
            years=exp_peak,
        )

    return {
        "wage_curves": {
            "exp_years": [round(float(x), 1) for x in exp_vec],
            "w_exp": [round(float(v), 1) for v in w_exp],
            "w_base": [round(float(v), 1) for v in w_base],
            "w_disc": [round(float(v), 1) for v in w_disc] if w_disc is not None else None,
        },
        "metrics": {
            "premium_pct": premium_pct,
            "breakeven_year": be_yr,
            "real_wage_dev": real_wage_dev,
        },
        "migration_npv": migration_npv,
    }
