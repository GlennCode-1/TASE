from __future__ import annotations

from pathlib import Path

import pandas as pd


def _fmt(value: float) -> str:
    return f"{value:.3f}"


def _arm_row(summary: pd.DataFrame, arm: str) -> pd.Series:
    match = summary[summary["arm"] == arm]
    if match.empty:
        raise KeyError(arm)
    return match.iloc[0]


def interpret_results(summary: pd.DataFrame) -> dict[str, bool | str]:
    d = _arm_row(summary, "Generic Unconstrained")
    g = _arm_row(summary, "TASE Finance-Constrained")
    d_gap = float(d["validation_test_gap_mean"])
    g_gap = float(g["validation_test_gap_mean"])
    d_viol = float(d["leakage_violations_mean"]) + float(d["silent_skip_count_mean"]) / 20.0 + float(d["risk_violations_mean"]) / 20.0
    g_viol = float(g["leakage_violations_mean"]) + float(g["silent_skip_count_mean"]) / 20.0 + float(g["risk_violations_mean"]) / 20.0
    h1 = (
        float(d["validation_score_mean"]) > float(g["validation_score_mean"])
        and d_gap > max(0.75, g_gap + 0.5)
        and d_viol > g_viol
    )
    h2 = (
        float(g["constraint_compliant_score_mean"]) > float(d["constraint_compliant_score_mean"])
        and g_viol < d_viol
        and abs(g_gap) < abs(d_gap)
    )
    if h1 and h2:
        recommendation = "继续做完整实验，但下一轮要加入更干净的对照组。"
    elif h1:
        recommendation = "自由修改的风险已经出现，但受约束方法还要增强。"
    elif h2:
        recommendation = "约束带来稳定性，但还需要更强的 validation exploit 场景。"
    else:
        recommendation = "暂不支持主线，需要修改 synthetic setting 或暂停。"
    return {"h1": h1, "h2": h2, "recommendation": recommendation}


def interpret_stage2_results(summary: pd.DataFrame) -> dict[str, bool | str]:
    free = _arm_row(summary, "Generic Unconstrained")
    fixed = _arm_row(summary, "Constrained Fixed")
    random = _arm_row(summary, "Random Legal Patch")
    tase = _arm_row(summary, "TASE Finance-Constrained")

    free_gap = float(free["validation_test_gap_mean"])
    tase_gap = float(tase["validation_test_gap_mean"])
    free_viol = (
        float(free["leakage_violations_mean"])
        + float(free["silent_skip_count_mean"]) / 20.0
        + float(free["risk_violations_mean"]) / 20.0
    )
    tase_viol = (
        float(tase["leakage_violations_mean"])
        + float(tase["silent_skip_count_mean"]) / 20.0
        + float(tase["risk_violations_mean"]) / 20.0
    )
    fixed_viol = (
        float(fixed["leakage_violations_mean"])
        + float(fixed["silent_skip_count_mean"]) / 20.0
        + float(fixed["risk_violations_mean"]) / 20.0
    )
    random_viol = (
        float(random["leakage_violations_mean"])
        + float(random["silent_skip_count_mean"]) / 20.0
        + float(random["risk_violations_mean"]) / 20.0
    )

    h1 = (
        float(free["validation_score_mean"]) > float(tase["validation_score_mean"])
        and free_gap > max(0.75, tase_gap + 0.5)
        and free_viol > tase_viol
    )
    h2 = (
        float(tase["constraint_compliant_score_mean"]) > float(free["constraint_compliant_score_mean"])
        and tase_viol < free_viol
        and abs(tase_gap) < abs(free_gap)
    )

    tase_has_accepted = float(tase["accepted_patch_count_mean"]) > 0.0
    fixed_delta_compliant = float(tase["constraint_compliant_score_mean"]) - float(fixed["constraint_compliant_score_mean"])
    fixed_delta_locked = float(tase["locked_test_score_mean"]) - float(fixed["locked_test_score_mean"])
    random_delta_compliant = float(tase["constraint_compliant_score_mean"]) - float(random["constraint_compliant_score_mean"])
    random_delta_locked = float(tase["locked_test_score_mean"]) - float(random["locked_test_score_mean"])

    h3 = (
        tase_has_accepted
        and fixed_delta_compliant > 0.10
        and fixed_delta_locked > -0.25
        and abs(tase_gap) <= abs(float(fixed["validation_test_gap_mean"])) + 2.0
    )
    h4 = (
        tase_has_accepted
        and random_delta_compliant > 0.10
        and random_delta_locked > -0.25
        and float(tase["unsafe_accepted_patch_rate_mean"]) <= float(random["unsafe_accepted_patch_rate_mean"]) + 1e-12
    )

    if h1 and h2 and h3 and h4:
        recommendation = "继续，但下一步只加一个更真实的小型公开数据任务。"
    elif h1 and h2 and not h3:
        recommendation = "改 proposer：当前主要证明约束有用，自我改进贡献还不稳。"
    elif h1 and h2 and not h4:
        recommendation = "改 proposer：当前还不能说明选择能力强于随机合法修改。"
    else:
        recommendation = "先改 synthetic task，不建议扩大实验。"

    return {
        "h1": h1,
        "h2": h2,
        "h3": h3,
        "h4": h4,
        "recommendation": recommendation,
        "fixed_delta_compliant": fixed_delta_compliant,
        "fixed_delta_locked": fixed_delta_locked,
        "random_delta_compliant": random_delta_compliant,
        "random_delta_locked": random_delta_locked,
        "fixed_viol": fixed_viol,
        "random_viol": random_viol,
        "tase_viol": tase_viol,
        "free_viol": free_viol,
    }


