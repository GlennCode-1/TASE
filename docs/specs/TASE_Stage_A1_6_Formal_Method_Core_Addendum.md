# TASE Stage A1.6 — Formal Method Core Addendum

> 本文件是可直接并入 T.A.S.E 项目文档 / 论文 Method 章节的正式 specification，不是审查意见。
> 目的：补齐 method core 的 formalism 与 meta-policy，使 TASE Direction A 不再可被归约为 “LLM-wrapped model selection / quant AutoML wrapper”。
> 约束：不扩张 alpha/operator/candidate space；不偷看 locked test；不修改 transaction cost / final metric；不声称发现 alpha 或真实盈利。

---

## 0. 定位

本 addendum 建立在 Stage A1-Revised 与 Stage A1.5 之上，只补六块被外审指出的方法核心缺口：

1. Method contribution 的正确定位（§1）；
2. 形式化对象与 patch language semantics（§2–§3）；
3. Invariant preservation 的构造性保证（§4）；
4. Meta-policy / patch selection 机制（§5）；
5. H0b 的 leakage-safe nested 协议（§6）；
6. Independent workflow-application observation 计数与 power（§7），以及 strong non-agent baseline（§8）与 CSCV 主对手/ablation（§9）。

Stage A1.5 中已确立、本文不再重复但继续生效的部分：typed patch language 的 enum 集合、budget invariance、archive completeness、locked-test isolation、pre-registered non-inferiority margins（Sharpe diff CI 下界 ≥ −0.10；net return diff CI 下界 ≥ −0.02）、RD-Agent(Q)-style reliability comparison、effective independent candidate count、PIT source check。

---

# 1. Method Contribution Reframing

TASE 的 method contribution **不是** “typed patch language 比 fixed config search 表达力更强”。在表达力上，任何 TASE 能表达的 workflow，一个穷举 pre-registered 配置的搜索也能表达；因此表达力不是卖点。

TASE 的贡献是 **invariant-preserving self-modification under gameable financial evaluators**，具体由五条构成：

1. self-modification 被限制在一个 **typed patch space** `P` 内，meta-agent 不能发出任意自然语言指令或任意 Python code；
2. patch execution 是 **deterministic** 的：提议（LLM）与执行（executor）严格分离；
3. candidate-level alpha / P&L invariants 由 **hash** 保护，任何改变候选本身的 patch 在执行前被拒；
4. **archive completeness / budget invariance / locked-test isolation** 被 executor 强制，而非依赖承诺；
5. 因此在一个 **gameable** 的金融 evaluator（回测）下，meta-agent 在结构上**无法**通过 leakage、隐藏 loser、扩预算、改指标等非法路径刷高分——它只能通过合法的 selection/rejection/ensemble 决策改变结果。

这使 TASE 与 self-modifying-agent 一线（Meta-Harness、DGM / Darwin-Gödel Machine、AgentBreeder、ADAS）直接对话：那些工作在 **honest / verifiable evaluator**（coding pass rate、benchmark accuracy）下研究 harness/scaffold 自演化，其安全性来自 evaluator 不可被 game。TASE 处理的是它们未覆盖的场景——**当 evaluator 本身可被 game（noisy、non-stationary、leakage-prone、data-snooping-prone 的金融回测）时，如何让自修改保持 invariant-preserving 且 auditable**。

**Contribution Statement (EN).**
We introduce a typed workflow patch language and a deterministic, invariant-preserving patch executor for finance-constrained strategy-discovery agents. The contribution is not increased expressive power over fixed configuration search; it is *invariant-preserving self-modification under gameable financial evaluators*. A meta-agent may only propose typed patches; a deterministic executor admits a patch only if it provably preserves per-candidate signal and P&L (verified by hashes), search-budget equality, archive completeness, and locked-test isolation. This makes the space of legal self-modifications auditable and cheat-resistant even when the downstream evaluator is a gameable backtest, positioning TASE as the financial, gameable-evaluator counterpart to self-modifying-agent frameworks (Meta-Harness, DGM, AgentBreeder) whose safety currently relies on honest evaluators.

