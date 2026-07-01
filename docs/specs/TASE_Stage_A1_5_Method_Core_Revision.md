# TASE Stage A1.5 — Method-Core Revision
## Typed Workflow Patch Language + Revised Experiment Specification

## 0. 本文件目的

Stage A1.5 的目的，是把 TASE Direction A 从“LLM meta-agent 搜 workflow 配置”升级成一个更像 AAAI 方法论文的核心方法：

> Typed Workflow Patch Language + invariant-preserving patch executor + finance-specific reliability objective + contextual patch policy

此前 Stage A2 外部审查给出的核心结论是：

- Claude：PASS WITH MAJOR REVISIONS；
- Gemini：Ready after minor spec fixes；
- Grok：当前版本 AAAI 风险高，除非补强 method contribution。

因此，不能直接进入 Codex full implementation。必须先补强方法核心，否则 Direction A 容易被 reviewer 打成：

> LLM-wrapped model selection / quant AutoML / alpha mining wrapper.

---

## 1. Stage A1.5 的核心修订

Stage A1.5 做六件事：

1. 定义 Typed Workflow Patch Language；
2. 定义 patch semantics 和 invariant-preserving executor；
3. 将 H0 拆成 H0a / H0b；
4. 将 Classic CSCV / PBO Selector 提升为主对手；
5. 加入 non-agent contextual workflow selector baseline；
6. 预注册 performance non-inferiority margin。

---

## 2. 修订后的核心 claim

TASE 不能写成：

> We use an LLM meta-agent to search better workflow configurations.

这太弱，也太像 AutoML。

TASE 应写成：

> We introduce a typed workflow patch language for finance-constrained strategy-discovery agents. A meta-agent proposes patches in this language, while a deterministic patch executor enforces invariants over candidate signals, evaluation budgets, archives, and locked-test isolation. TASE optimizes selection reliability under gameable financial evaluators, with locked-test performance treated as a non-inferiority constraint.

中文：

> 本文提出一个面向金融策略发现 agent 的 typed workflow patch language。Meta-agent 只能用这种类型化语言提出 workflow patch，随后由 deterministic patch executor 执行，并强制检查候选信号不变、搜索预算不变、归档完整、locked-test 隔离等不变量。TASE 优化的不是 raw return，而是在 gameable financial evaluator 下的 selection reliability；locked-test performance 只作为不显著变差的约束。

---

## 3. Typed Workflow Patch Language

### 3.1 设计原则

TASE patch 不能是自然语言，也不能是任意 Python code。

合法 patch 必须是结构化 JSON / YAML object：

```yaml
patch_id: string
patch_type: enum
target_stage: enum
operation: enum
parameters: dict
preconditions: list
expected_effect: string
safety_tags: list
```

Meta-agent 只能选择或组合预定义 patch type。执行 patch 的不是 LLM，而是 deterministic patch executor。

---

## 4. Patch Type 定义

### 4.1 ValidationSchedulePatch

用途：改变 validation 如何组织，但不改变 raw data、locked test 或 candidate P&L。

```yaml
patch_type: ValidationSchedulePatch
target_stage: validation
operation: set_validation_scheme
parameters:
  scheme: CSCV_10
  aggregation: median_rank
```

允许字段：

- scheme: simple_walk_forward / expanding_walk_forward / CSCV_10 / CSCV_20 / regime_split_validation
- aggregation: mean_rank / median_rank / worst_decile_rank / stability_weighted_rank

禁止字段：

- locked_test_window；
- transaction_cost；
- raw_return_series；
- feature_availability；
- future_return；
- final_metric_after_validation。

### 4.2 PruningRulePatch

用途：改变候选如何被剪枝。

```yaml
patch_type: PruningRulePatch
target_stage: candidate_filtering
operation: set_pruning_rule
parameters:
  metric: pbo_adjusted_sharpe
  threshold: pre_registered_medium
  min_folds_survived: 4
```