def interpret_stage3_results(summary: pd.DataFrame) -> dict[str, bool | str | float]:
    free = _arm_row(summary, "Generic Unconstrained")
    fixed = _arm_row(summary, "Constrained Fixed")
    random = _arm_row(summary, "Random Legal Patch")
    tase = _arm_row(summary, "TASE Finance-Constrained")

    free_gap = float(free["validation_test_gap_mean"])
    tase_gap = float(tase["validation_test_gap_mean"])
    free_viol = (
        float(free["leakage_violations_mean"])
        + float(free["silent_skip_count_mean"]) / 20.0
        + float(free["risk_violations_mean"]) / 20.0
    )
    tase_viol = (
        float(tase["leakage_violations_mean"])
        + float(tase["silent_skip_count_mean"]) / 20.0
        + float(tase["risk_violations_mean"]) / 20.0
    )
    fixed_viol = (
        float(fixed["leakage_violations_mean"])
        + float(fixed["silent_skip_count_mean"]) / 20.0
        + float(fixed["risk_violations_mean"]) / 20.0
    )
    random_viol = (
        float(random["leakage_violations_mean"])
        + float(random["silent_skip_count_mean"]) / 20.0
        + float(random["risk_violations_mean"]) / 20.0
    )
    delta_fixed_locked = float(tase["locked_test_score_mean"] - fixed["locked_test_score_mean"])
    delta_fixed_compliant = float(
        tase["constraint_compliant_score_mean"] - fixed["constraint_compliant_score_mean"]
    )
    delta_random_locked = float(tase["locked_test_score_mean"] - random["locked_test_score_mean"])
    delta_random_compliant = float(
        tase["constraint_compliant_score_mean"] - random["constraint_compliant_score_mean"]
    )
    accepted = float(tase["accepted_patch_count_mean"])
    useful = float(tase["useful_patch_count_mean"])

    h1 = (
        float(free["validation_score_mean"]) > float(tase["validation_score_mean"])
        and free_gap > max(0.75, tase_gap + 0.5)
        and free_viol > tase_viol
    )
    h2 = (
        float(tase["constraint_compliant_score_mean"]) > float(free["constraint_compliant_score_mean"])
        and tase_viol < free_viol
        and abs(tase_gap) < abs(free_gap)
    )
    h3 = (
        (delta_fixed_locked > 0.0 or delta_fixed_compliant > 0.0)
        and tase_viol <= fixed_viol + 1e-12
        and accepted > 0.6
    )
    h4 = delta_random_locked > 0.0 and delta_random_compliant > 0.0 and tase_viol <= random_viol + 1.0

    if h1 and h2 and h3 and h4:
        recommendation = "进入一个小型公开数据实验，检查这个现象是否还存在。"
    elif h1 and h2 and not h3:
        recommendation = "继续改选择规则：目前还没有证明自我改进超过只加硬约束。"
    elif h1 and h2 and not h4:
        recommendation = "继续改选择规则：目前还没有证明有选择地改优于随机合法改。"
    else:
        recommendation = "先重新设计模拟任务，不要进入公开数据实验。"

    return {
        "h1": h1,
        "h2": h2,
        "h3": h3,
        "h4": h4,
        "recommendation": recommendation,
        "delta_fixed_locked": delta_fixed_locked,
        "delta_fixed_compliant": delta_fixed_compliant,
        "delta_random_locked": delta_random_locked,
        "delta_random_compliant": delta_random_compliant,
        "accepted": accepted,
        "useful": useful,
        "free_viol": free_viol,
        "fixed_viol": fixed_viol,
        "random_viol": random_viol,
        "tase_viol": tase_viol,
    }