**Contribution Statement (中).**
本文提出一个面向 finance-constrained 策略发现 agent 的 typed workflow patch language 与一个 deterministic、invariant-preserving 的 patch executor。其贡献不在于比 fixed configuration search 拥有更强表达力，而在于 **gameable financial evaluator 下的 invariant-preserving self-modification**：meta-agent 只能提出 typed patch，executor 仅在能证明该 patch 保持 per-candidate signal/P&L（由 hash 校验）、search budget 相等、archive 完整、locked-test 隔离时才接受。这使得合法自修改的空间在下游 evaluator 可被 game 时仍然 auditable 且 cheat-resistant，从而把 TASE 定位为 self-modifying-agent 一线（Meta-Harness、DGM、AgentBreeder，其安全性依赖 honest evaluator）在金融 gameable evaluator 下的对应物。

---

# 2. Formal Objects and Notation

- Candidate set：`C = {c_1, …, c_N}`，N 为固定 candidate library 大小（pre-registered，不可扩）。
- 每个 candidate `c_i` 携带**冻结**的四元组：signal `s_i`、per-period P&L 曲线 `r_i`、turnover 曲线 `u_i`、cost-adjusted P&L `r̃_i`。这些在所有 arm、所有 patch 前后恒定。
- Workflow state：`W ∈ 𝒲`，一个 typed configuration（validation scheme、pruning rule、penalty usage、critic loop、ensemble rule、archive policy、retest/rollback 等字段的取值组合）。
- Archive：`A = (A_acc, A_rej, A_fail, A_inv)`，分别为 accepted / rejected / failed / invalid 候选，append-only。
- Diagnostics：`D_t`，仅用 `≤ t` 数据计算的 past-only 诊断（见 §5.1）。
- Patch：`p ∈ P`，typed patch language（§3）。
- Patch executor：`E : 𝒲 × P → 𝒲 ∪ {⊥}`，`⊥` 表示 reject。
- Workflow transition：`W_{t+1} = E(W_t, p_t)`，当 `E` 返回 `⊥` 时 `W_{t+1} = W_t`（no-op），并记录 rejection。
- Locked test：`T_lock`，write-once、read-final：仅在 final evaluation 阶段可读。
- Validation windows：`V_t`，walk-forward 的验证段。
- Meta-policy：`π_θ(p_t | W_t, D_t, A_t)`，trace-conditioned typed proposer（§5）。

**核心结构定义（Selection-Only Action）.**
一个 workflow `W` 只通过一个 **selection/ensemble map** `Φ_W : C → Δ(C)` 作用于候选集：`Φ_W` 决定哪些候选被 accept/reject、以及 accepted 候选的组合权重。定义组合 P&L
```
R(W) = Σ_i  Φ_W(i) · r_i        （accepted 集合上）
```
关键约束：`W` 对 `{c_i}` 的作用**仅**经由 `Φ_W`，绝不触碰 `(s_i, r_i, u_i, r̃_i)`。此定义是 §4 Proposition 1 与整个 novelty 边界的形式基础——TASE 改变的是 `Φ_W`（如何选），永不改变 `r_i`（选的是什么）。

**Reliability 泛函.**
selection reliability 指标是 `Φ_W` 诱导的 selection 过程的泛函，均在 validation 上估计，不使用 `T_lock`：validation-to-locked degradation proxy、PBO（CSCV）、snooping-adjusted false-discovery proxy、selected-set stability。performance 指标（locked net return、Sharpe、CVaR 等）仅作 non-inferiority 约束。

---

# 3. Typed Workflow Patch Language: Formal Semantics

## 3.1 Patch Schema

```
p = (type, target_stage, operation, parameters, preconditions, safety_tags)
```
其中 `type ∈` 七类枚举；`parameters` 仅允许 pre-registered enum / 离散取值（无任意数值、无 nested free-form dict）；`preconditions` 为对 `W_t` 的可判定谓词；`safety_tags` 用于审计标注，不影响语义。

## 3.2 Patch Types

