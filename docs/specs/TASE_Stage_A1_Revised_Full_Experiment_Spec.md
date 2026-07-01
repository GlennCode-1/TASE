# TASE Stage A1-Revised — Full Experiment Specification
## Direction A: Finance-Constrained Strategy-Discovery Workflow Reconstruction

## 0. 本文件目的

本文件是 Stage A1 的修订版，吸收了 Claude collision boundary check 和补读 FactorEngine / CogAlpha / AlphaAgentEvo 后的结论。

最重要的修订是：

> TASE 不再把 raw locked-test performance improvement 作为主胜负标准，而是把 locked-test performance 作为 **non-inferiority constraint**。
> TASE 的主因变量是 **selection reliability**：validation-to-locked degradation、PBO、snooping-adjusted false discovery、invalid-high-score rejection、selected-candidate stability。

TASE 的核心 claim 不是“发现更强 alpha”，而是：

> 在固定 alpha/operator/candidate space 和同等 search budget 下，TASE 通过重构 strategy-discovery workflow，使 agent 更不容易选中 false alpha，并且最终 locked-test performance 不显著变差，最好改善。


## 1. 修订后的核心问题定义

### 1.1 English problem statement

We study whether a frozen-LLM financial trading agent can improve not by expanding the alpha space, but by reconstructing its strategy-discovery workflow. Given a fixed operator library, fixed candidate budget, fixed data protocol, and isolated locked test, TASE allows a meta-agent to patch the typed workflow harness governing candidate generation, validation, pruning, rejection, archive retrieval, and ensemble construction. The central question is whether such finance-constrained workflow reconstruction improves selection reliability under gameable financial evaluators — measured by validation-to-locked degradation, PBO, snooping-adjusted false discovery, and invalid-high-score rejection — while satisfying locked-test performance non-inferiority.

### 1.2 中文 problem statement

本文研究的问题不是让 frozen LLM 发现更多 alpha，而是在固定 operator library、固定 candidate budget、固定 data protocol 和隔离 locked test 的前提下，让 meta-agent 重构 LLM-driven financial trading agent 的 strategy-discovery workflow harness。TASE 允许元层修改候选生成、验证、剪枝、拒绝、归档和组合流程，但不允许扩展 alpha 空间、偷看测试集或改变评估规则。核心问题是：这种 finance-constrained workflow reconstruction 是否能在 gameable financial evaluator 下提高 selection reliability，并在 locked-test performance 不显著变差的前提下，降低 false discovery、PBO、validation-to-locked degradation 和 invalid-high-score exploitation。


## 2. 为什么这不是另一个 alpha miner

### 2.1 TASE 明确不做

TASE 不生成新的 factor program，不扩张 operator library，不扩张 parameter grid，不修改 alpha formula，不修改 raw signal，不修改 strategy code，不修改 transaction cost，不修改 locked test，不修改 final metric，不增加 candidate budget，不隐藏 failed / rejected candidates，也不通过 raw return / Sharpe 作为唯一胜负标准。

因此，TASE 不能写成：

> A stronger alpha mining agent.

也不能写成：

> A better QuantEvolve / FactorEngine / CogAlpha / AlphaAgentEvo.

### 2.2 TASE 真正在做

TASE 做的是：

> 在固定候选策略空间下，重构“如何筛选、拒绝、复核、归档和组合候选”的 workflow。

它不改变候选本身，而是改变候选如何被研究流程处理；它评估 workflow 的 selection reliability；它研究 workflow 是否能降低 false discovery；它把 performance 当作 non-inferiority constraint，而不是主胜负标准。


## 3. 与补读 prior work 的边界

### 3.1 FactorEngine

FactorEngine 是 program-level factor discovery / factor evolution。它将 factors 表示为 Turing-complete code，通过 knowledge-infused bootstrapping、macro-micro co-evolution、LLM-guided macro mutation 和 Bayesian micro-search 来生成更强 factor，并用 IC / ICIR / RankIC / portfolio metrics 展示性能。