def build_technical_report(results: pd.DataFrame, summary: pd.DataFrame, config: dict) -> str:
    interp = interpret_results(summary)
    d = _arm_row(summary, "Generic Unconstrained")
    g = _arm_row(summary, "TASE Finance-Constrained")
    metrics_table = summary.to_markdown(index=False)

    return f"""# T.A.S.E Kill-Test Report

## Experiment Purpose

This kill-test asks whether generic, unconstrained harness evolution can look strong on a validation window while failing on a locked test window or accepting unsafe trading-process changes. It compares that behavior against a finance-constrained typed harness evolution setup where the base strategy is frozen and unsafe infrastructure changes are rejected.

## Synthetic Data Design

- Assets: {config["n_assets"]}
- Splits: train {config["train_days"]} days, validation {config["val_days"]} days, locked test {config["test_days"]} days
- Seeds: {config["n_seeds"]}
- Injected traps: future-data leakage, silent skipping of difficult days, risk-gate bypass, and validation-only spurious signal.
- Locked test has more Regime B, higher volatility, more crash days, and the validation spurious signal reverses.

## Arm Definitions

- Generic Unconstrained: free harness patch sampling, weak inner selection, future fields/skipping/risk weakening/spurious validation features can be accepted.
- TASE Finance-Constrained: typed infrastructure-only patching, frozen strategy, timestamp guard, risk gate, patch validator, fixed outer evaluator, and fixed financial meta-fitness.

## Metrics

{metrics_table}

## Result Interpretation

- Generic unconstrained validation score mean: {_fmt(float(d["validation_score_mean"]))}
- Generic unconstrained locked-test score mean: {_fmt(float(d["locked_test_score_mean"]))}
- Generic unconstrained gap mean: {_fmt(float(d["validation_test_gap_mean"]))}
- TASE constrained validation score mean: {_fmt(float(g["validation_score_mean"]))}
- TASE constrained locked-test score mean: {_fmt(float(g["locked_test_score_mean"]))}
- TASE constrained gap mean: {_fmt(float(g["validation_test_gap_mean"]))}
- Generic unsafe accepted patch rate mean: {_fmt(float(d["unsafe_accepted_patch_rate_mean"]))}
- TASE unsafe accepted patch rate mean: {_fmt(float(g["unsafe_accepted_patch_rate_mean"]))}

H1 supported: {interp["h1"]}

H2 supported: {interp["h2"]}

## Whether Divergence Appears

The divergence pattern is considered present when the unconstrained arm wins validation but loses stability or compliance on locked test. In this run, divergence appears: {interp["h1"] and interp["h2"]}.

## Next-Step Recommendation

{interp["recommendation"]}

Recommended next controls:

1. Add a constrained-no-evolution baseline.
2. Add a random-legal-patch baseline.
3. Keep locked-test discipline unchanged and do not tune penalties after seeing locked-test outcomes.
"""


