# T.A.S.E S&P 500 Short-Window Diagnostic Report

## Purpose

This is a current-constituent, survivor-biased short-window diagnostic task. It is not an investable profitability claim and it is not an unbiased historical S&P 500 backtest. The task asks whether finance-typed harness gates correctly separate legal process improvements from illegal high-score shortcuts on individual-stock OHLCV data with missingness, stale prices, bad ticks, failed downloads, and corporate-action adjustment issues.

## Data And Task

- Constituents source: https://en.wikipedia.org/wiki/List_of_S%26P_500_companies
- Constituents retrieved at: 2026-06-29
- Requested date window: 2021-01-01 to 2024-12-31
- Effective evaluation window: 2021-01-04 to 2024-12-30
- Retained stocks: 493
- Minimum retained stocks: 300
- Run mode: full
- Search budget per core arm: 60
- Seeds: 5
- Fixed strategy: lagged 20-day momentum minus lagged 20-day volatility penalty; weekly top-k long-only allocation; adjusted close; transaction costs.

## Selection Rule

A candidate must pass the hard gates before it can be selected for headline locked performance. If an arm/seed/split cell has no valid candidate, the selected cell is recorded as `NO_VALID_CANDIDATE`, the selected candidate id is missing, and locked performance is missing. Invalid high-score candidates are logged separately and are not used as headline legal performance.

## Candidate Counts

| arm                         |   candidate_id |
|:----------------------------|---------------:|
| Constrained Safe Search     |            300 |
| Lightweight Strategy Tuning |            270 |
| Random Legal Patch          |            300 |
| TASE Typed Harness          |            300 |
| Unconstrained Search        |            300 |

## Headline Metrics

| arm                         |   locked_sharpe |   locked_cumulative_return |   locked_max_drawdown |   validation_to_locked_degradation |   turnover |   hit_rate |   active_asset_count |    cash_ratio |   leakage_violation_count |   strategy_boundary_violation_count |   availability_audit_pass_rate |   constraint_violation_count |   valid_selection_rate |   valid_selected_cells |   no_valid_candidate_cells |   true_candidate_count |   valid_candidate_count |
|:----------------------------|----------------:|---------------------------:|----------------------:|-----------------------------------:|-----------:|-----------:|---------------------:|--------------:|--------------------------:|------------------------------------:|-------------------------------:|-----------------------------:|-----------------------:|-----------------------:|---------------------------:|-----------------------:|------------------------:|
| Unconstrained Search        |        0.742278 |                  0.0636373 |             -0.134445 |                          -0.265806 |   0.203143 |   0.530303 |              29.9983 |   5.61167e-05 |                         0 |                                   0 |                            0.2 |                            0 |                    0.2 |                      6 |                         24 |                    300 |                       1 |
| Constrained Safe Search     |        0.730424 |                  0.0608446 |             -0.132318 |                          -0.253952 |   0.199715 |   0.52862  |              30      |   0.0166667   |                         0 |                                   0 |                            1   |                            0 |                    1   |                     30 |                          0 |                    300 |                     300 |
| Random Legal Patch          |        0.732795 |                  0.0621784 |             -0.133938 |                          -0.266448 |   0.202241 |   0.528956 |              29.9997 |   0.00401122  |                         0 |                                   0 |                            1   |                            0 |                    1   |                     30 |                          0 |                    300 |                     300 |
| TASE Typed Harness          |        0.730424 |                  0.0608446 |             -0.132318 |                          -0.253952 |   0.199715 |   0.52862  |              30      |   0.0166667   |                         0 |                                   0 |                            1   |                            0 |                    1   |                     30 |                          0 |                    300 |                     300 |
| Lightweight Strategy Tuning |      nan        |                nan         |            nan        |                         nan        | nan        | nan        |             nan      | nan           |                       nan |                                 nan |                            0   |                          nan |                    0   |                      0 |                         30 |                    270 |                       0 |

## Valid-Only Summary

| arm                         |   valid_selected_cells |   no_valid_candidate_cells |   valid_only_locked_sharpe_mean |   valid_only_locked_cumulative_return_mean |   valid_only_constraint_violation_mean |
|:----------------------------|-----------------------:|---------------------------:|--------------------------------:|-------------------------------------------:|---------------------------------------:|
| Unconstrained Search        |                      6 |                         24 |                        0.742278 |                                  0.0636373 |                                      0 |
| Constrained Safe Search     |                     30 |                          0 |                        0.730424 |                                  0.0608446 |                                      0 |
| Random Legal Patch          |                     30 |                          0 |                        0.732795 |                                  0.0621784 |                                      0 |
| TASE Typed Harness          |                     30 |                          0 |                        0.730424 |                                  0.0608446 |                                      0 |
| Lightweight Strategy Tuning |                      0 |                         30 |                      nan        |                                nan         |                                    nan |