| Patch Type | Domain（作用面） | Allowed Effect | Forbidden Effect | Main Invariant |
|---|---|---|---|---|
| ValidationSchedulePatch | validation 组织 | 在 pre-registered 集合内切换 scheme / aggregation（如 CSCV_10、median_rank） | 改 locked window、transaction cost、feature availability、final metric、raw return series | candidate invariance + locked-test isolation |
| PruningRulePatch | candidate filtering | 在 pre-registered 集合内设 metric / threshold / min_folds_survived | 任意事后数值阈值、用 locked 指标、集合外阈值搜索 | candidate invariance + budget invariance |
| PenaltyUsagePatch | scoring | 启用/关闭 PBO/turnover/drawdown/CVaR/cost/instability penalty，权重取 pre-registered low/med/high | 连续权重事后微调、从 locked 选权重、削弱 transaction cost | candidate invariance |
| CriticLoopPatch | review | 增删 pre-registered reviewer（leakage/turnover/drawdown/regime/diversity/archive），设 decision_rule | reviewer 读 locked、改 candidate formula、改成本、隐藏 rejected | archive completeness + locked-test isolation |
| EnsembleRulePatch | ensemble | 在 pre-registered 集合内设 rule / k / weight_scheme | 用 locked 权重、按 locked 表现选、改 candidate P&L、加新候选 | candidate invariance |
| ArchivePolicyPatch | memory | 设 retrieval policy、是否使用 rejected archive | 删除 rejected/failed、改 archived metrics、用 locked 检索 | archive completeness |
| RetestRollbackPatch | diagnostics | 设 retest trigger / action、rollback 上一 patch | 在 locked 上 retest、改 final metric、隐藏 retest failure | budget invariance + archive completeness |

## 3.3 Operational Semantics

executor 四步；**LLM/meta-agent 只提议 patch，不执行 patch**：

```
def execute(W, p):
    if not SchemaValidate(p):        return REJECT("schema")
    if not PreconditionCheck(W, p):  return REJECT("precondition")
    W_tentative = tentative_apply(W, p)          # 纯函数，不落盘
    if not InvariantCheck(W, W_tentative):       # 见 §4
        return REJECT("invariant")
    commit(W_tentative)                          # 落盘 + 记录
    return W_tentative
```

- `SchemaValidate`：`type/operation` 合法、`parameters` 全在 allowed enum、无 forbidden field、无 Python code、无无结构自然语言。
- `PreconditionCheck`：如 CSCV 需足够 fold、regime_split 需 regime label、ensemble 需 accepted 数 ≥ k、archive 检索需 archive 非空。
- `InvariantCheck`：§4 的四类不变量，逐个 hash / 计数校验。
- 所有结果写入 `workflow_patch_log.csv`、`rejected_patch_log.csv`、`invariant_gate_report.csv`、`archive_completeness_report.csv`。

---

# 4. Invariant Preservation

## 4.1 Candidate Invariance
对所有 `c_i`，patch 前后：
```
hash(s_i)  ==  hash(s_i');   hash(r_i)  ==  hash(r_i')
hash(u_i)  ==  hash(u_i');   hash(r̃_i) ==  hash(r̃_i')
```
hash 在预注册的固定 rounding（见 §10）下计算。语义：workflow patch 只能改变候选如何被 select/reject/review/archive/ensemble，不能改变候选本身。

## 4.2 Budget Invariance
所有 searchable arm 共享：candidate generation budget、candidate evaluation budget、workflow patch budget，以及 failed/invalid/retested 的计数规则；由单调 counter 强制，patch 不能增预算。

## 4.3 Archive Completeness
`A_acc, A_rej, A_fail, A_inv`、schema-rejected patches、invariant-rejected patches 全部 append-only 保留；hidden/dropped count 必须为 0。

## 4.4 Locked-Test Isolation
```
T_lock 不可被 meta-policy 读取
T_lock 不可被 executor 读取（final evaluation 除外）
T_lock 不进入 H0b 的 target 构造与 selector 训练
T_lock 不参与 workflow selection
```

## 4.5 Proposition 1（构造性保证）

**Proposition 1.** 若 patch `p` 通过 SchemaValidate、PreconditionCheck 与 InvariantCheck，则 `W' = E(W,p)` 满足：(i) 不改变任何 candidate-level signal 或 P&L 曲线；(ii) 不增加 evaluation budget；(iii) 不从 archive 移除任何 rejected/failed 候选；(iv) 在 final evaluation 前不访问 locked-test 结果。

