# Stage A0 — Novelty Boundary
# Why TASE Is Not Another Alpha Miner

## 0. Stage A0 的目的

Stage A0 的目的不是设计实验，也不是写代码，而是先把 TASE 的 novelty boundary 写清楚。

现在方向 A 已经回到原始主线：

> TASE 研究的不是某一个策略是否更赚钱，而是：在 frozen LLM 之上，能否让 meta-agent 对 LLM-driven financial trading agent 的 typed, multi-component **strategy-discovery workflow harness** 进行 finance-constrained reconstruction，并证明这种 meta-level reconstruction 的增量不能由 fixed workflow、SHARP-style rubric evolution、object-level strategy evolution 或 generic unconstrained harness evolution 单独解释。

但方向 A 最大风险也非常明确：

> 如果 TASE 的胜负只由 selected strategy ensemble 的 raw locked-test return / Sharpe 决定，那么 reviewer 很容易认为它只是另一个 alpha mining / quant AutoML / strategy evolution system。

因此，Stage A0 必须回答：

> TASE 和 alpha miner 的本质区别是什么？这个区别如何落到实验设计和评价指标上？

---

## 1. 一句话 novelty boundary

**TASE is not an alpha miner because it does not expand the alpha/operator space or optimize raw strategy performance directly; instead, under a fixed candidate library, fixed search budget, fixed data protocol, and locked test, it reconstructs the strategy-discovery workflow to reduce false-discovery risk, validation-to-locked degradation, PBO, and invalid high-score exploitation while preserving locked-test performance.**

中文表述：

> TASE 不是另一个 alpha mining 系统，因为它不扩张 alpha / factor / operator 空间，也不直接以 raw strategy performance 为唯一目标；它在固定候选策略库、固定搜索预算、固定数据协议和锁定测试集下，重构策略发现与筛选 workflow，目标是减少 false discovery、validation-to-locked degradation、PBO 和 invalid high-score exploitation，并在此基础上保持或改善 locked-test performance。

---

## 2. TASE 不是在做什么

TASE 不能被写成以下任何一种东西：

### 2.1 不是发现新 alpha 的系统

TASE 不主张：

- 发现了新的因子；
- 找到了新的 trading signal；
- 生成了更优策略公式；
- 通过扩大策略空间提升收益；
- 凭借更大搜索预算找到更好策略。

所有实验 arm 必须共享同一个：

- candidate strategy / factor library；
- operator library；
- parameter grid；
- raw data；
- feature availability / timestamp rule；
- transaction cost assumption；
- train / validation / locked-test protocol；
- maximum candidate budget。

如果 TASE 使用了额外 operator、额外数据源、额外 candidate budget，或者偷偷扩大了 parameter grid，它就退化成 alpha miner。

### 2.2 不是 object-level strategy evolution

TASE 不直接演化：

- alpha formula；
- factor expression；
- model architecture；
- signal-to-position rule；
- portfolio rule；
- strategy code；
- market timing rule；
- risk-on / risk-off rule。

这些属于 object-level strategy evolution，应放入 baseline，而不是 TASE 的合法 patch space。

### 2.3 不是只追求 raw return / Sharpe 的 AutoML

TASE 不能只用以下指标作为核心胜负标准：

- raw cumulative return；
- raw annualized return；
- raw Sharpe；
- validation-best performance；
- selected strategy 的单次 locked-test 收益。

这些指标可以报告，但不能定义 TASE 的主要贡献。

---

## 3. TASE 真正在做什么

TASE 做的是 **strategy-discovery workflow harness reconstruction**。

也就是说，它重构的是：

> 如何生成、筛选、复核、拒绝、组合、归档候选策略的研究流程。

TASE 的合法 patch space 包括：

- candidate generation schedule；
- operator selection order；
- validation split schedule；
- walk-forward / CSCV aggregation rule；
- candidate pruning threshold；
- PBO / data-snooping penalty usage；
- turnover / drawdown / cost penalty usage；
- critic / reviewer loop；
- leakage checker；
- risk reviewer；
- ensemble construction rule；
- diversity constraint；
- archive retrieval / memory policy；
- accepted / rejected candidate logging；
- retest policy under diagnostics；
- rollback rule；
- evidence threshold for acceptance；
- invalid-high-score handling。

TASE 的目标不是“生成更强 alpha”，而是：

> 在同样候选池中，组织一个更不容易被 noisy、non-stationary、data-snooping-prone、leakage-prone financial evaluator 欺骗的 discovery workflow。

