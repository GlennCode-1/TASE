# T.A.S.E Public Full ETF Report

## Purpose

This public full run tests overfitting-adjusted robustness, not live trading profitability. It uses a larger fixed ETF candidate universe, equal search budgets, multiple rolling splits, and bootstrap confidence intervals.

## Data And Task

- Universe request: SPY, QQQ, IWM, DIA, VTI, EFA, EEM, EWJ, EWU, EWG, FXI, TLT, IEF, SHY, LQD, HYG, TIP, AGG, GLD, SLV, USO, DBC, VNQ, IYR, XLF, XLK, XLE, XLI, XLU, XLP, XLY, XLV, XLB, XLRE, MTUM, QUAL, USMV, VLUE, SIZE, SPLV, VUG, VTV, IVE, IVW, ARKK, SMH, XBI
- Minimum history coverage: 0.9
- Minimum retained assets: 30
- Retained assets in run: 39
- Filtered tickers: ARKK, MTUM, QUAL, SIZE, SPLV, USMV, VLUE, XLRE
- Date request: 2007-01-01 to 2024-12-31
- Run mode: full
- Effective evaluation window: 2007-05-10 to 2024-12-30
- Search budget per searchable arm: 100
- Seeds: 10

## Headline Metrics

| arm                            |   locked_sharpe |   locked_cumulative_return |   locked_max_drawdown |   turnover |   leakage_audit_pass_rate |   pi_invariance_pass_rate |   constraint_violation_count |   pbo_estimate |   is_oos_rank_correlation |   validation_to_oos_degradation |   deflated_sharpe_ratio |   spa_like_pvalue |   true_candidate_count |   mean_split_candidate_count |
|:-------------------------------|----------------:|---------------------------:|----------------------:|-----------:|--------------------------:|--------------------------:|-----------------------------:|---------------:|--------------------------:|--------------------------------:|------------------------:|------------------:|-----------------------:|-----------------------------:|
| MetaHarness Unconstrained      |       22.0373   |                1149.22     |           -0.00306851 |  0.811989  |                         0 |                         1 |                     2.4      |       0        |                  0.535631 |                      -1.7501    |              763.276    |          0.016983 |                   1000 |                         1000 |
| Constrained Safe Search        |        0.506754 |                   0.248997 |           -0.168273   |  0.165505  |                         1 |                         1 |                     0        |       0        |                  0        |                      -0.228283  |                7.36944  |          1        |                   1000 |                         1000 |
| Random Legal Patch             |        0.506754 |                   0.248997 |           -0.168273   |  0.165505  |                         1 |                         1 |                     0        |       0        |                  0        |                      -0.228283  |                7.36944  |          1        |                   1000 |                         1000 |
| TASE Typed Harness             |        0.506754 |                   0.248997 |           -0.168273   |  0.165505  |                         1 |                         1 |                     0        |       0        |                  0        |                      -0.228283  |                7.36944  |          1        |                   1000 |                         1000 |
| Lightweight Strategy Evolution |        0.419    |                   0.156079 |           -0.18339    |  0.0658406 |                         1 |                         1 |                     0.857143 |       0.571429 |                  0.185514 |                       0.0725423 |               15.2075   |          0.460539 |                   1000 |                         1000 |
| SHARP-style Policy Baseline    |        0.512774 |                   0.252037 |           -0.165509   |  0.165914  |                         1 |                         1 |                     0.285714 |       0.714286 |                 -0.428571 |                      -0.215517  |                7.69327  |          0.988583 |                   1000 |                         1000 |
| Equal Weight Buy Hold          |        0.499597 |                   0.244308 |           -0.168273   |  0.164141  |                         1 |                         1 |                     0        |       0        |                  0        |                       0         |                0.499597 |          1        |                      1 |                          nan |
| 60/40 Proxy                    |        0.499597 |                   0.244308 |           -0.168273   |  0.164141  |                         1 |                         1 |                     0        |       0        |                  0        |                       0         |                0.499597 |          1        |                      1 |                          nan |

## Bootstrap CI

| arm                            | metric        |      mean |    ci_low |   ci_high |   n_bootstrap |
|:-------------------------------|:--------------|----------:|----------:|----------:|--------------:|
| MetaHarness Unconstrained      | locked_sharpe | 22.0373   | 21.5605   | 22.5448   |           200 |
| Constrained Safe Search        | locked_sharpe |  0.506754 |  0.419562 |  0.616865 |           200 |
| Random Legal Patch             | locked_sharpe |  0.506754 |  0.412312 |  0.628049 |           200 |
| TASE Typed Harness             | locked_sharpe |  0.506754 |  0.391458 |  0.614402 |           200 |
| Lightweight Strategy Evolution | locked_sharpe |  0.419    |  0.35965  |  0.455679 |           200 |
| SHARP-style Policy Baseline    | locked_sharpe |  0.512774 |  0.413946 |  0.606696 |           200 |
| Equal Weight Buy Hold          | locked_sharpe |  0.499597 |  0.406107 |  0.600122 |           200 |
| 60/40 Proxy                    | locked_sharpe |  0.499597 |  0.382888 |  0.617658 |           200 |

## Candidate Counts

| arm                            |   candidate_id |
|:-------------------------------|---------------:|
| Constrained Safe Search        |           1000 |
| Lightweight Strategy Evolution |           1000 |
| MetaHarness Unconstrained      |           1000 |
| Random Legal Patch             |           1000 |
| SHARP-style Policy Baseline    |           1000 |
| TASE Typed Harness             |           1000 |

## H1-H5 Judgment

- H1 supported: False
- H2 supported: True
- H3 supported: False
- H4 supported: False
- H5 supported: False

## Important Interpretation Note

The unconstrained arm can show very high raw locked metrics, but it fails the leakage/constraint audit. This report therefore does not treat that raw score as a profitability claim or as sufficient support for TASE.

## Recommendation

暂停扩大实验，先修 public toy 设计或数据质量。