**Proof sketch.**
(i) 由构造，patch language `P` 的每个 operation 的 codomain 都不含 `(s_i,r_i,u_i,r̃_i)`——它们只写 `W` 的 selection/pruning/penalty/critic/ensemble/archive/retest 字段（§3.2）。即便某 operation 的实现有误，InvariantCheck 在 commit 前重算全部 candidate 的四个 hash 并逐一比对，任一不等即返回 `⊥`。故 (i) 成立。
(ii) budget 由单调 counter 维护，`tentative_apply` 不递增 counter，任何试图增预算的 operation 不在 allowed enum 中，SchemaValidate 即拒。故 (ii)。
(iii) archive 为 append-only 结构，无 delete 操作暴露给 `P`；ArchivePolicyPatch 只能改 retrieval，不能改存储；InvariantCheck 校验 `|A_*'| ≥ |A_*|`。故 (iii)。
(iv) `T_lock` 位于 executor 与 meta-policy 均不可达的 access barrier 之后，仅 final-evaluation 例程持有句柄；任何读取 locked 的 operation 不在 enum 中。故 (iv)。∎

Proposition 1 是**构造级**保证（type system + 重算 hash + append-only + access barrier），非经验观察；它是 §1 贡献声明可被形式化背书的原因。此外必须实现**多 patch 复合**下的不变量保持：对每一步 `W_{t+1}=E(W_t,p_t)` 独立执行 InvariantCheck，故不变量在任意 patch 序列下逐步保持（归纳）。

---

# 5. Meta-Policy / Patch Selection Mechanism

TASE 的 meta-policy 不是 “LLM proposes patches” 一句话，而是：

> **Trace-conditioned typed proposer + validation-only reliability scoring + evolutionary archive update.**

即一个在 typed patch space 内、以 validation-only reliability 为 fitness、由 LLM 依据 workflow trace 与 past-only diagnostics 条件化提议、并维护 lineage archive 的进化式搜索。

## 5.1 Inputs to Meta-Policy
允许输入（全部 past-only）：`W_t`；`D_t` = { validation distribution dispersion、candidate correlation/clustering、effective independent candidate count、turnover distribution、PBO distribution、regime volatility、drawdown clustering、candidate family composition、validation stability score、archive failure pattern }；archive `A_t`；previous patch outcomes（validation 侧）。
禁止输入：locked-test 任何量、future returns、hidden labels、post-hoc metric weights。

## 5.2 Patch Proposal
LLM proposer 生成 `K` 个 typed patch：`p_t^1,…,p_t^K ~ π_θ(· | W_t, D_t, A_t)`。每个必须先过 SchemaValidate；非法直接丢弃并记录（不占 evaluation budget 之外的额度）。

## 5.3 Patch Scoring（validation-only）
对每个通过 schema 与 invariant 的 patch，用 validation-only reliability objective 评分：
```
R_val(p) = − α1·degradation_proxy(p)
           − α2·PBO_proxy(p)
           − α3·false_discovery_proxy(p)
           − α4·invalid_risk_penalty(p)
           + α5·stability_bonus(p)
```
- `degradation_proxy`：`W'=E(W,p)` 诱导的 selection，在 validation sub-splits 上 in-sample→held-out 的 rank/score 退化（越小越好）。
- `PBO_proxy`：该 selection 过程在 validation folds 上的 CSCV 过拟合概率。
- `false_discovery_proxy`：被选中候选中，validation edge 未通过 snooping-adjusted（SPA/Reality-Check）门槛的比例。
- `invalid_risk_penalty`：预测该 workflow 在部署中逼近 boundary/gate 违规的风险（如贴阈值决策计数）。
- `stability_bonus`：selected set 在 validation sub-windows / seeds 间的稳定性（rank 相关）。
- `α1…α5` **pre-registered**，不得在看到 validation 分布后调整；locked 不进入任一项。

## 5.4 Patch Selection
`p_t^* = argmax_p R_val(p)`，或采用 evolutionary top-k：保留 top-k patch，其 `W'` 作为下一轮父代，形成 lineage。budget 由 §4.2 counter 统一约束。