---

## 4. 实验中必须冻结的东西

为了证明 TASE 不是 alpha miner，实验中以下对象必须冻结：

| 对象 | 冻结原因 |
|---|---|
| Raw data | 防止通过换数据获利 |
| Universe | 防止通过换股票池获利 |
| Operator library | 防止扩大 alpha 空间 |
| Parameter grid | 防止隐性 strategy tuning |
| Candidate budget | 防止用更多搜索次数获利 |
| Transaction cost | 防止通过降低成本假设获利 |
| Feature availability rule | 防止 look-ahead leakage |
| Train / validation / locked-test split | 防止 test leakage |
| Final evaluation metric | 防止 post-hoc metric selection |
| Leakage gates | 防止弱化安全边界 |
| Hard constraints | 防止绕过风险或评估协议 |

如果 TASE 修改了这些对象，应判为 invalid candidate 或 unconstrained / strategy baseline，而不是合法 TASE。

---

## 5. 实验中 TASE 可以修改的东西

TASE 只能修改 workflow 层面的选择纪律：

| 可修改对象 | 为什么属于 workflow harness |
|---|---|
| Validation schedule | 决定如何评估候选稳定性，不改变候选本身 |
| Pruning rule | 决定哪些候选进入下一轮，不改变候选收益曲线 |
| PBO penalty | 决定如何惩罚过拟合风险 |
| Turnover / cost penalty | 决定如何惩罚不可交易性 |
| Drawdown penalty | 决定如何惩罚尾部风险 |
| Critic loop | 决定是否加入复核者 |
| Leakage checker order | 决定检查流程 |
| Ensemble construction rule | 决定如何组合已存在候选 |
| Diversity constraint | 防止选择高度重复的候选 |
| Archive / memory policy | 决定如何使用 accepted / rejected trace |
| Retest rule | 决定诊断异常时是否复测 |
| Rollback rule | 决定失败 workflow 如何回退 |
| Evidence threshold | 决定接受候选需要多少证据 |

关键边界：

> TASE 可以改变“候选策略如何被筛选和组合”，但不能改变“单个候选策略本身是什么”。

---

## 6. Workflow 版 boundary gate

方向 A 必须有一个类似 π-invariance 的 workflow boundary gate。

### 6.1 Gate 定义

对于固定 candidate library 中的每个 candidate：

> TASE patch 前后，该 candidate 的 raw signal、per-period return series、turnover series、cost-adjusted P&L curve 必须完全一致或在数值容差内一致。

如果某个 workflow patch 改变了单个 candidate 的原始信号或回测曲线，说明它不是 workflow patch，而是在偷改 alpha / strategy / evaluation protocol。

### 6.2 允许变化的对象

TASE patch 只能改变：

- candidate 是否被接受；
- candidate 是否被拒绝；
- candidate 是否进入 ensemble；
- ensemble 中各 candidate 的权重；
- accepted / rejected candidate 的记录；
- workflow diagnostics；
- retest / rollback / archive decision。

### 6.3 必须拒绝的负控制

以下故意坏 patch 必须被 100% 拒绝：

- 增加新 operator；
- 扩大 parameter grid；
- 偷看 locked test；
- 改 transaction cost；
- 改 final metric；
- 改 universe；
- 改 feature availability rule；
- 弱化 leakage gate；
- 隐藏 rejected candidates；
- 静默丢弃 failed candidates；
- 增加 candidate budget；
- 使用 future returns。

---

## 7. TASE 的 dependent variable 应该是什么

TASE 的主 dependent variable 不能是 raw return，而应是 **selection reliability**。

核心指标应包括：

### 7.1 Overfitting-control metrics

- validation-to-locked degradation；
- PBO；
- Deflated Sharpe；
- White Reality Check / SPA-like adjusted p-value；
- multiple-testing adjusted significance；
- selected candidate stability across folds/seeds。

### 7.2 False-discovery-control metrics

- false-discovery proxy；
- invalid-high-score rejection rate；
- no-valid-candidate rate；
- selected false-positive candidate ratio；
- accepted / rejected audit completeness。

### 7.3 Performance preservation metrics

- locked-test net return；
- locked-test Sharpe；
- turnover-adjusted return；
- max drawdown；
- CVaR；
- turnover；
- transaction cost.

Performance 不是唯一目标，而是约束：

> TASE should reduce false-discovery risk and degradation while preserving, or ideally improving, locked-test net performance.

