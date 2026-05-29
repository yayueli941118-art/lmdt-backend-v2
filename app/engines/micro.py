"""
个体职业实验室 — 明瑟工资方程 + 迁移 NPV 算法引擎
完全解耦 Streamlit 依赖，纯 NumPy 计算
"""

import numpy as np

# ── 中国工资基准（分学历，2024-2025 校准） ──────────────────────
CHINA_WAGE_BY_EDU_2024 = {
    9: 4200.0,
    12: 5500.0,
    16: 9200.0,
    19: 14500.0,
    22: 21000.0,
}

CURVE_RESOLUTION = 80  # 平滑曲线点数


def calc_mincer_core(s: int, exp_vec: np.ndarray, gen_t: float, spec_t: float, disc_pct: float):
    """
    经典明瑟工资方程扩展模型 (Mincer 1974)
    Ln(W) = b0 + b1*S + b2*Exp + b3*Exp² + b4*GenTrain + b5*SpecTrain

    参数校准基于中国长期微观经济数据回归均值。
    """
    b0 = 6.8
    b1 = 0.085       # 教育回报率: 年均 8.5%
    b2 = 0.045       # 早期工作经验回报率
    b3 = -0.0007     # 经验回报率二次项（天花板效应）

    ln_w = b0 + b1 * s + b2 * exp_vec + b3 * (exp_vec ** 2)

    # 培训策略修正
    if gen_t > 0:
        ln_w += 0.08  # 一般培训：全期提升通用生产率
    if spec_t > 0:
        ln_w += -0.05 + 0.004 * exp_vec  # 特殊培训：前期交学费，后期爆发

    w_exp = np.exp(ln_w)
    w_disc = w_exp * (1.0 - disc_pct / 100.0)

    return w_exp, w_disc


def calc_migration_npv_core(remain_years: int, annual_premium: float,
                             c_move: float, c_psych: float):
    """
    劳动力迁移空间套利的净现值动态累积模型 (NPV)
    每年折现率 r = 5%
    """
    t_vec = np.arange(1, remain_years + 1)
    discount_rate = 0.05

    net_flow = np.full(remain_years, annual_premium - c_psych)
    net_flow[0] -= c_move  # 第一年扣除搬迁硬件成本

    discounted_flow = net_flow / ((1 + discount_rate) ** t_vec)
    cum_npv = np.cumsum(discounted_flow)

    return t_vec.tolist(), cum_npv.tolist()


def calculate_individual(
    edu: int,
    exp_peak: int,
    train_type: str,
    disc: float,
    migrate: bool,
    w_diff: float,
    c_move: float,
    c_psych: float,
) -> dict:
    """个体实验室完整计算 → 返回前端契约 JSON"""

    exp_vec = np.linspace(0, exp_peak, CURVE_RESOLUTION)

    # 培训参数映射
    gen_t = 5.0 if "一般" in train_type else 0.0
    spec_t = 3.0 if "特殊" in train_type else 0.0

    # 1. 实验组明瑟方程
    w_exp, w_disc = calc_mincer_core(edu, exp_vec, gen_t, spec_t, disc)

    # 2. 对照组基准线（锁定 12 年高中学历）
    w_base, _ = calc_mincer_core(12, exp_vec, 0.0, 0.0, 0.0)

    # 3. 一生积累资产现值（梯形数值积分）
    lifetime_edu = float(np.trapezoid(w_exp, exp_vec))
    lifetime_base = float(np.trapezoid(w_base, exp_vec))
    premium = ((lifetime_edu / lifetime_base) - 1.0) * 100

    # 4. 教育投资盈亏平衡回本年限
    cum_edu = np.cumsum(w_exp)
    cum_base = np.cumsum(w_base)
    diff_cum = cum_edu - cum_base
    be_idx = np.where(diff_cum > 0)[0]
    breakeven_year = int(exp_vec[be_idx[0]]) if len(be_idx) > 0 and diff_cum[-1] > 0 else None

    # 5. 中国实际工资基准对比
    real_wage_baseline = CHINA_WAGE_BY_EDU_2024.get(edu, 0.0)
    vs_china_baseline = float((w_exp[0] / real_wage_baseline - 1.0) * 100) if real_wage_baseline > 0 else 0.0

    # 6. 迁移 NPV
    migrate_years, migrate_npv = [], []
    is_worth_it = False
    if migrate:
        annual_premium = w_diff * 12.0  # 年尺度溢价 (k)
        migrate_years, migrate_npv = calc_migration_npv_core(
            remain_years=exp_peak,
            annual_premium=annual_premium,
            c_move=c_move,
            c_psych=c_psych,
        )
        is_worth_it = len(np.where(np.array(migrate_npv) > 0)[0]) > 0 if migrate_npv else False

    return {
        "metrics": {
            "lifetime_premium_pct": round(premium, 2),
            "discrimination_loss_pct": disc,
            "vs_china_baseline_pct": round(vs_china_baseline, 2),
            "china_baseline_value": real_wage_baseline,
            "breakeven_year": breakeven_year,
        },
        "charts": {
            "experience_years": [round(float(x), 1) for x in exp_vec],
            "wage_curve_selected": [round(float(v), 1) for v in w_exp],
            "wage_curve_baseline": [round(float(v), 1) for v in w_base],
            "wage_curve_disc": [round(float(v), 1) for v in w_disc],
        },
        "migration": {
            "is_calculated": migrate,
            "years": migrate_years,
            "cumulative_npv": [round(float(n), 2) for n in migrate_npv],
            "is_worth_it": is_worth_it,
        },
    }