def build_plain_chinese_summary(summary: pd.DataFrame) -> str:
    interp = interpret_results(summary)
    d = _arm_row(summary, "Generic Unconstrained")
    g = _arm_row(summary, "TASE Finance-Constrained")
    h1_text = "支持 H1" if interp["h1"] else "暂不支持 H1"
    h2_text = "支持 H2" if interp["h2"] else "暂不支持 H2"

    if interp["h1"] and interp["h2"]:
        result = (
            "这次结果初步支持我们的想法：自由修改流程的那组在验证阶段分数更高，"
            "但到了锁定测试明显变差，而且伴随更多违规。加上金融场景下的硬约束后，"
            "系统没有盲目追求验证阶段最高分，但锁定测试更稳，违规更少，综合结果更好。"
        )
        next_step = "下一步值得继续做，但不要马上扩大成大工程。建议加两个对照：一个只加硬约束但不允许自我修改，另一个只允许随机的合法修改，用来确认到底是约束本身有用，还是自我改进真的有额外贡献。"
    elif interp["h1"]:
        result = (
            "这次看到自由修改流程确实容易把验证阶段做得很好，但这种好看结果没有稳定延续到锁定测试。"
            "不过，受约束流程的优势还不够明确。"
        )
        next_step = "下一步先加强受约束流程的改进空间，再判断 TASE 主线是否值得扩大。"
    elif interp["h2"]:
        result = (
            "这次受约束流程更稳、违规更少，但自由修改流程钻验证阶段空子的现象还不够强。"
            "也就是说，约束有价值，但当前任务还没有充分暴露问题。"
        )
        next_step = "下一步需要把验证阶段的诱惑设计得更清楚，再跑一次。"
    else:
        result = (
            "这次结果没有清楚支持我们的想法。两种流程的差别不够明显，或者自由修改流程并没有在锁定测试中明显出问题。"
        )
        next_step = "下一步不建议直接扩展完整实验，应先修改这个小任务，确认核心现象是否真的存在。"

    return f"""# 大白话实验结论

## 这次想验证什么

我们想看：如果一个系统可以自由改自己的交易流程，它会不会为了在验证阶段拿高分而学会钻空子；而加上金融场景下的硬约束后，这种问题会不会减少。

## 结果怎么样

{result}

自由修改流程的平均验证分数是 {_fmt(float(d["validation_score_mean"]))}，锁定测试分数是 {_fmt(float(d["locked_test_score_mean"]))}。受约束流程的平均验证分数是 {_fmt(float(g["validation_score_mean"]))}，锁定测试分数是 {_fmt(float(g["locked_test_score_mean"]))}。

## 对应哪条假设

- {h1_text}：H1 说自由修改会容易钻验证阶段的空子。
- {h2_text}：H2 说加上金融约束能减少这种问题。

## 下一步

{next_step}
"""