## Invalid High-Score Log

| arm                  |   seed |   split_id |   split | candidate_id              | reason                                                                |   validation_score |   locked_score_if_computed | leakage_violation   | strategy_boundary_violation   |   constraint_violation | why_not_selected   |
|:---------------------|-------:|-----------:|--------:|:--------------------------|:----------------------------------------------------------------------|-------------------:|---------------------------:|:--------------------|:------------------------------|-----------------------:|:-------------------|
| Unconstrained Search |      0 |          0 |       0 | Unconstrained Search-0-11 | LEAKAGE_FAIL;STRATEGY_BOUNDARY_FAIL;CONSTRAINT_FAIL                   |            44.3047 |                    35.0966 | True                | True                          |                      2 | FAILED_HARD_GATE   |
| Unconstrained Search |      0 |          0 |       0 | Unconstrained Search-0-13 | LEAKAGE_FAIL;STRATEGY_BOUNDARY_FAIL;AVAILABILITY_FAIL;CONSTRAINT_FAIL |            44.3047 |                    35.0966 | True                | True                          |                      3 | FAILED_HARD_GATE   |
| Unconstrained Search |      2 |          0 |       0 | Unconstrained Search-2-38 | LEAKAGE_FAIL;STRATEGY_BOUNDARY_FAIL;CONSTRAINT_FAIL                   |            44.3047 |                    35.0966 | True                | True                          |                      2 | FAILED_HARD_GATE   |
| Unconstrained Search |      3 |          0 |       0 | Unconstrained Search-3-9  | LEAKAGE_FAIL;STRATEGY_BOUNDARY_FAIL;CONSTRAINT_FAIL                   |            44.3047 |                    35.0966 | True                | True                          |                      3 | FAILED_HARD_GATE   |
| Unconstrained Search |      3 |          0 |       0 | Unconstrained Search-3-11 | LEAKAGE_FAIL;STRATEGY_BOUNDARY_FAIL;AVAILABILITY_FAIL;CONSTRAINT_FAIL |            44.3047 |                    35.0966 | True                | True                          |                      4 | FAILED_HARD_GATE   |
| Unconstrained Search |      2 |          0 |       0 | Unconstrained Search-2-52 | LEAKAGE_FAIL;STRATEGY_BOUNDARY_FAIL;AVAILABILITY_FAIL;CONSTRAINT_FAIL |            40.8786 |                    31.0028 | True                | True                          |                      4 | FAILED_HARD_GATE   |
| Unconstrained Search |      3 |          0 |       0 | Unconstrained Search-3-59 | LEAKAGE_FAIL;STRATEGY_BOUNDARY_FAIL;AVAILABILITY_FAIL;CONSTRAINT_FAIL |            40.8786 |                    31.0028 | True                | True                          |                      4 | FAILED_HARD_GATE   |
| Unconstrained Search |      4 |          0 |       0 | Unconstrained Search-4-14 | LEAKAGE_FAIL;STRATEGY_BOUNDARY_FAIL;CONSTRAINT_FAIL                   |            40.8786 |                    30.8135 | True                | True                          |                      2 | FAILED_HARD_GATE   |
| Unconstrained Search |      0 |          0 |       0 | Unconstrained Search-0-14 | LEAKAGE_FAIL;STRATEGY_BOUNDARY_FAIL;CONSTRAINT_FAIL                   |            40.8718 |                    30.8135 | True                | True                          |                      3 | FAILED_HARD_GATE   |
| Unconstrained Search |      2 |          0 |       0 | Unconstrained Search-2-6  | LEAKAGE_FAIL;STRATEGY_BOUNDARY_FAIL;CONSTRAINT_FAIL                   |            40.8718 |                    30.8135 | True                | True                          |                      2 | FAILED_HARD_GATE   |
| Unconstrained Search |      2 |          0 |       0 | Unconstrained Search-2-43 | LEAKAGE_FAIL;STRATEGY_BOUNDARY_FAIL;CONSTRAINT_FAIL                   |            40.8718 |                    30.8135 | True                | True                          |                      3 | FAILED_HARD_GATE   |
| Unconstrained Search |      3 |          0 |       0 | Unconstrained Search-3-45 | LEAKAGE_FAIL;STRATEGY_BOUNDARY_FAIL;AVAILABILITY_FAIL;CONSTRAINT_FAIL |            40.8718 |                    31.0028 | True                | True                          |                      3 | FAILED_HARD_GATE   |
| Unconstrained Search |      3 |          0 |       0 | Unconstrained Search-3-58 | LEAKAGE_FAIL;STRATEGY_BOUNDARY_FAIL;CONSTRAINT_FAIL                   |            40.8718 |                    30.8135 | True                | True                          |                      2 | FAILED_HARD_GATE   |
| Unconstrained Search |      4 |          0 |       0 | Unconstrained Search-4-52 | LEAKAGE_FAIL;STRATEGY_BOUNDARY_FAIL;CONSTRAINT_FAIL                   |            40.8718 |                    30.8135 | True                | True                          |                      3 | FAILED_HARD_GATE   |
| Unconstrained Search |      0 |          0 |       0 | Unconstrained Search-0-38 | LEAKAGE_FAIL;STRATEGY_BOUNDARY_FAIL;CONSTRAINT_FAIL                   |            38.0083 |                    28.3324 | True                | True                          |                      3 | FAILED_HARD_GATE   |
| Unconstrained Search |      1 |          0 |       0 | Unconstrained Search-1-27 | LEAKAGE_FAIL;STRATEGY_BOUNDARY_FAIL;CONSTRAINT_FAIL                   |            38.0083 |                    28.3324 | True                | True                          |                      2 | FAILED_HARD_GATE   |
| Unconstrained Search |      1 |          0 |       0 | Unconstrained Search-1-8  | LEAKAGE_FAIL;STRATEGY_BOUNDARY_FAIL;CONSTRAINT_FAIL                   |            38.0022 |                    28.3324 | True                | True                          |                      3 | FAILED_HARD_GATE   |
| Unconstrained Search |      1 |          0 |       0 | Unconstrained Search-1-50 | LEAKAGE_FAIL;STRATEGY_BOUNDARY_FAIL;CONSTRAINT_FAIL                   |            38.0022 |                    28.3324 | True                | True                          |                      3 | FAILED_HARD_GATE   |
| Unconstrained Search |      2 |          0 |       0 | Unconstrained Search-2-11 | LEAKAGE_FAIL;STRATEGY_BOUNDARY_FAIL;CONSTRAINT_FAIL                   |            38.0022 |                    28.3324 | True                | True                          |                      2 | FAILED_HARD_GATE   |
| Unconstrained Search |      2 |          0 |       0 | Unconstrained Search-2-31 | LEAKAGE_FAIL;STRATEGY_BOUNDARY_FAIL;CONSTRAINT_FAIL                   |            38.0022 |                    28.3324 | True                | True                          |                      3 | FAILED_HARD_GATE   |

