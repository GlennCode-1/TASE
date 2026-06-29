# T.A.S.E S&P 500 Short-Window Diagnostic Report

## Purpose

This is a current-constituent, survivor-biased short-window diagnostic task. It is not used to claim investable profitability or unbiased S&P 500 performance. The task asks whether finance-typed harness patches become observable on individual-stock OHLCV data with missingness, stale prices, bad ticks, failed downloads, and corporate-action adjustment issues.

## Data And Task

- Constituents source: https://en.wikipedia.org/wiki/List_of_S%26P_500_companies
- Constituents retrieved at: 2026-06-29
- Requested date window: 2021-01-01 to 2024-12-31
- Effective evaluation window: 2021-01-04 to 2024-12-30
- Retained stocks: 493
- Minimum retained stocks: 300
- Search budget per core arm: 60
- Seeds: 5
- Fixed strategy: lagged 20-day momentum minus lagged 20-day volatility penalty; weekly top-k long-only allocation; adjusted close; transaction costs.

## Candidate Counts

| arm                         |   candidate_id |
|:----------------------------|---------------:|
| Constrained Safe Search     |            300 |
| Lightweight Strategy Tuning |            270 |
| Random Legal Patch          |            300 |
| TASE Typed Harness          |            300 |
| Unconstrained Search        |            300 |

## Headline Metrics

| arm                         |   locked_sharpe |   locked_cumulative_return |   locked_max_drawdown |   validation_to_locked_degradation |   turnover |   hit_rate |   active_asset_count |   cash_ratio |   leakage_violation_count |   strategy_boundary_violation_count |   availability_audit_pass_rate |   constraint_violation_count |   valid_selection_rate |   true_candidate_count |   valid_candidate_count |
|:----------------------------|----------------:|---------------------------:|----------------------:|-----------------------------------:|-----------:|-----------:|---------------------:|-------------:|--------------------------:|------------------------------------:|-------------------------------:|-----------------------------:|-----------------------:|-----------------------:|------------------------:|
| Unconstrained Search        |        1.44856  |                  0.0665538 |             -0.107656 |                          -0.291779 |  0.169854  |   0.454545 |              24.1525 |   0.192368   |                       0.2 |                            0.733333 |                            0.8 |                          1.4 |                    0.8 |                    300 |                       7 |
| Constrained Safe Search     |        0.730424 |                  0.059922  |             -0.13293  |                          -0.253952 |  0.20031   |   0.52862  |              30      |   0.0133333  |                       0   |                            0        |                            1   |                          0   |                    1   |                    300 |                     300 |
| Random Legal Patch          |        0.732795 |                  0.0621784 |             -0.133938 |                          -0.266448 |  0.202241  |   0.528956 |              29.9997 |   0.00401122 |                       0   |                            0        |                            1   |                          0   |                    1   |                    300 |                     300 |
| TASE Typed Harness          |        0.730424 |                  0.059922  |             -0.13293  |                          -0.253952 |  0.20031   |   0.52862  |              30      |   0.0133333  |                       0   |                            0        |                            1   |                          0   |                    1   |                    300 |                     300 |
| Lightweight Strategy Tuning |        0.805388 |                  0.0643507 |             -0.125699 |                           0.268671 |  0.0741975 |   0.530303 |              35      |   0          |                       0   |                            1        |                            1   |                          1   |                    1   |                    270 |                     270 |

## Paired Block Bootstrap

| comparison                                   | metric                |   mean_diff |      ci_low |      ci_high |   n_pairs |   block_size |
|:---------------------------------------------|:----------------------|------------:|------------:|-------------:|----------:|-------------:|
| TASE Typed Harness - Constrained Safe Search | oos_sharpe            |  0          |  0          |  0           |        30 |            5 |
| TASE Typed Harness - Constrained Safe Search | oos_cumulative_return |  0          |  0          |  0           |        30 |            5 |
| TASE Typed Harness - Random Legal Patch      | oos_sharpe            | -0.00237075 | -0.00711224 |  5.92119e-17 |        30 |            5 |
| TASE Typed Harness - Random Legal Patch      | oos_cumulative_return | -0.00225641 | -0.00344343 | -0.00122516  |        30 |            5 |

## H1a-H5 Judgment

- H1a supported: True
- H1b supported: False
- H2 supported: True
- H3 supported: False
- H4 supported: False
- H5 supported: False

## Interpretation Rules

Leakage-failing or strategy-boundary-failing candidates are not allowed into valid selection. They are reported only as invalid high-score evidence. DSR is intentionally not reported here; paired block bootstrap on selected locked results is used for TASE-vs-baseline differences.

## Recommendation

保留为股票数据流程诊断，先改合法 patch 的选择空间，再谈扩大。
