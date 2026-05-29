"""
个体职业实验室 — 明瑟工资方程 + 迁移 NPV 算法引擎
完全向量化 NumPy 实现，无循环分支
"""

import numpy as np
import numpy_financial as npf

# ── 中国工资基准（分学历，2024-2025 校准） ──────────────────────
CHINA_WAGE_BY_EDU_2024 = {
    9: 4200.0,
    12: 5500.0,
    16: 9200.0,
    19: 14500.0,
    22: 21000.0,
}


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
    """完全向量化的个体实验室计算"""

    # 1. 统一 18-60 岁生命周期年龄向量
    age_vec = np.arange(18, 61, dtype=float)

    # 2. 动态毕业年龄：6岁入学 + 受教育年限
    grad_age = edu  # 简化：18高中毕业(edu=12→18)，22本科(edu=16→22)，25硕士(19)，28博士(22)
    # 实际毕业年龄 = 18 + (edu - 12) = edu + 6 → grad_age = edu + 6
    grad_age = edu + 6

    # 3. 对照组（高中毕业，18岁入职，无培训，无歧视）
    exp_base = np.maximum(0, age_vec - 18)
    ln_w_base = 7.5 + 0.085 * 12 + 0.06 * exp_base - 0.001 * (exp_base ** 2)
    w_base = np.exp(ln_w_base)

    # 4. 实验组（毕业后开始累积工龄）
    exp_edu = np.maximum(0, age_vec - grad_age)
    ln_w_edu = 7.5 + 0.10 * edu + 0.06 * exp_edu - 0.001 * (exp_edu ** 2)

    # 培训效应
    if "一般" in train_type:
        ln_w_edu += 0.08
    elif "特殊" in train_type:
        ln_w_edu += -0.05 + 0.004 * exp_edu

    w_edu_raw = np.exp(ln_w_edu)

    # 核心修正：毕业前收入为负数（学费+机会成本），毕业后开始获取明瑟溢价
    w_exp = np.where(age_vec < grad_age, -2.0, w_edu_raw)

    # 5. 歧视受损曲线（毕业年龄拦截）
    w_disc_raw = w_edu_raw * (1.0 - disc / 100.0)
    w_disc = np.where(age_vec < grad_age, -2.0, w_disc_raw)

    # 6. 终身资产总总收入提升率（梯形积分）
    lifetime_edu = float(np.trapezoid(w_exp, age_vec))
    lifetime_base = float(np.trapezoid(w_base, age_vec))
    premium = ((lifetime_edu / lifetime_base) - 1.0) * 100.0

    # 回本年龄：累积资产交叉反超点
    cum_edu = np.cumsum(w_exp)
    cum_base = np.cumsum(w_base)
    be_idx = np.where(cum_edu > cum_base)[0]
    breakeven_age = int(age_vec[be_idx[0]]) if len(be_idx) > 0 and (cum_edu[-1] > cum_base[-1]) else None

    # 内部收益率 IRR：净现金流差额 (w_exp - w_base) 的内部报酬率
    net_cf = w_exp - w_base
    try:
        irr_raw = npf.irr(net_cf)
        irr_pct = float(irr_raw * 100) if irr_raw > 0 else 0.0
    except Exception:
        irr_pct = 0.0

    # 工资反超年龄：毕业后工资首次高于高中生的年龄
    crossover_age = None
    mask_working = age_vec >= grad_age
    crossover_idx = np.where(mask_working & (w_exp > w_base))[0]
    if len(crossover_idx) > 0:
        crossover_age = int(age_vec[crossover_idx[0]])

    # 7. 中国实际基准对比
    real_wage = CHINA_WAGE_BY_EDU_2024.get(edu, 0.0)
    post_grad_idx = np.where(age_vec >= grad_age)[0]
    vs_china = 0.0
    if real_wage > 0 and len(post_grad_idx) > 0:
        first_idx = post_grad_idx[0]
        vs_china = float((w_edu_raw[first_idx] / real_wage - 1.0) * 100)

    # 8. 空间迁移套利 NPV
    migrate_years, migrate_npv_list = [], []
    is_worth_it = False
    if migrate:
        t_max = 60 - grad_age
        if t_max > 0:
            t_vec = np.arange(1, t_max + 1)
            net_flow = np.full(t_max, w_diff * 12.0 - c_psych)
            net_flow[0] -= c_move
            discounted = net_flow / ((1 + 0.05) ** t_vec)
            migrate_years = (grad_age + t_vec).tolist()
            migrate_npv_list = np.cumsum(discounted).tolist()
            is_worth_it = migrate_npv_list[-1] > 0 if migrate_npv_list else False

    return {
        "metrics": {
            "lifetime_premium_pct": round(premium, 2),
            "discrimination_loss_pct": disc,
            "vs_china_baseline_pct": round(vs_china, 2),
            "china_baseline_value": real_wage,
            "breakeven_age": breakeven_age,
            "crossover_age": crossover_age,
            "irr_pct": round(irr_pct, 2),
        },
        "charts": {
            "age_years": [int(a) for a in age_vec],
            "wage_curve_selected": [round(float(v), 2) for v in w_exp],
            "wage_curve_baseline": [round(float(v), 2) for v in w_base],
            "wage_curve_disc": [round(float(v), 2) for v in w_disc],
            "wage_curve_selected_gross": [round(float(v), 2) for v in w_edu_raw],
        },
        "migration": {
            "is_calculated": migrate,
            "years": migrate_years,
            "cumulative_npv": [round(float(n), 2) for n in migrate_npv_list],
            "is_worth_it": is_worth_it,
        },
    }