允许字段：

- metric: validation_sharpe / pbo_adjusted_sharpe / degradation_adjusted_return / turnover_adjusted_return / cvar_adjusted_score
- threshold: pre_registered_low / pre_registered_medium / pre_registered_high
- min_folds_survived: 3 / 4 / 5

禁止：

- arbitrary numeric threshold generated after seeing validation distribution；
- locked-test metric；
- post-hoc threshold search outside allowed set。

### 4.3 PenaltyUsagePatch

用途：决定 workflow 是否启用 PBO / turnover / drawdown / cost / stability penalty。

```yaml
patch_type: PenaltyUsagePatch
target_stage: scoring
operation: enable_penalty
parameters:
  penalty_type: PBO
  weight: pre_registered_medium
```

允许 penalty_type：

- PBO
- turnover
- drawdown
- CVaR
- transaction_cost
- candidate_instability
- ensemble_concentration

允许 weight：

- pre_registered_low
- pre_registered_medium
- pre_registered_high

禁止：

- continuous weight tuning after validation；
- metric weight chosen from locked test；
- weakening transaction cost。

### 4.4 CriticLoopPatch

用途：决定是否加入 critic / reviewer loop。

```yaml
patch_type: CriticLoopPatch
target_stage: review
operation: add_reviewer
parameters:
  reviewer_type: leakage_reviewer
  decision_rule: veto_if_fail
```

允许 reviewer_type：

- leakage_reviewer
- turnover_reviewer
- drawdown_reviewer
- regime_stability_reviewer
- diversity_reviewer
- archive_consistency_reviewer

允许 decision_rule：

- veto_if_fail
- require_two_passes
- downgrade_score
- retest_candidate

禁止：

- reviewer reads locked test；
- reviewer changes candidate formula；
- reviewer changes transaction cost；
- reviewer hides rejected candidate。

### 4.5 EnsembleRulePatch

用途：改变 accepted candidates 如何组合。

```yaml
patch_type: EnsembleRulePatch
target_stage: ensemble
operation: set_ensemble_rule
parameters:
  rule: diversity_constrained_top_k
  k: 10
  weight_scheme: inverse_turnover
```

允许 rule：

- top_k_by_reliability
- diversity_constrained_top_k
- cluster_representative_selection
- stability_weighted_selection

允许 weight_scheme：

- equal_weight
- inverse_turnover
- inverse_volatility
- reliability_weighted

禁止：

- using locked-test weights；
- selecting candidates based on locked performance；
- changing candidate P&L curve；
- adding new candidates。

### 4.6 ArchivePolicyPatch

用途：改变 accepted / rejected / failed candidate archive 的使用方式。

```yaml
patch_type: ArchivePolicyPatch
target_stage: memory
operation: set_retrieval_policy
parameters:
  retrieval: similar_failure_avoidance
  use_rejected_archive: true
```

允许 retrieval：

- accepted_only
- rejected_failure_avoidance
- similar_failure_avoidance
- regime_matched_retrieval

禁止：

- deleting rejected candidates；
- hiding failed candidates；
- editing archived metrics；
- using locked-test results in archive retrieval。

### 4.7 RetestRollbackPatch

用途：决定异常候选是否复测，以及 workflow patch 是否回滚。

```yaml
patch_type: RetestRollbackPatch
target_stage: diagnostics
operation: set_retest_policy
parameters:
  trigger: high_validation_low_stability
  action: retest_on_alternative_validation
```

允许 trigger：

- high_validation_low_stability
- high_turnover
- high_pbo
- critic_disagreement
- archive_conflict

允许 action：

- retest_on_alternative_validation
- downgrade_candidate
- reject_candidate
- rollback_last_patch

禁止：

- retest on locked test；
- change final metric；
- hide retest failure。

---

## 5. Patch Executor Semantics

每个 patch 经过四步执行：