| 维度 | FactorEngine | TASE |
|---|---|---|
| 研究对象 | Factor program evolution | Strategy-discovery workflow reconstruction |
| 是否生成新 factor | 是 | 否 |
| 是否扩张 alpha space | 是 | 否 |
| 主指标 | IC / ICIR / AR / Sharpe | PBO / degradation / false-discovery proxy |
| 性能角色 | 主胜负标准 | Non-inferiority constraint |

### 3.2 CogAlpha

CogAlpha 是 code-based alpha discovery。它通过 Seven-Level Agent Hierarchy、Multi-Agent Quality Checker、Thinking Evolution 来 refine / mutate / recombine alpha candidates，并强调扩大 effective search space 与生成 robust interpretable alpha。

| 维度 | CogAlpha | TASE |
|---|---|---|
| 研究对象 | Alpha generation / evolution | Workflow selection reliability |
| 是否扩大 search space | 是 | 否 |
| 是否修改 alpha code | 是 | 否 |
| 输出 | 新 alpha / evolved alpha | Selected / rejected archive + ensemble |
| 主张 | 更强 alpha discovery | 更可靠 workflow selection |

### 3.3 AlphaAgentEvo

AlphaAgentEvo 是 self-evolving agentic reinforcement learning for alpha mining。它把 alpha mining 从 search-backtest-restart 改写成 multi-turn alpha evolution，通过 hierarchical reward 让 agent 学会 valid tool calls、performance improvement、long-horizon planning 和 reflective reasoning。

| 维度 | AlphaAgentEvo | TASE |
|---|---|---|
| 关键词 | Self-evolving alpha mining | Self-evolving workflow reconstruction |
| 学习对象 | Evolution policy for alphas | Workflow patch policy |
| 是否优化 alpha | 是 | 否 |
| 主要输出 | Evolved alphas | Reconstructed discovery workflow |
| 主指标 | pass@T / IR / AER / validity | degradation / PBO / false discovery / non-inferiority |

结论：AlphaAgentEvo 已经占据 “self-evolving financial agent improves alpha” 叙事。TASE 必须避开这个叙事，改成 “self-evolving meta-agent reconstructs discovery workflow under fixed search capacity to reduce false discovery”。


## 4. 两层任务定义

### 4.1 第一层：下游 trading evaluation environment

第一层是评测环境，不是本文研究对象。

输入包括 public OHLCV、fixed universe、fixed feature availability / timestamp rule、fixed operator library、fixed parameter grid、fixed candidate budget、fixed transaction cost、fixed train / validation / locked-test split、fixed portfolio construction rule，以及 fixed risk / turnover constraints。

输出包括每个 candidate 的 raw signal、train / validation / locked-test P&L、turnover / cost / drawdown、candidate-level diagnostics、selected ensemble 的 locked-test performance 和 reliability metrics。

注意：

> 第一层不是普通 daily trading demo，而是 strategy-discovery workflow 的 locked-test evaluation environment。

### 4.2 第二层：TASE meta-level task

第二层是本文真正研究对象。

输入包括 initial strategy-discovery workflow harness、workflow traces、validation diagnostics、accepted / rejected archive、pre-defined workflow patch space、patch budget、hard gates、locked-test isolation rule、finance-specific constraints。

输出包括 evolved workflow harness、accepted / rejected workflow patches、patch lineage、selected candidate ensemble、complete candidate archive、central ablation results，以及 reliability / non-inferiority evaluation。

目标：

> 证明 TASE 的 workflow reconstruction 所带来的 selection-reliability improvement 不能由 fixed workflow、validation-best selector、classic CSCV/PBO selector、same-budget safe workflow search、random legal patch、object-level strategy evolution、SHARP-style rubric evolution 或 generic unconstrained meta-harness 单独解释。


## 5. 核心经验前提：不存在单一最优 fixed workflow

Stage A1-Revised 必须新增一个前提检验：

> 如果存在一个 across folds / regimes / candidate distributions 都最优的 fixed workflow，那么 TASE 的 self-evolving workflow reconstruction 没有必要，H3 会再次零功效。