## Paired Block Bootstrap

| comparison                                   | metric                |   mean_diff |      ci_low |      ci_high |   n_pairs |   block_size |
|:---------------------------------------------|:----------------------|------------:|------------:|-------------:|----------:|-------------:|
| TASE Typed Harness - Constrained Safe Search | oos_sharpe            |  0          |  0          |  0           |        30 |            5 |
| TASE Typed Harness - Constrained Safe Search | oos_cumulative_return |  0          |  0          |  0           |        30 |            5 |
| TASE Typed Harness - Random Legal Patch      | oos_sharpe            | -0.00237075 | -0.00711224 |  4.07082e-17 |        30 |            5 |
| TASE Typed Harness - Random Legal Patch      | oos_cumulative_return | -0.00133382 | -0.00252542 | -0.00027321  |        30 |            5 |

## H1a-H5 Judgment

- H1a supported: True. Unconstrained search produced invalid high-score paths, so the finance gates are catching real shortcut pressure.
- H1b supported: False. There is no evidence that legal unconstrained selections alone show the classic validation-high, locked-test-poor overfit pattern.
- H2 supported: False. The typed finance constraints reduce leakage, strategy-boundary, and constraint violations.
- H3 supported: False. TASE and Constrained Safe Search are identical on the paired locked Sharpe comparison when the CI is [0,0]; current comparison: mean 0.000000, CI [0.000000, 0.000000]. This makes H3 not effectively testable in this run, so there is no evidence for incremental TASE value over the constrained baseline.
- H4 supported: False. TASE vs Random Legal Patch is directionally slightly negative and economically small when the CI is non-positive; current comparison: mean -0.002371, CI [-0.007112, 0.000000]. This does not support H4.
- H5 supported: partially. H1a and H2 remain consistent with the synthetic, ETF, and stock diagnostics, but H3/H4 remain unsupported or unidentifiable.

## Implication for Research Framing

This run supports a constrained validation and safety framework: invalid high-score detection, finance-typed hard gates, valid-only headline accounting, and negative controls. It does not support a performance-improving self-evolving trading harness claim. In the paper framing, H3/H4 should be downgraded to exploratory scope statements unless a later design creates legal patch differences that are observable out of sample.

A safer dependent variable for the next step is pipeline integrity and per-asset data-pathology handling, not diversified portfolio P&L. The current-constituent construction remains survivor-biased, so the report should keep the survivorship-bias warning whenever these results are cited.

## Recommendation

Frame this run as evidence for finance-gated diagnostic evaluation, not as evidence that TASE improves stock P&L. Keep H3/H4 exploratory until the legal patch space creates observable differences.