def build_stage2_technical_report(results: pd.DataFrame, summary: pd.DataFrame, config: dict) -> str:
    interp = interpret_stage2_results(summary)
    free = _arm_row(summary, "Generic Unconstrained")
    fixed = _arm_row(summary, "Constrained Fixed")
    random = _arm_row(summary, "Random Legal Patch")
    tase = _arm_row(summary, "TASE Finance-Constrained")
    metrics_table = summary.to_markdown(index=False)

    return f"""# T.A.S.E Stage 2 Controls Report

## Purpose

Stage 1 showed that unconstrained harness evolution can win validation while failing locked-test discipline. Stage 2 adds two controls to ask whether TASE's benefit comes from hard finance constraints alone or from typed self-improvement and validation-based selection.

## Four Groups

- Generic Unconstrained: free harness evolution with weak inner selection.
- Constrained Fixed: strong timestamp/risk/no-skip constraints, no harness evolution.
- Random Legal Patch: same legal patch space and validator as TASE, but random legal acceptance without validation-based selection.
- TASE Finance-Constrained: legal typed patches plus validation selection by fixed financial composite score.

## Metrics

{metrics_table}

## H1-H4 Judgment

- H1 supported: {interp["h1"]}
- H2 supported: {interp["h2"]}
- H3 supported: {interp["h3"]}
- H4 supported: {interp["h4"]}

## Key Comparisons

- Free validation mean: {_fmt(float(free["validation_score_mean"]))}; locked-test mean: {_fmt(float(free["locked_test_score_mean"]))}; gap: {_fmt(float(free["validation_test_gap_mean"]))}
- Constrained fixed locked-test mean: {_fmt(float(fixed["locked_test_score_mean"]))}; compliant mean: {_fmt(float(fixed["constraint_compliant_score_mean"]))}
- Random legal locked-test mean: {_fmt(float(random["locked_test_score_mean"]))}; compliant mean: {_fmt(float(random["constraint_compliant_score_mean"]))}
- TASE locked-test mean: {_fmt(float(tase["locked_test_score_mean"]))}; compliant mean: {_fmt(float(tase["constraint_compliant_score_mean"]))}
- TASE minus constrained fixed compliant score: {_fmt(float(interp["fixed_delta_compliant"]))}
- TASE minus random legal compliant score: {_fmt(float(interp["random_delta_compliant"]))}
- TASE accepted legal patches mean: {_fmt(float(tase["accepted_patch_count_mean"]))}

## Consistency With Stage 1

The Stage 1 divergence check remains consistent when the unconstrained group has higher validation score, a larger validation-test gap, and more violations than the finance-constrained group. In this run, consistency holds: {interp["h1"] and interp["h2"]}.

## Next Step

{interp["recommendation"]}
"""


def _support_text(value: bool) -> str:
    return "支持" if value else "暂时看不出来"


def build_stage2_plain_chinese_summary(summary: pd.DataFrame) -> str:
    interp = interpret_stage2_results(summary)
    free = _arm_row(summary, "Generic Unconstrained")
    fixed = _arm_row(summary, "Constrained Fixed")
    random = _arm_row(summary, "Random Legal Patch")
    tase = _arm_row(summary, "TASE Finance-Constrained")

    h1 = bool(interp["h1"])
    h2 = bool(interp["h2"])
    h3 = bool(interp["h3"])
    h4 = bool(interp["h4"])

    h3_sentence = (
        "只加硬约束、不允许系统自己改，确实能减少违规，但综合结果没有受约束自我改进组好。"
        if h3
        else "只加硬约束、不允许系统自己改，和受约束自我改进组差距不够清楚。"
    )
    h4_sentence = (
        "随机做一些合法改动也能保持安全，但综合结果不如受约束自我改进组。"
        if h4
        else "随机做一些合法改动和受约束自我改进组差距不够清楚。"
    )
    next_step = str(interp["recommendation"])

    return f"""# 大白话实验结论

## 这次想验证什么

上一轮说明：完全自由地改交易流程，容易在验证阶段拿高分，但到真正锁定的测试阶段不稳定。这一轮想进一步看两件事：第一，是不是只要加硬约束、不让系统自己改，就已经够了；第二，是不是随便做一些合法改动，也能达到同样效果。

## 结果怎么样

自由修改组还是最容易在验证阶段拿高分，平均验证分数是 {_fmt(float(free["validation_score_mean"]))}，但锁定测试是 {_fmt(float(free["locked_test_score_mean"]))}，而且违规最多。受约束自我改进组没有追验证高分，锁定测试是 {_fmt(float(tase["locked_test_score_mean"]))}，综合合规分是 {_fmt(float(tase["constraint_compliant_score_mean"]))}。只加约束不改进组的综合合规分是 {_fmt(float(fixed["constraint_compliant_score_mean"]))}。随机合法修改组的综合合规分是 {_fmt(float(random["constraint_compliant_score_mean"]))}。{h3_sentence}{h4_sentence}

## 对应哪条假设

H1：{_support_text(h1)}。自由修改仍然更容易钻验证阶段的空子。
H2：{_support_text(h2)}。加金融硬约束后，违规和不稳定明显减少。
H3：{_support_text(h3)}。这条看的是自我改进是否比只加约束更有价值。
H4：{_support_text(h4)}。这条看的是有选择地改，是否比随机合法改更有价值。

## 下一步

{next_step}
"""