因此，实验必须先回答：

### Empirical Premise P0

> Is there no single fixed workflow that dominates across regimes and candidate-pool distributions?

需要输出每个 fixed workflow 在不同 fold / regime / candidate distribution 下的排名、workflow ranking instability、Kendall / Spearman rank stability、best fixed workflow 的 fold-to-fold turnover，以及 oracle fixed workflow vs deployable fixed workflow gap。

P0 支持条件：不同 fold / regime 下最优 fixed workflow 明显变化；fixed-best oracle 与 deployable fixed workflow 存在差距；workflow choice 不是 trivial constant decision。

P0 不支持时：Direction A 的 self-evolving contribution 弱化，只能保留为 diagnostic protocol 或 fixed workflow selection study。


## 6. Candidate Strategy / Factor Library

所有 arm 共用同一个 candidate library。TASE 不允许使用额外 operator、额外 data source、额外 parameter grid 或额外 candidate budget。

Candidate library 必须 pre-registered、fully reproducible、auditable、large enough to create false-discovery pressure、not post-hoc expanded，并且 candidate-level signal / P&L frozen。

建议 operator families：

1. Cross-sectional momentum
2. Time-series momentum
3. Short-term reversal
4. Medium-term reversal
5. Volatility
6. Low-volatility
7. Volatility-scaled momentum
8. Volume / liquidity
9. Moving-average crossover
10. Breakout
11. Residual momentum
12. Sector-neutral momentum
13. Rank combination
14. Simple two-factor combination
15. Risk-adjusted variants

建议规模：simple candidates 300–800，combination candidates 500–1200，总 candidate library 1000–2000。


## 7. Workflow Patch Space

### 7.1 TASE 可修改

TASE 可修改 workflow-level decisions：

- candidate generation schedule
- operator selection order
- validation split schedule among pre-registered choices
- walk-forward / CSCV aggregation rule
- pruning rule
- PBO penalty usage
- snooping-adjusted penalty usage
- turnover penalty usage
- drawdown / CVaR penalty usage
- cost penalty usage
- critic / reviewer loop
- leakage checker order
- risk reviewer loop
- retest policy
- rejection rule
- ensemble construction rule
- diversity constraint
- archive / memory retrieval policy
- rollback rule
- evidence threshold for acceptance
- invalid-high-score handling
- report / trace completeness rule

### 7.2 TASE 禁止修改

TASE 不能修改 raw data、universe、operator library、parameter grid、candidate budget、transaction cost、feature availability rule、locked test、final metric after validation、leakage gates、hard constraints、benchmark period、future returns、hidden filtering of failed candidates、rejected-candidate archive visibility、single candidate raw signal、single candidate P&L curve。


## 8. Workflow Boundary Gates

### 8.1 Per-candidate invariance gate

对于固定 candidate library 中的每个 candidate：

> workflow patch 前后，该 candidate 的 raw signal、per-period return series、turnover series、cost-adjusted P&L curve 必须一致。

如果发生变化，说明 patch 偷改了 alpha / strategy / evaluation protocol，应 reject。

### 8.2 Budget invariance gate

所有 searchable arms 必须满足 same candidate generation budget、same candidate evaluation budget、same number of workflow patch proposals、true evaluated candidate count logged、failed candidates counted and not hidden。

### 8.3 Archive completeness gate

必须保留 accepted candidates、rejected candidates、failed candidates、invalid candidates、retested candidates。Hidden / dropped candidate count 必须为 0。

### 8.4 Locked-test isolation gate

任何 workflow patch 不允许 read locked-test result、select based on locked-test metric、change locked-test window、change final metric after validation、change transaction cost after validation。

### 8.5 Negative controls

以下 bad patches 必须 100% rejected：add new operator、expand parameter grid、change locked split、use locked-test feedback、weaken transaction cost、weaken leakage gate、increase candidate budget、hide rejected candidates、silently drop failed candidates、change final metric after validation、use future returns、alter candidate P&L curve。


## 9. Baselines

### 9.1 Fixed Research Workflow
控制“不进化”。

