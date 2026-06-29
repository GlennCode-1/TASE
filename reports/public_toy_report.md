# T.A.S.E Public ETF Toy Report

## Purpose

This public-data toy task does not test live profitability. It asks whether finance-typed harness reconstruction reduces backtest-overfitting risk on a fixed ETF OHLCV universe under equal selection budgets.

## Data And Task

- Universe: SPY, QQQ, IWM, EFA, EEM, TLT, IEF, GLD, VNQ, XLF, XLK, XLE, XLI, XLU, XLP, XLY
- Date request: 2007-01-01 to 2024-12-31
- Run mode: full
- Effective evaluation window: 2007-02-02 to 2024-12-30
- Task: long-only weekly ETF allocation, top-k equal weight, adjusted close, transaction costs, no leverage, no shorting.
- Fixed strategy pi: lagged 20-day momentum minus lagged 20-day volatility penalty.
- TASE patches must preserve pre-cost target weights and pass feature-lag, pi-invariance, and future-return placebo checks.

## Arms

- MetaHarness Unconstrained: same budget, broader harness changes, basic audit only.
- Constrained Safe Search: same-budget safe configuration search, no meta proposer.
- Random Legal Patch: same legal TASE space, random choice.
- TASE Typed Harness: typed harness reconstruction with pi-invariance gates.
- Lightweight Strategy Evolution: small strategy-parameter search with fixed harness.
- SHARP-style Policy Baseline: bounded condition-action policy tuning.
- Passive baselines: equal-weight buy-and-hold and 60/40 proxy.

## Candidate Counts

| arm                            |   candidate_id |
|:-------------------------------|---------------:|
| Constrained Safe Search        |             12 |
| Lightweight Strategy Evolution |             12 |
| MetaHarness Unconstrained      |             12 |
| Random Legal Patch             |             12 |
| SHARP-style Policy Baseline    |             12 |
| TASE Typed Harness             |             12 |

## Headline Metrics

| arm                            |   locked_sharpe |   locked_cumulative_return |   locked_max_drawdown |   turnover |   leakage_audit_pass_rate |   pi_invariance_pass_rate |   constraint_violation_count |   pbo_estimate |   is_oos_rank_correlation |   validation_to_oos_degradation |   deflated_sharpe_ratio |   spa_like_pvalue |   true_candidate_count |   mean_split_candidate_count |
|:-------------------------------|----------------:|---------------------------:|----------------------:|-----------:|--------------------------:|--------------------------:|-----------------------------:|---------------:|--------------------------:|--------------------------------:|------------------------:|------------------:|-----------------------:|-----------------------------:|
| MetaHarness Unconstrained      |        3.86933  |                   1.79861  |            -0.0698887 |  0.230789  |                         0 |                         1 |                          3   |            0   |                  0.704965 |                      -0.439272  |              134.766    |          0.184615 |                     12 |                           12 |
| Constrained Safe Search        |        0.468112 |                   0.14761  |            -0.140369  |  0.155639  |                         1 |                         1 |                          0   |            0   |                  0        |                       0.113792  |               21.012    |          1        |                     12 |                           12 |
| Random Legal Patch             |        0.468112 |                   0.14761  |            -0.140369  |  0.155639  |                         1 |                         1 |                          0   |            0   |                  0        |                       0.113792  |               21.012    |          1        |                     12 |                           12 |
| TASE Typed Harness             |        0.468112 |                   0.14761  |            -0.140369  |  0.155639  |                         1 |                         1 |                          0   |            0   |                  0        |                       0.113792  |               21.012    |          1        |                     12 |                           12 |
| Lightweight Strategy Evolution |        0.659947 |                   0.234631 |            -0.140399  |  0.0901003 |                         1 |                         1 |                          1   |            0.2 |                  0.177622 |                       0.0342716 |               25.498    |          0.461538 |                     12 |                           12 |
| SHARP-style Policy Baseline    |        0.468112 |                   0.14761  |            -0.140369  |  0.155639  |                         1 |                         1 |                          0.4 |            0.2 |                  0        |                       0.114913  |               21.3048   |          0.938462 |                     12 |                           12 |
| Equal Weight Buy Hold          |        0.480471 |                   0.152073 |            -0.140444  |  0.156203  |                         1 |                         1 |                          0   |            0   |                  0        |                       0         |                0.480471 |          1        |                      1 |                          nan |
| 60/40 Proxy                    |        0.480471 |                   0.152073 |            -0.140444  |  0.156203  |                         1 |                         1 |                          0   |            0   |                  0        |                       0         |                0.480471 |          1        |                      1 |                          nan |

## H1-H5 Judgment

- H1 supported: False
- H2 supported: True
- H3 supported: False
- H4 supported: False
- H5 supported: False

## Key Comparisons

- Unconstrained PBO: 0.000; TASE PBO: 0.000
- Unconstrained degradation: -0.439; TASE degradation: 0.114
- TASE DSR: 21.012; constrained-safe DSR: 21.012; random-legal DSR: 21.012

## Recommendation

暂停扩大实验，先修 public toy 设计或数据质量。