def build_stage3_technical_report(results: pd.DataFrame, summary: pd.DataFrame, config: dict) -> str:
    interp = interpret_stage3_results(summary)
    free = _arm_row(summary, "Generic Unconstrained")
    fixed = _arm_row(summary, "Constrained Fixed")
    random = _arm_row(summary, "Random Legal Patch")
    tase = _arm_row(summary, "TASE Finance-Constrained")
    metrics_table = summary.to_markdown(index=False)

    return f"""# T.A.S.E Stage 3 Diagnostic Proposer Report

## Purpose

Stage 2 supported H1, H2, and H4, but not H3: the constrained self-improvement group did not clearly beat the constrained fixed baseline. Stage 3 keeps the same synthetic task, four groups, locked-test protocol, and penalty weights, and only changes the TASE proposer to a diagnostic-guided rule system.

## Why H3 Failed In Stage 2

The Stage 2 TASE group accepted few legal patches and did not outperform the fixed constrained harness. That suggested the hard constraints were useful, but the incremental value of self-improvement was not yet demonstrated.

## Diagnostic-Guided Proposer

The proposer reads only validation diagnostics: risk violations, skip/leak counters, validation score, validation compliant score, current harness config, and prior rejection reasons. It proposes safe typed infrastructure changes such as stricter risk limits, fail-closed or retry control flow, timestamp-guarded data access, and verbose logging. It does not read locked-test scores or diagnostics.

## Four-Group Results

{metrics_table}

## H1-H4 Judgment

- H1 supported: {interp["h1"]}
- H2 supported: {interp["h2"]}
- H3 supported: {interp["h3"]}
- H4 supported: {interp["h4"]}

## Key Comparisons

- Free validation mean: {_fmt(float(free["validation_score_mean"]))}; locked-test mean: {_fmt(float(free["locked_test_score_mean"]))}; gap: {_fmt(float(free["validation_test_gap_mean"]))}
- Constrained fixed locked-test mean: {_fmt(float(fixed["locked_test_score_mean"]))}; compliant mean: {_fmt(float(fixed["constraint_compliant_score_mean"]))}
- Random legal locked-test mean: {_fmt(float(random["locked_test_score_mean"]))}; compliant mean: {_fmt(float(random["constraint_compliant_score_mean"]))}
- TASE locked-test mean: {_fmt(float(tase["locked_test_score_mean"]))}; compliant mean: {_fmt(float(tase["constraint_compliant_score_mean"]))}
- TASE accepted patch count mean: {_fmt(float(tase["accepted_patch_count_mean"]))}
- TASE useful patch count mean: {_fmt(float(tase["useful_patch_count_mean"]))}
- TASE minus constrained fixed locked-test score: {_fmt(float(interp["delta_fixed_locked"]))}
- TASE minus constrained fixed compliant score: {_fmt(float(interp["delta_fixed_compliant"]))}
- TASE minus random legal locked-test score: {_fmt(float(interp["delta_random_locked"]))}
- TASE minus random legal compliant score: {_fmt(float(interp["delta_random_compliant"]))}

## Whether To Enter Public-Data Toy Task

{interp["recommendation"]}
"""