如果 TASE 只降低 PBO 但收益显著恶化，应写成 trade-off，而不是无条件支持。

---

## 8. 和主要 prior work 的边界

### 8.1 QuantEvolve / AlphaAgentEvo / FactorMiner / FactorEngine

这些工作主要扩展或搜索 alpha / factor / strategy object space。

TASE 与它们的区别：

- 它们优化 candidate strategy；
- TASE 固定 candidate library 和 operator library；
- 它们主要追求 performance；
- TASE 主要追求 selection reliability under gameable financial evaluators；
- 它们可以作为 object-level strategy evolution baseline；
- TASE 必须证明增量不是来自更大 candidate space。

一句话区分：

> QuantEvolve-style methods ask “which strategy should we evolve?”; TASE asks “which discovery workflow avoids selecting false strategies under the same candidate set and budget?”

### 8.2 RD-Agent(Q)

RD-Agent(Q) 自动化 factor / model R&D loop，重点是提高研究产出和性能。

TASE 与它的区别：

- RD-Agent(Q) 侧重自动化 R&D 产出；
- TASE 侧重 finance-constrained workflow reconstruction under false-discovery risk；
- TASE 固定 operator library、candidate budget 和 locked-test protocol；
- TASE 的核心指标是 PBO / degradation / false-discovery proxy，而非单纯 annualized return。

一句话区分：

> RD-Agent(Q) automates quant research; TASE controls and reconstructs the discovery workflow to reduce false discoveries under the same search space.

### 8.3 SHARP

SHARP-style prior 更接近 finance-specific policy / rubric evolution。

TASE 与它的区别：

- SHARP-style baseline 演化 condition-action policy / rubric；
- TASE 演化 research workflow harness；
- SHARP 的核心是策略/政策规则如何演化；
- TASE 的核心是候选生成、验证、拒绝、归档和组合流程如何演化；
- SHARP-style rubric evolution 应作为 baseline，而不是被忽略。

一句话区分：

> SHARP evolves trading policy/rubric; TASE reconstructs the research workflow that decides which candidate strategies survive evaluation.

### 8.4 Meta-Harness / DGM / AgentBreeder

这些工作说明 harness / scaffold 可以被优化，但多在 coding / reasoning 等更确定的 evaluator 上验证。

TASE 与它们的区别：

- 通用方法多假设 benchmark evaluator 较可信；
- 金融 evaluator noisy、non-stationary、gameable；
- TASE 贡献在于把 harness reconstruction 放入 finance-specific false-discovery control、locked-test discipline 和 leakage boundary 中；
- generic unconstrained meta-harness 应作为 baseline。

一句话区分：

> Generic meta-harness methods optimize scaffold under relatively honest evaluators; TASE studies constrained workflow reconstruction under gameable financial evaluators.

---

## 9. Central Ablation

Stage A0 建议将 central ablation 固定为：

| Arm | 作用 |
|---|---|
| Fixed Research Workflow | 固定 workflow，不进化 |
| Validation-Best Selector | 贪婪 alpha mining / AutoML 抽象 |
| Same-Budget Safe Workflow Search | 排除“只是多试 workflow 配置” |
| Random Legal Workflow Patch | 排除“合法随机改也一样” |
| Object-Level Strategy Search | 排除“其实是策略搜索贡献” |
| SHARP-style Rubric / Policy Evolution | 排除“只是 policy / rubric evolution” |
| Generic Unconstrained Meta-Harness | 检验无约束 harness 是否走向 invalid high-score |
| TASE Finance-Constrained Workflow Harness | 本文方法 |
| Passive / Equal-Weight | 金融基准下限 |

TASE 的 claim 只有在以下条件下才成立：

1. 不靠更多 candidate evaluations；
2. 不靠新增 operator；
3. 不靠偷看 locked test；
4. 不靠改 transaction cost；
5. 不靠隐藏 rejected candidates；
6. 不靠 object-level strategy tuning；
7. 相比 same-budget safe workflow search 和 random legal workflow patch，有更低 degradation / PBO / false-discovery proxy；
8. 相比 validation-best selector，有更强 out-of-sample reliability；
9. locked-test net performance 不显著更差，最好更好。

---

## 10. Reviewer 可能攻击与回答

### Attack 1：这只是 alpha mining / AutoML for quant

回答：