## 5.5 Archive Update
记录 proposed / accepted / rejected patches、rejection reasons、invariant failures、downstream validation diagnostics、lineage 父子关系，落盘 `workflow_patch_log.csv` 与 `rejected_patch_log.csv`。

## 5.6 Why This Is Not Random Config Search
- patch proposals **conditioned on** workflow trace 与 past-only diagnostics（Random Legal 无条件）；
- patch search 是 typed + invariant-preserving（不是任意 config）；
- patch scoring 优化 reliability objective（Validation-Best 优化 raw validation 分，二者目标不同）；
- Same-Budget Safe Search 无 adaptive、trace-conditioned 的 patch 生成；
- Non-Agent Contextual 无 language-based reasoning / archive 解释；
- 因此 TASE 的假设是：**在相同预算与相同候选空间下，trace-conditioned typed proposal 比无条件/非自适应搜索更快找到低 false-discovery 的 workflow**。此假设由 §5.7 与 §9 的对照检验，不预设成立。

## 5.7 Failure Criterion
若 TASE 打不过 §8.2 的 **learned** non-agent contextual selector（在同一 past-only diagnostics、同一 reliability 指标、同一预算下），则判定：
> contextual workflow selection helps, but the LLM meta-agent contribution is not supported.
此时论文如实降级为 protocol / diagnostic，不声称 agent 必要性。

---

# 6. H0b Nested Walk-Forward Protocol（leakage-safe）

**H0a**：workflow heterogeneity exists——不同 fold/regime/candidate-pool 下 best fixed workflow 不同（指标：workflow ranking variance、Kendall/Spearman 不稳定性、best workflow 跨 fold turnover、oracle vs deployable fixed workflow gap）。

**H0b**：workflow heterogeneity is predictable from past-only diagnostics。

Leakage-safe 约束：
- H0b 的 target（“best workflow at τ”）**只能**由 `τ` **之前**的 validation 窗口定义；
- 不得使用 locked test；不得使用未来 fold；
- 每个 decision point 只用当时可见的 `D_τ`；
- 采用 nested / expanding walk-forward。

```
for decision time τ in expanding_walkforward(T_train ... T_end):
    D_τ         = diagnostics(data <= τ)                     # past-only
    label(τ)    = argmax_W reliability_on(V_{prior_window(τ)}, W)   # 仅用 τ 之前 validation
    train_pairs = {(D_{τ'}, label(τ'+1)) : τ' < τ}          # 只用过去 pair
    selector.fit(train_pairs)
    pred(τ+1)   = selector.predict(D_τ)
    evaluate pred(τ+1) on next validation/application window (not locked)
# locked test 只在所有决策完成后的 final evaluation 使用
```

H0b 支持条件：past-only diagnostics 预测 next-window best workflow 显著优于 random mapping，**且** TASE 优于 learned non-agent contextual selector（§8.2）。H0b 不支持 → self-evolution 主张降级为 diagnostic / workflow-selection study。

---

# 7. Independent Workflow-Application Observations and Power

**定义.**
- *fold-level observation*：一个 walk-forward fold 的最终结果。
- *seed-level stochastic replicate*：同一 fold 下不同随机种子的重复；**衡量方差，不增加独立信息**。
- *workflow-application observation*：一次“在某个 decision window 上应用某 workflow 并在其 held-out 上评估”的事件。
- *true independent decision point*：nested/expanding walk-forward 下互不重叠（或弱重叠）的 sub-window 决策。

**规则.**
1. 报告 **independent workflow-application observations** 数，而非 `seeds × folds` 的名义乘积；
2. 不得用 `seeds × folds` 充当独立样本量；
3. 用 expanding/nested sub-windows 增加真实 decision points（例如把每个 fold 内的 rebalance/子窗口作为独立 application 观测）；
4. **pre-register minimum detectable effect (MDE)**；
5. 若 power 不足，`H5-CSCV` 与 H0b 的正向结论必须标注为 **exploratory**，不得作为 gating 支持。