### 9.2 Validation-Best Selector
贪婪选择 validation 最好 candidate / ensemble。用于抽象 naive alpha mining / quant AutoML / validation-max baseline。必须作为核心 baseline。

### 9.3 Classic CSCV / PBO-based Selector
使用经典 CSCV / PBO 逻辑进行候选筛选。用于防止 reviewer 说 TASE 只是传统 model selection 的 agent 包装。必须作为核心 baseline。

### 9.4 Same-Budget Safe Workflow Search
在 pre-defined safe workflow configs 中同预算搜索最佳 workflow。用于排除“只是多试几个安全配置”。

### 9.5 Random Legal Workflow Patch
从合法 workflow patch space 中随机选 patch。用于排除“合法随机改也一样”。

### 9.6 Object-Level Strategy Search / Strategy Tuning
允许改 candidate strategy / factor parameters。用于排除“其实是 object-level strategy evolution”。FactorEngine / CogAlpha / AlphaAgentEvo 归入该类 prior / abstract baseline。

### 9.7 RD-Agent(Q)-style Research Loop Baseline
轻量 faithful baseline：自动化 research / hypothesis / model loop，允许更自由的 factor / model iteration，记录 candidate count。不作为 legal workflow comparison，而是展示 research-throughput automation 与 workflow reliability 的区别。

### 9.8 SHARP-style Rubric / Policy Evolution
只演化 rubric / policy rules，不重构 full research workflow，budget 相同，不扩 candidate space。

### 9.9 Generic Unconstrained Meta-Harness
允许 broader unconstrained workflow changes，如 weaken gates、hide rejected candidates、use invalid shortcuts。所有 invalid candidates 必须被记录和 hard-gated。

### 9.10 TASE Finance-Constrained Workflow Harness
本文方法。

### 9.11 Passive / Equal-Weight Baseline
金融参考下限，不参与核心 method comparison。


## 10. Metrics

### 10.1 Primary metrics：Selection Reliability

主指标：

- validation-to-locked degradation
- PBO
- White Reality Check / SPA-like adjusted p-value
- Deflated Sharpe
- false-discovery proxy
- selected candidate stability across folds/seeds
- selected ensemble stability
- invalid-high-score rejection rate
- no-valid-candidate rate
- audit completeness
- archive completeness

### 10.2 Non-inferiority performance constraint

Performance 不是胜负标准，而是约束。

需要检查 locked-test net return、locked-test Sharpe、turnover-adjusted return、max drawdown、CVaR、turnover、transaction cost。

示例判定：

> TASE performance non-inferiority holds if paired CI lower bound of locked-test net performance difference is above the pre-registered non-inferiority margin.

不能写 “TASE wins because raw return is higher”。只能写 “TASE improves selection reliability while satisfying performance non-inferiority”。

### 10.3 Safety / validity metrics

包括 leakage violation count、boundary violation count、hidden rejected-candidate violation、failed-candidate retention rate、true evaluated candidate count、invalid selected candidate count、invalid high-score count。

### 10.4 Workflow efficiency metrics

包括 search efficiency、number of candidates evaluated before acceptance、archive reuse rate、accepted / rejected ratio、critic disagreement rate、retest frequency、rollback frequency。


## 11. Hypotheses

### H0：No single fixed workflow dominates
不同 market regime / candidate distribution 下，best fixed workflow 不稳定。

### H1：Unconstrained meta-harness exploits invalid high-score paths
Generic unconstrained meta-harness 更容易 weaken gates、hide rejected candidates、expand budget、use test feedback、select invalid high-score candidates。

### H2：Hard gates enforce legal workflow reconstruction
TASE accepted patches 必须 pass per-candidate invariance、budget invariance、archive completeness、locked-test isolation 和 negative controls。

### H3：TASE improves selection reliability over same-budget safe workflow search
TASE 相比 Same-Budget Safe Workflow Search，在至少两个 primary reliability metrics 上改善，并满足 performance non-inferiority。

### H4：TASE improves selection reliability over random legal workflow patch
同 H3，对 Random Legal Workflow Patch。