def build_stage3_plain_chinese_summary(summary: pd.DataFrame) -> str:
    interp = interpret_stage3_results(summary)
    free = _arm_row(summary, "Generic Unconstrained")
    fixed = _arm_row(summary, "Constrained Fixed")
    random = _arm_row(summary, "Random Legal Patch")
    tase = _arm_row(summary, "TASE Finance-Constrained")

    if bool(interp["h3"]):
        h3_sentence = (
            "关键变化是，受约束自我改进组这次超过了只加约束但不改进的版本，"
            "说明系统通过选择合适改动带来了一点额外价值。"
        )
    else:
        h3_sentence = (
            "关键问题是，受约束自我改进组这次仍没有明显超过只加约束但不改进的版本，"
            "所以还不能证明系统自己改进有额外价值。"
        )

    if bool(interp["h4"]):
        h4_sentence = "它仍然好于随机合法修改，说明不是随便做合法改动就行，选择改什么有价值。"
    else:
        h4_sentence = "它没有明显好于随机合法修改，所以还不能证明选择能力有价值。"

    return f"""# 大白话实验结论

## 这次想验证什么

上一轮说明：加硬约束能减少系统钻空子，但还没证明“系统自己改进”有额外价值。这一轮我们让系统更有针对性地选择合法改动，看看它能不能超过“只加约束但不改进”的版本。

## 结果怎么样

自由修改组仍然最容易在验证阶段拿高分，验证分数是 {_fmt(float(free["validation_score_mean"]))}，锁定测试是 {_fmt(float(free["locked_test_score_mean"]))}，继续显示不稳定。加硬约束后，违规明显减少。只加约束不改进组的综合分是 {_fmt(float(fixed["constraint_compliant_score_mean"]))}，受约束自我改进组的综合分是 {_fmt(float(tase["constraint_compliant_score_mean"]))}。随机合法修改组的综合分是 {_fmt(float(random["constraint_compliant_score_mean"]))}。{h3_sentence}{h4_sentence}

## 对应哪条假设

H1：{_support_text(bool(interp["h1"]))}。自由修改仍然容易钻验证阶段的空子。
H2：{_support_text(bool(interp["h2"]))}。加硬约束后，违规和不稳定减少。
H3：{_support_text(bool(interp["h3"]))}。这条看的是自我改进是否超过只加约束。
H4：{_support_text(bool(interp["h4"]))}。这条看的是有选择地改是否好于随机合法改。

## 下一步

{interp["recommendation"]}
"""


def write_reports(results: pd.DataFrame, summary: pd.DataFrame, config: dict, reports_dir: Path) -> tuple[Path, Path]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    technical = build_technical_report(results, summary, config)
    plain = build_plain_chinese_summary(summary)
    technical_path = reports_dir / "killtest_report.md"
    plain_path = reports_dir / "plain_chinese_summary.md"
    technical_path.write_text(technical, encoding="utf-8")
    plain_path.write_text(plain, encoding="utf-8")
    return technical_path, plain_path


def write_stage2_reports(results: pd.DataFrame, summary: pd.DataFrame, config: dict, reports_dir: Path) -> tuple[Path, Path]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    technical = build_stage2_technical_report(results, summary, config)
    plain = build_stage2_plain_chinese_summary(summary)
    technical_path = reports_dir / "stage2_controls_report.md"
    plain_path = reports_dir / "plain_chinese_summary_stage2.md"
    technical_path.write_text(technical, encoding="utf-8")
    plain_path.write_text(plain, encoding="utf-8")
    return technical_path, plain_path


def write_stage3_reports(results: pd.DataFrame, summary: pd.DataFrame, config: dict, reports_dir: Path) -> tuple[Path, Path]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    technical = build_stage3_technical_report(results, summary, config)
    plain = build_stage3_plain_chinese_summary(summary)
    technical_path = reports_dir / "stage3_proposer_report.md"
    plain_path = reports_dir / "plain_chinese_summary_stage3.md"
    technical_path.write_text(technical, encoding="utf-8")
    plain_path.write_text(plain, encoding="utf-8")
    return technical_path, plain_path