**Power-check 模板（pre-register）.**
```
n_indep      = number of independent workflow-application observations
MDE          = smallest paired reliability difference of interest (e.g., ΔPBO = 0.05)
method       = paired block bootstrap over matched decision-point outputs
power_target = 0.80
decision rule:
  if 95% paired CI excludes 0 and |effect| >= MDE  -> supported
  if CI width > MDE and CI includes 0              -> underpowered -> exploratory
  if |effect| < MDE                                -> no material effect
```

---

# 8. Strong Non-Agent Contextual Baseline

## 8.1 Rule-Based Contextual Selector（下界）
固定 if-else 规则，依据 past-only diagnostics 选 workflow（如：effective independent candidate count 低 → diversity_constrained_selector；validation dispersion 高 → CSCV_PBO_selector；turnover 高 → turnover_penalized_selector；否则 fixed_conservative_selector）。

## 8.2 Learned Non-Agent Contextual Selector（上界，必须做）
从以下择一或并列：shallow decision tree、gradient boosting（浅层）、contextual bandit、multinomial logistic / ranking model。
- 输入：与 TASE **完全相同**的 past-only diagnostics（结构化特征）；
- 输出：workflow choice；
- 禁止：locked-test、future returns、LLM reasoning、超出结构化特征的 archive free-text 解释。

**判定.** TASE 必须相对 learned non-agent baseline 有增量。否则写：
> contextual workflow selection helps, but the LLM meta-agent contribution is not supported.

learned baseline 与 TASE 使用同一 §6 nested 协议、同一 §7 观测计数、同一 §9 reliability 指标与预算。

---

# 9. CSCV / PBO Main Opponent and Ablation

## 9.1 H5-CSCV
主对手是 Classic CSCV / PBO Selector（不是稻草人：它正是被设计来优化 PBO/false-discovery 的 SOTA）。
成功条件（全部满足）：
- TASE − CSCV 在 **至少两个** primary reliability metrics 上 paired CI 改善；
- performance non-inferiority 成立（§ pre-registered margins）；
- candidate budget 相同；
- 不靠新增 operator；
- 不靠 hidden archive changes。

打平即失败：
> 若 TASE 与 CSCV/PBO 在 reliability 上无显著差异，则不算支持 TASE，只说明 TASE 复现了经典方法。

## 9.2 PBO-Patch Ablation
关闭 TASE 的 PBO PenaltyUsagePatch 后重跑：
- 若 reliability 未明显下降 → 增量来自 **非-CSCV** 的 workflow decisions（支持 novelty）；
- 若显著下降 → TASE 主要依赖 CSCV/PBO，novelty 弱化，需如实报告。

**Pre-registered “material degradation” 规则：**
```
PBO-patch ablation is material if, relative to full TASE:
  (a) at least two reliability metrics degrade beyond their paired-CI threshold, OR
  (b) validation-to-locked degradation increases by more than a pre-registered margin (e.g., +0.05 in the degradation proxy).
```

---

# 10. Codex-Ready Addendum Requirements

进入 Codex full implementation 前，implementation prompt 必须写入以下硬约束：

1. **Typed schemas via Pydantic**：每个 patch type 一个 Pydantic model，字段级校验；
2. **strict enum values**：所有 parameters 为 `Enum`，拒绝集合外取值；
3. **no arbitrary nested dict**：parameters 扁平、类型受限，禁止任意嵌套/自由文本字段；
4. **no Python code generated by LLM**：LLM 仅输出 typed JSON/YAML patch；executor 为确定性代码；
5. **candidate matrices precomputed**：`s_i, r_i, u_i, r̃_i` 预计算并冻结，供所有 arm 共享；
6. **hash precision / rounding**：固定 rounding（如 float64 → round 至 pre-registered 小数位）后计算 `sha256`，写入 `per_candidate_invariance_gate_report.csv`；
7. **checkpoint / resume required**：seed×fold×patch-round 断点续跑；
8. **locked-test physical separation**：locked 数据在独立存储/进程后，仅 final-evaluation 例程可读；meta-policy 与 executor 无句柄；
9. **B0–B7 staged implementation**（见下）；
10. **required outputs**：invariance / archive / budget report、`h0b_predictability.csv`、`tase_vs_cscv_marginal.csv`、`contextual_selector_comparison.csv`（含 learned baseline）、`independent_observation_count.csv`、`power_check.csv`、`pbo_patch_ablation.csv`、`workflow_patch_log.csv`、`rejected_patch_log.csv`。

