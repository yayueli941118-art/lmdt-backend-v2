"""
歧视经济学引擎 — Oaxaca-Blinder 工资分解
参考：Oaxaca (1973), Blinder (1973)
"""

import numpy as np
from typing import Optional


def oaxaca_blinder_decompose(
    group_a_wages: list[float],
    group_b_wages: list[float],
    group_a_edu: list[float],
    group_b_edu: list[float],
    group_a_exp: list[float],
    group_b_exp: list[float],
) -> dict:
    """
    Oaxaca-Blinder 工资歧视分解

    将两组的平均工资差异分解为：
    1. 禀赋效应 (Endowment Effect) — 特征差异可解释的部分
    2. 系数效应 (Coefficient Effect) — 不可解释的歧视部分
    3. 交互效应 (Interaction Effect)

    Parameters:
    - group_a_wages, group_b_wages: 两组对数工资
    - group_a_edu, group_b_edu: 两组受教育年限
    - group_a_exp, group_b_exp: 两组工作经验年限

    Returns:
    - 完整的 Oaxaca-Blinder 分解结果
    """
    # 转为 numpy
    ln_w_a = np.log(np.array(group_a_wages, dtype=float))
    ln_w_b = np.log(np.array(group_b_wages, dtype=float))
    edu_a = np.array(group_a_edu, dtype=float)
    edu_b = np.array(group_b_edu, dtype=float)
    exp_a = np.array(group_a_exp, dtype=float)
    exp_b = np.array(group_b_exp, dtype=float)

    # 构建设计矩阵 (edu, exp, exp^2)
    X_a = np.column_stack([np.ones_like(edu_a), edu_a, exp_a, exp_a ** 2])
    X_b = np.column_stack([np.ones_like(edu_b), edu_b, exp_b, exp_b ** 2])

    # OLS 回归
    try:
        beta_a = np.linalg.lstsq(X_a, ln_w_a, rcond=None)[0]
        beta_b = np.linalg.lstsq(X_b, ln_w_b, rcond=None)[0]
    except np.linalg.LinAlgError:
        beta_a = np.zeros(4)
        beta_b = np.zeros(4)

    # 均值
    X_a_mean = X_a.mean(axis=0)
    X_b_mean = X_b.mean(axis=0)

    ln_w_a_mean = ln_w_a.mean()
    ln_w_b_mean = ln_w_b.mean()
    gap = ln_w_b_mean - ln_w_a_mean  # B 组相对于 A 组的工资差距

    # 三因素分解 (Jann 2008)
    # gap = (X̄_B - X̄_A)'β_A  +  X̄_A'(β_B - β_A)  +  (X̄_B - X̄_A)'(β_B - β_A)
    #        endowment            coefficient           interaction
    endowment = float(np.dot(X_b_mean - X_a_mean, beta_a))
    coefficient = float(np.dot(X_a_mean, beta_b - beta_a))
    interaction = float(np.dot(X_b_mean - X_a_mean, beta_b - beta_a))

    # 逐变量分解
    var_names = ["常数项", "受教育年限", "工作经验", "经验²"]
    var_decomp = []
    for i, name in enumerate(var_names):
        e_i = float((X_b_mean[i] - X_a_mean[i]) * beta_a[i])
        c_i = float(X_a_mean[i] * (beta_b[i] - beta_a[i]))
        i_i = float((X_b_mean[i] - X_a_mean[i]) * (beta_b[i] - beta_a[i]))
        var_decomp.append({
            "variable": name,
            "endowment": round(e_i, 4),
            "coefficient": round(c_i, 4),
            "interaction": round(i_i, 4),
            "total": round(e_i + c_i + i_i, 4),
        })

    # 可解释比例
    explained_pct = round(abs(endowment) / (abs(gap) + 1e-12) * 100, 1)
    unexplained_pct = round(100 - explained_pct, 1)

    # 组间统计
    def group_stats(wages, edu, exp):
        return {
            "mean_wage": round(float(np.mean(wages)), 2),
            "median_wage": round(float(np.median(wages)), 2),
            "std_wage": round(float(np.std(wages)), 2),
            "mean_edu": round(float(np.mean(edu)), 2),
            "mean_exp": round(float(np.mean(exp)), 2),
            "sample_size": len(wages),
        }

    return {
        "decomposition": {
            "total_gap_ln": round(gap, 4),
            "total_gap_pct": round((np.exp(gap) - 1) * 100, 2),
            "endowment_effect": round(endowment, 4),
            "coefficient_effect": round(coefficient, 4),
            "interaction_effect": round(interaction, 4),
            "explained_pct": explained_pct,
            "unexplained_pct": unexplained_pct,
            "gap_direction": "B组相对A组" if gap > 0 else "A组相对B组",
        },
        "by_variable": var_decomp,
        "coefficients": {
            "group_a": [round(float(b), 6) for b in beta_a],
            "group_b": [round(float(b), 6) for b in beta_b],
            "coefficient_names": var_names,
            "r_squared_a": round(float(1 - np.sum((ln_w_a - X_a @ beta_a) ** 2) / np.sum((ln_w_a - ln_w_a_mean) ** 2)), 4),
            "r_squared_b": round(float(1 - np.sum((ln_w_b - X_b @ beta_b) ** 2) / np.sum((ln_w_b - ln_w_b_mean) ** 2)), 4),
        },
        "group_a": group_stats(np.array(group_a_wages), edu_a, exp_a),
        "group_b": group_stats(np.array(group_b_wages), edu_b, exp_b),
    }