> We explicitly fix the candidate library, operator set, parameter grid, data, search budget, transaction cost, and locked test across all arms. TASE does not expand the strategy space. The only object under reconstruction is the workflow that validates, rejects, archives, and ensembles candidates. Our primary outcome is selection reliability, not raw strategy performance.

### Attack 2：你最终还是用 selected strategy 的收益评价

回答：

> We report locked-test net performance, but it is not the sole objective. The core metrics are validation-to-locked degradation, PBO, snooping-adjusted significance, false-discovery proxy, invalid-high-score rejection, and selected-candidate stability. Performance is treated as a preservation constraint.

### Attack 3：TASE 可能只是比 baseline 多试了更多候选

回答：

> All searchable arms are constrained to the same candidate budget and the same number of candidate evaluations. We report true evaluated candidate counts for each arm.

### Attack 4：TASE 可能偷改了 alpha

回答：

> We use a per-candidate invariance gate: every candidate’s raw signal and P&L curve must remain unchanged under a workflow patch. Workflow patches may only change selection, rejection, archive, and ensemble decisions.

### Attack 5：为什么不是 SHARP？

回答：

> SHARP-style evolution modifies trading policy/rubric. TASE reconstructs the research workflow for candidate validation, rejection, archive, and ensemble construction. We include a SHARP-style baseline to isolate this difference.

### Attack 6：为什么不是 Meta-Harness？

回答：

> Generic meta-harness methods optimize scaffold under relatively stable evaluators. TASE focuses on gameable financial evaluators and adds finance-specific constraints, locked-test isolation, false-discovery metrics, and invalid-high-score diagnostics.

---

## 11. Stage A0 最终 problem statement

建议论文问题定义写成：

> We study whether a frozen-LLM financial trading agent can improve not by expanding the strategy space, but by reconstructing its strategy-discovery workflow. Given a fixed operator library, fixed candidate budget, fixed data protocol, and locked test, TASE allows a meta-agent to patch the typed workflow harness governing candidate generation, validation, pruning, rejection, archive retrieval, and ensemble construction. The central question is whether such finance-constrained workflow reconstruction yields selection-reliability gains that cannot be explained by fixed workflows, SHARP-style policy evolution, object-level strategy search, or unconstrained generic harness evolution.

中文版本：

> 本文研究的问题不是让 frozen LLM 找到更多策略，而是让 meta-agent 在固定候选策略空间、固定搜索预算、固定数据协议和锁定测试集下，重构 LLM-driven financial trading agent 的策略发现 workflow harness。TASE 允许元层修改候选生成、验证、剪枝、拒绝、归档和组合流程，但不允许扩展 alpha 空间、偷看测试集或改变评估规则。核心问题是：这种 finance-constrained workflow reconstruction 是否能带来 selection reliability 上的增量，并且这种增量不能由 fixed workflow、SHARP-style policy evolution、object-level strategy search 或 unconstrained generic harness evolution 单独解释。

---

## 12. 不应该再说的话

不要再说：

- TASE discovers better alpha；
- TASE guarantees higher trading return；
- TASE beats all strategy mining methods；
- TASE improves raw Sharpe by self-evolution；
- TASE is a stronger QuantEvolve；
- TASE uses LLM to find hidden market laws；
- TASE proves profitable trading.

可以说：

- TASE improves or preserves locked-test performance under stronger false-discovery control；
- TASE reduces validation-to-locked degradation；
- TASE lowers PBO under fixed candidate budget；
- TASE rejects invalid high-score paths；
- TASE reconstructs workflow rather than strategy object；
- TASE studies self-evolving financial agents under gameable evaluators.

---

## 13. Stage A0 是否通过

Stage A0 通过条件：

1. Novelty boundary 已明确：TASE 是 workflow reconstruction，不是 alpha mining；
2. Dependent variable 已明确：selection reliability 优先，performance preservation 约束；
3. Frozen objects 已明确：data / library / budget / locked test / metric / cost；
4. Allowed patch space 已明确：validation / pruning / archive / ensemble / critic / rejection；
5. Forbidden patch space 已明确：operator expansion / future data / test feedback / cost weakening；
6. Boundary gate 已明确：per-candidate signal and P&L invariance；
7. Central baselines 已明确；
8. Reviewer attack response 已明确；
9. 进入 Stage A1 前必须做 collision check，尤其针对 QuantEvolve、RD-Agent(Q)、FactorMiner、SHARP。

结论：

> Stage A0 可以通过，但必须把 “Why TASE is not another alpha miner” 写进论文方法和实验设计，而不是只作为内部解释。