**B0–B7 staged implementation.**
- **B0** 数据与候选：PIT source check（membership snapshot / URL / hash / coverage / delisting handling / survivorship warning）；candidate library 预计算 + hash；effective independent candidate count。
- **B1** workflow state schema + Fixed Research Workflow baseline。
- **B2** typed patch language（Pydantic）+ executor 四步 + §4 invariants + negative controls（故意坏 patch 必须 100% 被拒）。**未通过 negative control 不得进 B3。**
- **B3** baselines：Validation-Best、Classic CSCV/PBO、Same-Budget Safe、Random Legal、Non-Agent（rule + learned）、Object-Level Strategy、RD-Agent(Q)-style、SHARP-style、Generic Unconstrained Meta-Harness、Passive。
- **B4** meta-policy：trace-conditioned proposer + validation-only reliability scoring + evolutionary archive（§5）。
- **B5** H0a/H0b nested 协议 + independent-observation 计数 + power check（§6–§7）。
- **B6** full run（10 seeds、≥7 folds、nested sub-windows）+ H5-CSCV marginal + PBO-patch ablation。
- **B7** robustness（ETF sanity、cost 5/10/20bps、library size、regime split、locked-shift、current-constituents appendix）+ reporting + 诚实 H 判定。

---

## Stage A1.6 Pass Criteria

进入 Codex full implementation 前，必须全部满足：

1. §1 method contribution 定位为 invariant-preserving self-modification under gameable evaluators（含 EN/中 statement），并声明不主张扩表达力；
2. §2–§3 形式化对象与 patch semantics 已写入；Selection-Only Action 定义明确；
3. §4 四类 invariants + Proposition 1（含 proof sketch + 多 patch 复合）已写入；
4. §5 meta-policy（trace-conditioned proposer + validation-only reliability scoring + evolutionary archive）已定义，含“为何非 random config search”与 failure criterion；
5. §6 H0b nested、leakage-safe 协议已定义（locked 不进 target/训练）；
6. §7 independent workflow-application observation 计数 + pre-registered MDE + power 模板已写入，underpowered → exploratory；
7. §8 learned non-agent contextual baseline 已定义，TASE 须胜之否则降级；
8. §9 H5-CSCV 主对手 + “打平即失败” + PBO-patch ablation 的 material-degradation 规则已 pre-register；
9. §10 Codex 硬约束（Pydantic / enum / no-LLM-code / hash / locked separation / B0–B7 / outputs）已写入；
10. pre-registered non-inferiority margins（Sharpe ≥ −0.10、net return ≥ −0.02）与 PIT source check 保持生效。

## Final Recommendation

**Ready for Codex after incorporating A1.6.**

理由：A1.6 补齐了 A2-short 指出的四个 minor 缺口——method contribution 的正确定位（对话 self-modifying-agent 一线而非 alpha mining）、meta-policy 的 formalism（trace-conditioned typed proposer + reliability fitness + evolutionary archive，回答“为何不是 random config search / 为何要 agent”）、H0b 的 leakage-safe nested 协议、independent-observation 计数与 power。加上 A1.5 已立住的 typed patch language + deterministic executor + hash invariance（Proposition 1 提供构造级保证），method core 已不再可被归约为 “LLM-wrapped model selection”。

需要明确的边界：A1.6 让方法**可实现且可辩护**，但不保证结果为正。三个 gating 经验前提仍可能失败，且必须诚实执行其降级：H0b 不成立（heterogeneity 不可预测）、TASE 打平 CSCV、或 TASE 不胜 learned non-agent baseline——任一发生，self-evolution 主张降级为 protocol / diagnostic，performance 永不作为胜负标准。据此，无需再走一整轮外审；按 §Stage A1.6 Pass Criteria 逐条并入 spec 后，即可进入 Codex 的 B0–B7 分阶段实现。