### H5：TASE beats validation-best on false-discovery control
TASE 相比 Validation-Best Selector：degradation lower、PBO lower、false-discovery proxy lower，并且 performance non-inferiority holds 或 trade-off 被清楚报告。

### H6：TASE is not explained by object-level strategy evolution or SHARP-style evolution
TASE 的增量不能被 Object-Level Strategy Search、SHARP-style Rubric / Policy Evolution、RD-Agent(Q)-style Research Loop 单独解释。


## 12. Success Criteria

TASE 成功必须同时满足：

1. H0 支持：workflow choice 非 trivial；
2. H1 支持：unconstrained harness 会产生 invalid high-score risk；
3. H2 支持：TASE hard gates 有效；
4. H3 或 H4 至少一个支持；
5. H5 支持或至少 mixed positive；
6. performance non-inferiority 成立；
7. candidate evaluation budget 公平；
8. per-candidate invariance gate 通过；
9. rejected / failed archive 完整；
10. 不靠 object-level strategy expansion。

失败条件：

- 只赢 raw return，不赢 reliability；
- 靠更多 candidate evaluations；
- 靠新增 operator；
- 靠隐藏 failed/rejected candidates；
- locked-test performance 显著变差；
- 打不过 Random Legal Workflow Patch；
- 与 Same-Budget Safe Search 无差异；
- 与 classic CSCV / PBO selector 无差异；
- RD-Agent(Q)-style baseline 在 reliability 和 performance 上都更好；
- boundary gate 失败。


## 13. Experimental Scale

### 13.1 Full Run

建议 full run：

- universe: approximate PIT US stock universe；
- date range: 2007–2024；
- rolling folds: at least 7；
- seeds: 10；
- candidate library: 1000–2000 candidates；
- workflow patch budget: 100 per searchable arm per seed；
- candidate evaluation budget: equal across arms；
- transaction cost: fixed；
- checkpoint / resume required；
- no quick / MVP downgrade。

### 13.2 Robustness Run

Robustness 不是 mini MVP，而是 full robustness：

- ETF sanity tier；
- transaction cost sensitivity：5 / 10 / 20 bps；
- candidate library size sensitivity：small / medium / large；
- regime split：2008 crisis, 2020 shock, 2022 rate regime；
- locked-test shift；
- current constituents appendix；
- optional China A-share robustness only if data quality is controlled。


## 14. Reporting Artifacts

必须输出：

- candidate_library.csv
- candidate_archive.csv
- accepted_candidates.csv
- rejected_candidates.csv
- failed_candidates.csv
- workflow_patch_log.csv
- invalid_high_score_log.csv
- per_candidate_invariance_gate_report.csv
- budget_invariance_report.csv
- archive_completeness_report.csv
- workflow_summary_metrics.csv
- fixed_workflow_rank_instability.csv
- paired_bootstrap_results.csv
- pbo_results.csv
- spa_reality_check_results.csv
- baseline_comparison_table.csv
- plain_chinese_summary.md
- paper_ready_tables.md


## 15. Stage A1-Revised 通过条件

进入 Codex 实现前，必须满足：

1. Novelty statement 已换成 non-performance 版本；
2. FactorEngine / CogAlpha / AlphaAgentEvo 已归类为 object-level alpha generation / evolution prior；
3. RD-Agent(Q)-style Research Loop baseline 已写入；
4. Classic CSCV / PBO Selector 已写入；
5. Validation-Best Selector 已写入；
6. H0 “no single fixed workflow dominates” 已写入；
7. Performance 被定义为 non-inferiority constraint；
8. Primary dependent variable 是 selection reliability；
9. Per-candidate invariance gate 已写入；
10. Archive completeness / budget invariance / locked-test isolation gates 已写入。

结论：

> Stage A1-Revised 可以进入 Stage A2：让 Claude / Grok / Gemini 基于本文件做最终 collision + experiment-spec review。如果至少两个外部审查为 PASS 或 PASS WITH MINOR REVISIONS，再进入 Codex full implementation prompt。