### Step 1：Schema Validation

检查 patch 是否符合 typed schema。

失败条件：

- patch_type 不存在；
- operation 不允许；
- parameters 含 forbidden field；
- parameter value 不在 allowed set；
- patch 尝试写 Python code；
- patch 含自然语言指令但无结构化字段。

### Step 2：Precondition Check

检查 patch 是否适用于当前 workflow state。

示例：

- CSCV aggregation 需要足够 fold；
- regime_split_validation 需要 regime label；
- ensemble_rule 需要 accepted candidate count >= k；
- archive retrieval 需要 archive 非空。

### Step 3：Invariant Check

执行 patch 前后必须保持：

- per-candidate raw signal invariant；
- per-candidate P&L curve invariant；
- candidate budget invariant；
- transaction cost invariant；
- locked-test isolation；
- archive completeness；
- failed candidate retention；
- feature availability rule invariant；
- hard leakage gate invariant。

### Step 4：Apply Patch

只有前三步通过，patch 才能写入 workflow config。

执行结果记录到：

- workflow_patch_log.csv；
- rejected_patch_log.csv；
- invariant_gate_report.csv；
- archive_completeness_report.csv。

---

## 6. 核心不变量

### 6.1 Candidate Invariance

对于每个 candidate：

```text
signal_before(candidate_id) == signal_after(candidate_id)
pnl_before(candidate_id) == pnl_after(candidate_id)
turnover_before(candidate_id) == turnover_after(candidate_id)
cost_adjusted_pnl_before(candidate_id) == cost_adjusted_pnl_after(candidate_id)
```

通过 hash 检查：

```text
candidate_signal_hash
candidate_pnl_hash
candidate_turnover_hash
candidate_cost_pnl_hash
```

### 6.2 Budget Invariance

所有 searchable arms 必须满足：

```text
candidate_generation_budget equal
candidate_evaluation_budget equal
workflow_patch_budget equal
failed_candidates counted
invalid_candidates counted
retested_candidates counted
```

### 6.3 Archive Completeness

必须保留：

- accepted candidates；
- rejected candidates；
- failed candidates；
- invalid candidates；
- retested candidates；
- patch rejected by schema；
- patch rejected by invariant gate。

### 6.4 Locked-Test Isolation

Workflow patch 不能读取：

- locked-test return；
- locked-test Sharpe；
- locked-test ranking；
- locked-test degradation；
- locked-test PBO；
- locked-test selected ensemble result。

Locked test 只能在 final evaluation stage 被调用。

---

## 7. H0 修订：H0a + H0b

原 H0 “no single fixed workflow dominates” 不够。必须拆成：

### H0a：Workflow Heterogeneity Exists

不同 fold / regime / candidate-pool distribution 下，最佳 fixed workflow 不同。

指标：

- workflow ranking variance；
- Kendall / Spearman rank instability；
- best workflow turnover across folds；
- oracle fixed workflow vs deployable fixed workflow gap。

### H0b：Workflow Heterogeneity Is Predictable From Past-Only Diagnostics

最佳 workflow 的变化不是纯噪声，而是能被 past-only diagnostics 预测。

Past-only diagnostics 包括：

- validation distribution dispersion；
- candidate correlation / clustering；
- effective independent candidate count；
- turnover distribution；
- PBO distribution；
- regime volatility；
- drawdown clustering；
- candidate family composition；
- validation stability score；
- archive failure pattern。

H0b baseline：

- random regime-to-workflow mapping；
- non-agent contextual selector；
- TASE contextual patch policy。

H0b 支持条件：

> Past-only diagnostics predict next-fold best workflow better than random mapping, and TASE improves over non-agent contextual selector.

H0b 不支持时：

> self-evolution 主张降级；TASE 只能写成 diagnostic / protocol / workflow selection study。

---

## 8. CSCV / PBO Selector 作为主对手

