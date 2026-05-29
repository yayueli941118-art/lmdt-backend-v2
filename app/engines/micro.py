"""
个体职业实验室 — 明瑟工资方程 + 迁移 NPV 算法引擎
统一年龄轴 (18-60)，包含教育投资的机会成本
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

AGE_START = 18
AGE_END = 60
CURVE_RESOLUTION = AGE_END - AGE_START + 1  # 43个点，每个年龄一个

# 上学期间月度折算成本（含学费+生活费，单位：元/月）
TUITION_MONTHLY = 2500.0


def _mincer_at_given_exp(edu: float, exp: float, gen_t: float, spec_t: float, disc_pct: float) -> float:
    """
    单点明瑟工资计算
    Ln(W) = b0 + b1*S + b2*Exp + b3*Exp² + 培训修正
    """
    b0, b1, b2, b3 = 7.5, 0.10, 0.06, -0.001

    if exp < 0:
        return 0.0

    ln_w = b0 + b1 * edu + b2 * exp + b3 * (exp ** 2)
    if gen_t > 0:
        ln_w += 0.08
    if spec_t > 0:
        ln_w += -0.05 + 0.004 * exp

    w = np.exp(ln_w)
    w = w * (1.0 - disc_pct / 100.0)
    return float(w)


def calc_migration_npv_core(remain_years: int, annual_premium: float,
                             c_move: float, c_psych: float):
    """迁移 NPV"""
    t_vec = np.arange(1, remain_years + 1)
    discount_rate = 0.05
    net_flow = np.full(remain_years, annual_premium - c_psych)
    net_flow[0] -= c_move
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
    """
    基于年龄轴的个体实验室计算
    - 对照组 (S=12): 18岁开始工作
    - 实验组 (S=edu): edu-6 岁之前为读书期，之后工作
    返回包含红区(投资期)和绿区(回报期)数据的完整契约
    """
    gen_t = 5.0 if "一般" in train_type else 0.0
    spec_t = 3.0 if "特殊" in train_type else 0.0

    age_vec = np.arange(AGE_START, AGE_END + 1, dtype=int)
    n = len(age_vec)

    baseline_wage = np.zeros(n)   # 高中组 (S=12)
    selected_wage = np.zeros(n)   # 选择组
    selected_gross = np.zeros(n)  # 选择组（不含歧视，用于凹区基准线）

    for i, age in enumerate(age_vec):
        # ── 对照组：18岁起工作 ──
        if age >= 18:
            baseline_wage[i] = _mincer_at_given_exp(12, age - 18, 0, 0, 0)

        # ── 选择组 ──
        work_start_age = edu  # 用受教育年限当作开始工作年龄的简化

        if age < work_start_age:
            # 在读期间：负的机会成本（放弃的工资+学费）
            forgone = baseline_wage[i]  # 高中毕业此时能赚的
            selected_gross[i] = -forgone
            selected_wage[i] = -(TUITION_MONTHLY + forgone)
        else:
            gross = _mincer_at_given_exp(edu, age - work_start_age, gen_t, spec_t, 0)
            selected_gross[i] = gross
            selected_wage[i] = _mincer_at_given_exp(edu, age - work_start_age, gen_t, spec_t, disc)

    # ── 累积净现值（含教育期成本） ──
    baseline_cum = np.cumsum(baseline_wage)
    selected_cum = np.cumsum(selected_wage)

    # 终身总收入溢价（基于累积）
    lifetime_selected = float(selected_cum[-1])
    lifetime_baseline = float(baseline_cum[-1])
    premium = ((lifetime_selected / lifetime_baseline) - 1.0) * 100 if lifetime_baseline > 0 else 0.0

    # 回本年：selected_cum > baseline_cum 的第一年
    diff_cum = selected_cum - baseline_cum
    be_idx_arr = np.where(diff_cum > 0)[0]
    breakeven_age = int(age_vec[be_idx_arr[0]]) if len(be_idx_arr) > 0 else None

    # 工资反超年：selected_wage > baseline_wage 的第一年（已有工作后）
    crossover_age = None
    for i in range(n):
        if age_vec[i] >= edu and selected_wage[i] > baseline_wage[i]:
            crossover_age = int(age_vec[i])
            break

    # ── 歧视轨迹 ──
    disc_wage = selected_gross * (1.0 - disc / 100.0) if disc > 0 else selected_wage.copy()

    # ── 中国基准对比 ──
    real_wage_baseline = CHINA_WAGE_BY_EDU_2024.get(edu, 0.0)
    first_work_age = edu
    first_work_idx = max(0, first_work_age - AGE_START)
    vs_china_baseline = float((selected_gross[first_work_idx] / real_wage_baseline - 1.0) * 100) if real_wage_baseline > 0 else 0.0

    # ── 迁移 NPV ──
    migrate_years, migrate_npv_list = [], []
    is_worth_it = False
    if migrate:
        annual_premium = w_diff * 12.0
        migrate_years, migrate_npv_list = calc_migration_npv_core(
            remain_years=exp_peak,
            annual_premium=annual_premium,
            c_move=c_move,
            c_psych=c_psych,
        )
        is_worth_it = len(np.where(np.array(migrate_npv_list) > 0)[0]) > 0 if migrate_npv_list else False

    return {
        "metrics": {
            "lifetime_premium_pct": round(premium, 2),
            "discrimination_loss_pct": disc,
            "vs_china_baseline_pct": round(vs_china_baseline, 2),
            "china_baseline_value": real_wage_baseline,
            "breakeven_age": breakeven_age,
            "crossover_age": crossover_age,
        },
        "charts": {
            "age_years": [int(a) for a in age_vec],
            "wage_curve_selected": [round(float(v), 1) for v in selected_wage],
            "wage_curve_baseline": [round(float(v), 1) for v in baseline_wage],
            "wage_curve_disc": [round(float(v), 1) for v in disc_wage],
            "wage_curve_selected_gross": [round(float(v), 1) for v in selected_gross],
        },
        "migration": {
            "is_calculated": migrate,
            "years": migrate_years,
            "cumulative_npv": [round(float(n), 2) for n in migrate_npv_list],
            "is_worth_it": is_worth_it,
        },
    }