Classic CSCV / PBO-based Selector 不是普通 baseline，而是主对手。

原因：

> TASE 的主因变量 PBO / false-discovery / degradation 正是 CSCV / Deflated Sharpe / Reality Check 被设计来处理的问题。

因此必须新增：

### H5-CSCV

TASE 相比 Classic CSCV / PBO Selector，是否在 selection reliability 上有边际增量？

成功条件：

- TASE − CSCV 在至少两个 primary reliability metrics 上 paired CI 改善；
- performance non-inferiority 成立；
- TASE 不靠更多 candidate evaluations；
- TASE 不靠新增 operator；
- TASE 不靠更宽 budget。

打平 CSCV 时：

> 不算支持 TASE，只能说明 TASE 复现了经典方法。

还必须做 ablation：

### PBO-Patch Ablation

关闭 TASE 的 PBO penalty patch 后：

- 如果 performance / reliability 不塌，说明 TASE 的增量来自非-CSCV workflow decisions；
- 如果显著变差，说明 TASE 主要依赖 CSCV/PBO，novelty 弱化。

---

## 9. Non-Agent Contextual Workflow Selector Baseline

必须新增 baseline：

> Non-Agent Contextual Selector

它不是 LLM，也不是 meta-agent，而是一个固定规则或 contextual bandit，根据 past-only diagnostics 选择 workflow。

示例规则：

```text
if effective_independent_candidate_count low:
    use diversity_constrained_selector
elif validation_dispersion high:
    use CSCV_PBO_selector
elif turnover_distribution high:
    use turnover_penalized_selector
else:
    use fixed_conservative_selector
```

目的：

> 回答 reviewer 的问题：为什么需要 LLM meta-agent？一个简单 contextual selector 不够吗？

TASE 必须相对该 baseline 有增量。否则结论应写成：

> contextual workflow selection helps, but LLM meta-agent is not necessary.

---

## 10. Performance Non-Inferiority Margin

必须预注册具体 margin。

建议同时使用：

### Sharpe Non-Inferiority

```text
paired_CI_lower_bound(TASE_locked_Sharpe - baseline_locked_Sharpe) >= -0.10
```

### Net Return Non-Inferiority

```text
paired_CI_lower_bound(TASE_locked_net_return - baseline_locked_net_return) >= -0.02
```

即：

> TASE 的 locked-test net return 相比 baseline 的下界不能差超过 2%。

禁止：

- 结果出来后改 margin；
- 不同 baseline 使用不同 margin；
- 对 TASE 有利时切换 margin。

---

## 11. Effective Independent Candidate Count

Candidate library 的名义数量 1000–2000 不等于有效独立候选数量。

必须报告：

- pairwise correlation clustering；
- effective independent candidate count；
- average intra-cluster correlation；
- number of candidate clusters；
- family-level concentration；
- selected candidate diversity。

如果 effective independent count 很低：

> false-discovery pressure 低于名义规模，PBO / multiple-testing 解释需要弱化。

---

## 12. Data Universe 修订

Approximate PIT US universe 仍是理想主任务，但实现前必须确认可复现 source。

进入 Codex 前必须做：

- PIT source check；
- membership snapshot；
- download URL / source；
- hash；
- date coverage；
- delisting / removed names handling；
- survivorship bias warning。

如果不能可靠获得 PIT：

- 使用 liquid US universe / current constituents 只能作为 diagnostic；
- 主 claim 必须降级；
- 不得冒充 point-in-time。

ETF tier 保留为 sanity，不作为主 evidence。

---

## 13. RD-Agent(Q)-style Baseline 修订

不能把 RD-Agent(Q)-style baseline 排除在 legal comparison 外。

必须做两类比较：

### 13.1 Throughput Comparison

RD-Agent(Q)-style baseline 可以生成 / 迭代更多 object-level ideas，但必须记录：

- candidate count；
- evaluated candidate count；
- invalid candidate count；
- false discovery metrics；
- locked-test degradation。

### 13.2 Reliability Comparison

即使 RD-Agent(Q)-style baseline performance 更高，也要比较：

- PBO；
- degradation；
- invalid-high-score rate；
- archive completeness；
- budget-normalized reliability。

如果 RD-Agent(Q)-style 在 reliability 和 performance 上都更好：

> TASE 失败，需要重构。

---

## 14. Revised Baseline Set

Stage A1.5 后，核心 baseline 是：

1. Fixed Research Workflow；
2. Validation-Best Selector；
3. Classic CSCV / PBO Selector；
4. Same-Budget Safe Workflow Search；
5. Random Legal Workflow Patch；
6. Non-Agent Contextual Workflow Selector；
7. Object-Level Strategy Search；
8. RD-Agent(Q)-style Research Loop Baseline；
9. SHARP-style Rubric / Policy Evolution；
10. Generic Unconstrained Meta-Harness；
11. TASE Finance-Constrained Workflow Harness；
12. Passive / Equal-Weight benchmark。

其中真正 central comparison：

- TASE vs CSCV/PBO；
- TASE vs Same-Budget Safe Search；
- TASE vs Random Legal；
- TASE vs Non-Agent Contextual；
- TASE vs Validation-Best；
- TASE vs RD-Agent(Q)-style reliability。

---

## 15. Revised Success Criteria

TASE 成功必须满足：

1. H0a 支持：workflow heterogeneity exists；
2. H0b 支持：workflow heterogeneity is predictable from past-only diagnostics；
3. H1 支持：unconstrained meta-harness exploits invalid high-score paths；
4. H2 支持：typed patch language + gates enforce legal workflow reconstruction；
5. H5-CSCV 支持：TASE beats CSCV/PBO on reliability；
6. TASE beats Non-Agent Contextual Selector；
7. TASE beats Same-Budget Safe Workflow Search 或 Random Legal Workflow Patch 至少一个；
8. performance non-inferiority 成立；
9. candidate evaluation budget 公平；
10. per-candidate invariance gate 通过；
11. archive completeness 成立；
12. TASE 不靠 object-level alpha expansion。

失败条件：

- H0b 不成立；
- TASE 打平 CSCV/PBO；
- TASE 打不过 Non-Agent Contextual Selector；
- performance non-inferiority 失败；
- TASE 只赢 raw return，不赢 reliability；
- TASE 靠更多 candidate evaluations；
- TASE 靠新增 operator；
- TASE hidden drops rejected candidates；
- RD-Agent(Q)-style 在 reliability 和 performance 上都更好；
- boundary gate 失败。

---

## 16. Codex 实现硬约束

后续 Codex 实现必须遵守：

1. LLM 不能写 Python execution code；
2. LLM 只能输出 typed JSON patch；
3. patch executor 是 deterministic code；
4. all candidate signals / P&L precomputed and hashed；
5. all workflow decisions logged；
6. all rejected / failed candidates retained；
7. locked test physically inaccessible until final stage；
8. candidate budget enforced by counter；
9. checkpoint / resume required；
10. outputs 必须包含 invariance / archive / budget / H0b / CSCV-marginal / contextual-selector reports。

---

## 17. Stage A1.5 通过条件

Stage A1.5 通过条件：

- Typed Workflow Patch Language 已定义；
- Patch executor semantics 已定义；
- H0a/H0b 已定义；
- CSCV/PBO 主对手地位已定义；
- Non-Agent Contextual baseline 已定义；
- Non-inferiority margin 已预注册；
- Effective independent candidate count 已加入；
- PIT source check 已加入；
- RD-Agent(Q)-style reliability comparison 已加入；
- Revised success/failure criteria 已写明。

如果这些被写入新版 spec，可以进入 Stage A2-short external review。
如果 Stage A2-short 至少 Claude/Gemini 通过，才进入 Codex full implementation。
