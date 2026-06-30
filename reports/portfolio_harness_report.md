# Portfolio Construction / Risk Management Harness Diagnostic

## Purpose

This experiment freezes the alpha, portfolio policy, objective weights, risk appetite, constraints, universe, and rebalance frequency. It asks whether TASE can improve the implementation layer of portfolio construction and risk management: covariance estimation, solver fallback, constraint repair, turnover enforcement, missing/stale data handling, cost accounting, and exposure monitoring.

It does not test live profitability and it does not allow TASE to discover alpha.

## Fixed Specification

- Alpha: past 20-day momentum minus 0.5 times past 20-day volatility.
- Risk aversion lambda: 3.0
- Max weight: 0.18
- Turnover cap: 0.35
- Asset-class cap: 0.55
- Rebalance frequency: W-FRI
- Long-only, no leverage, fixed ETF universe.

## Data

- Requested window: 2007-01-01 to 2024-12-31
- Effective window: 2007-04-11 to 2024-12-30
- Retained ETFs: 39
- Run mode: quick smoke

## Arms

- Fixed Safe Portfolio Harness
- Same-Budget Safe Configuration Search
- Random Legal Harness Patch
- TASE Typed Portfolio Harness Reconstruction
- Unconstrained Portfolio Harness Search
- Portfolio Strategy Tuning Baseline
- Passive baselines: Equal Weight, Risk Parity, 60/40

## Candidate Counts

| arm                                         |   candidate_id |
|:--------------------------------------------|---------------:|
| Fixed Safe Portfolio Harness                |              1 |
| Portfolio Strategy Tuning Baseline          |             12 |
| Random Legal Harness Patch                  |             12 |
| Same-Budget Safe Configuration Search       |             12 |
| TASE Typed Portfolio Harness Reconstruction |             12 |
| Unconstrained Portfolio Harness Search      |             12 |

## Headline Risk / Harness Metrics

| arm                                         |   locked_cvar_95 |   locked_downside_deviation |   locked_sortino |   locked_calmar |   locked_max_drawdown |   locked_drawdown_duration |   realized_volatility |     turnover |   transaction_cost_paid |   turnover_adjusted_net_return |   constraint_violation_severity |   infeasible_optimization_events |   optimizer_recovery_success_rate |   failed_rebalance_retention_rate |   cash_ratio_due_to_infeasibility |   exposure_drift |   herfindahl_index |   diversification_ratio |   asset_class_cap_violation_severity |   high_vol_return |   normal_vol_return |   stress_recovery_return |   locked_cumulative_return |   locked_annualized_return |   locked_sharpe |   valid_selected_cells |   no_valid_candidate_cells |   true_candidate_count |   valid_candidate_count |
|:--------------------------------------------|-----------------:|----------------------------:|-----------------:|----------------:|----------------------:|---------------------------:|----------------------:|-------------:|------------------------:|-------------------------------:|--------------------------------:|---------------------------------:|----------------------------------:|----------------------------------:|----------------------------------:|-----------------:|-------------------:|------------------------:|-------------------------------------:|------------------:|--------------------:|-------------------------:|---------------------------:|---------------------------:|----------------:|-----------------------:|---------------------------:|-----------------------:|------------------------:|
| Fixed Safe Portfolio Harness                |       -0.0175034 |                    0.133325 |        -0.254658 |       0.0317155 |            -0.117435  |                    81.5714 |              0.13074  |   0.0778792  |             0.00670519  |                    -0.0361472  |                      0.0047776  |                                0 |                                 1 |                                 1 |                         0.0424537 |      0.0224537   |          0.0561486 |                 1.42441 |                                 0    |      -5.00772e-05 |        -0.000474828 |             -0.000822038 |               -0.029442    |                -0.0476872  |      -0.345488  |                      7 |                          0 |                      1 |                       1 |
| Same-Budget Safe Configuration Search       |       -0.0182402 |                    0.138519 |        -0.13787  |       0.127005  |            -0.11667   |                    81.8571 |              0.139424 |   0.0779905  |             0.00671781  |                    -0.0311511  |                      0.0048889  |                                0 |                                 1 |                                 1 |                         0.031802  |      0.011802    |          0.0564876 |                 1.42407 |                                 0    |      -1.06936e-05 |        -0.000444375 |             -0.000772763 |               -0.0244332   |                -0.0378264  |      -0.218967  |                      7 |                          0 |                     12 |                       6 |
| Random Legal Harness Patch                  |       -0.0182402 |                    0.138519 |        -0.13787  |       0.127005  |            -0.11667   |                    81.8571 |              0.139424 |   0.0779905  |             0.00671781  |                    -0.0311511  |                      0.0048889  |                                0 |                                 1 |                                 1 |                         0.031802  |      0.011802    |          0.0564876 |                 1.42407 |                                 0    |      -1.06936e-05 |        -0.000444375 |             -0.000772763 |               -0.0244332   |                -0.0378264  |      -0.218967  |                      7 |                          0 |                     12 |                       6 |
| TASE Typed Portfolio Harness Reconstruction |       -0.0179219 |                    0.135843 |        -0.202198 |       0.111461  |            -0.11911   |                    80.1429 |              0.134901 |   0.0779505  |             0.00671151  |                    -0.034346   |                      0.00484891 |                                0 |                                 1 |                                 1 |                         0.0386539 |      0.0186539   |          0.0554619 |                 1.42374 |                                 0    |      -5.20814e-05 |        -0.000461114 |             -0.000797338 |               -0.0276345   |                -0.043436   |      -0.301838  |                      7 |                          0 |                     12 |                       7 |
| Unconstrained Portfolio Harness Search      |      nan         |                  nan        |       nan        |     nan         |           nan         |                   nan      |            nan        | nan          |           nan           |                   nan          |                    nan          |                              nan |                               nan |                               nan |                       nan         |    nan           |        nan         |               nan       |                               nan    |     nan           |       nan           |            nan           |              nan           |               nan          |     nan         |                      0 |                          7 |                     12 |                       0 |
| Portfolio Strategy Tuning Baseline          |       -0.0168742 |                    0.130029 |         0.224069 |       0.598934  |            -0.0985339 |                    78.5714 |              0.130868 |   0.0197299  |             0.00183389  |                    -0.00118498 |                      0.00463462 |                                0 |                                 1 |                                 1 |                         0.05394   |      0.03394     |          0.0349254 |                 1.42467 |                                 0    |       7.80509e-05 |        -0.000188643 |             -0.000580346 |                0.000648911 |                 0.00940355 |       0.159806  |                      0 |                          0 |                     12 |                       0 |
| Equal Weight ETF Portfolio                  |       -0.0178866 |                    0.13753  |         0.255121 |       0.768537  |            -0.107891  |                    86.7143 |              0.141255 |   0.00778667 |             0.000805    |                    -0.00217251 |                      0.00500571 |                                0 |                                 1 |                                 1 |                         0.02      |      0           |          0.0246256 |                 1.42586 |                                 0    |       7.32908e-05 |        -0.000270544 |             -0.000553639 |               -0.00136751  |                 0.00829168 |       0.157167  |                      0 |                          0 |                      1 |                       0 |
| Risk Parity Fixed Portfolio                 |       -0.0130597 |                    0.100608 |         0.177737 |       0.743617  |            -0.0856508 |                    86.7143 |              0.103871 |   0.00778667 |             0.000805    |                    -0.00557935 |                      0.00500571 |                                0 |                                 1 |                                 1 |                         0.02      |      2.22045e-16 |          0.0489438 |                 1.45166 |                                 0    |       4.91258e-05 |        -0.000266906 |             -0.000487425 |               -0.00477435  |                -0.00224641 |       0.0676293 |                      0 |                          0 |                      1 |                       0 |
| 60/40 Portfolio                             |       -0.0158573 |                    0.118473 |         0.269762 |       0.933283  |            -0.103616  |                    83.7143 |              0.124227 |   0.00794558 |             0.000821429 |                    -0.00820749 |                      0.695165   |                                0 |                                 1 |                                 1 |                         0         |      0.02        |          0.52      |                 1.24105 |                                 0.05 |      -2.14589e-05 |        -0.000360495 |             -0.000417121 |               -0.00738606  |                -0.00360321 |       0.14332   |                      0 |                          0 |                      1 |                       0 |

## Invalid High-Score Log

| arm                                    |   seed |   split_id | candidate_id                                | reason                                                                        |   validation_score |   locked_score_if_computed | why_not_selected   |
|:---------------------------------------|-------:|-----------:|:--------------------------------------------|:------------------------------------------------------------------------------|-------------------:|---------------------------:|:-------------------|
| Unconstrained Portfolio Harness Search |      0 |          6 | Unconstrained Portfolio Harness Search-0-2  | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED |           3.77401  |                 0.940566   | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          0 | Unconstrained Portfolio Harness Search-0-2  | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED |           3.25254  |                 0.637204   | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          5 | Unconstrained Portfolio Harness Search-0-2  | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED |           2.9301   |                 0.794299   | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          4 | Unconstrained Portfolio Harness Search-0-2  | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED |           2.73847  |                 1.19943    | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          1 | Unconstrained Portfolio Harness Search-0-2  | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED |           2.64395  |                 0.518418   | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          3 | Unconstrained Portfolio Harness Search-0-2  | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED |           2.29633  |                 1.41492    | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          2 | Unconstrained Portfolio Harness Search-0-2  | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED |           2.08569  |                 1.07771    | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          0 | Unconstrained Portfolio Harness Search-0-9  | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED |           0.727528 |                 0.00156153 | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          6 | Unconstrained Portfolio Harness Search-0-9  | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED |           0.571433 |                 0.209786   | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          1 | Unconstrained Portfolio Harness Search-0-9  | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED |           0.470644 |                -0.0498822  | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          0 | Unconstrained Portfolio Harness Search-0-5  | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED |           0.442542 |                -0.0356281  | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          1 | Unconstrained Portfolio Harness Search-0-5  | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED |           0.393252 |                -0.112243   | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          6 | Unconstrained Portfolio Harness Search-0-5  | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED |           0.380553 |                 0.118614   | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          5 | Unconstrained Portfolio Harness Search-0-9  | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED |           0.325628 |                 0.135882   | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          4 | Unconstrained Portfolio Harness Search-0-9  | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED |           0.23146  |                 0.297593   | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          2 | Unconstrained Portfolio Harness Search-0-9  | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED |           0.197712 |                 0.202573   | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          6 | Unconstrained Portfolio Harness Search-0-4  | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED |           0.197349 |                 0.064082   | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          0 | Unconstrained Portfolio Harness Search-0-11 | POLICY_SPECIFICATION_CHANGED;CLEAN_PANEL_W_STAR_CHANGED                       |           0.194437 |                -0.131459   | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          0 | Unconstrained Portfolio Harness Search-0-8  | POLICY_SPECIFICATION_CHANGED;CLEAN_PANEL_W_STAR_CHANGED;LOOSE_COST_ACCOUNTING |           0.17667  |                -0.131826   | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          0 | Unconstrained Portfolio Harness Search-0-1  | POLICY_SPECIFICATION_CHANGED;CLEAN_PANEL_W_STAR_CHANGED                       |           0.174369 |                -0.125265   | FAILED_HARD_GATE   |

## Paired Block Bootstrap

| comparison                                                                          | metric                          |    mean_diff |        ci_low |      ci_high |   n_pairs |   block_size |
|:------------------------------------------------------------------------------------|:--------------------------------|-------------:|--------------:|-------------:|----------:|-------------:|
| TASE Typed Portfolio Harness Reconstruction - Fixed Safe Portfolio Harness          | cvar_95                         | -0.000418458 |  -0.000714939 | -8.80375e-05 |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Fixed Safe Portfolio Harness          | drawdown_duration               | -1.42857     |  -3           |  0.142857    |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Fixed Safe Portfolio Harness          | turnover                        |  7.13043e-05 |   1.29844e-05 |  0.000136974 |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Fixed Safe Portfolio Harness          | transaction_cost_paid           |  6.32275e-06 |   4.31199e-07 |  1.1859e-05  |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Fixed Safe Portfolio Harness          | constraint_violation_severity   |  7.13043e-05 |   1.29844e-05 |  0.000129808 |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Fixed Safe Portfolio Harness          | optimizer_recovery_success_rate |  0           |   0           |  0           |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Fixed Safe Portfolio Harness          | turnover_adjusted_net_return    |  0.00180121  |  -0.00112902  |  0.00473145  |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Same-Budget Safe Configuration Search | cvar_95                         |  0.000318349 |   0           |  0.000636697 |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Same-Budget Safe Configuration Search | drawdown_duration               | -1.71429     |  -3.42857     |  0           |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Same-Budget Safe Configuration Search | turnover                        | -3.99977e-05 |  -7.99953e-05 |  0           |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Same-Budget Safe Configuration Search | transaction_cost_paid           | -6.29963e-06 |  -1.25993e-05 |  0           |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Same-Budget Safe Configuration Search | constraint_violation_severity   | -3.99977e-05 |  -7.99953e-05 |  0           |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Same-Budget Safe Configuration Search | optimizer_recovery_success_rate |  0           |   0           |  0           |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Same-Budget Safe Configuration Search | turnover_adjusted_net_return    | -0.00319493  |  -0.00638987  |  0           |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Random Legal Harness Patch            | cvar_95                         |  0.000318349 |   0           |  0.000636697 |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Random Legal Harness Patch            | drawdown_duration               | -1.71429     |  -3.42857     |  0           |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Random Legal Harness Patch            | turnover                        | -3.99977e-05 |  -7.99953e-05 |  0           |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Random Legal Harness Patch            | transaction_cost_paid           | -6.29963e-06 |  -1.25993e-05 |  0           |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Random Legal Harness Patch            | constraint_violation_severity   | -3.99977e-05 |  -7.99953e-05 |  0           |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Random Legal Harness Patch            | optimizer_recovery_success_rate |  0           |   0           |  0           |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Random Legal Harness Patch            | turnover_adjusted_net_return    | -0.00319493  |  -0.00638987  |  0           |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Risk Parity Fixed Portfolio           | cvar_95                         | -0.00486215  |  -0.00575224  | -0.00397207  |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Risk Parity Fixed Portfolio           | drawdown_duration               | -6.57143     | -18.4286      |  5.28571     |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Risk Parity Fixed Portfolio           | turnover                        |  0.0701638   |   0.0696614   |  0.0706603   |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Risk Parity Fixed Portfolio           | transaction_cost_paid           |  0.00590651  |   0.00447467  |  0.00736057  |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Risk Parity Fixed Portfolio           | constraint_violation_severity   | -0.000156809 |  -0.000221172 | -0.000106456 |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Risk Parity Fixed Portfolio           | optimizer_recovery_success_rate |  0           |   0           |  0           |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Risk Parity Fixed Portfolio           | turnover_adjusted_net_return    | -0.0287666   |  -0.0439096   | -0.0136237   |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Equal Weight ETF Portfolio            | cvar_95                         | -3.52398e-05 |  -0.000423325 |  0.000352711 |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Equal Weight ETF Portfolio            | drawdown_duration               | -6.57143     | -18.5714      |  5.42857     |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Equal Weight ETF Portfolio            | turnover                        |  0.0701638   |   0.0696674   |  0.0706412   |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Equal Weight ETF Portfolio            | transaction_cost_paid           |  0.00590651  |   0.00447412  |  0.00736057  |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Equal Weight ETF Portfolio            | constraint_violation_severity   | -0.000156809 |  -0.000224257 | -8.93598e-05 |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Equal Weight ETF Portfolio            | optimizer_recovery_success_rate |  0           |   0           |  0           |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Equal Weight ETF Portfolio            | turnover_adjusted_net_return    | -0.0321735   |  -0.0379908   | -0.0263855   |         7 |            5 |

## H1a-H5p Judgment

- H1a supported: True. Unconstrained portfolio harness search produced invalid candidates that are logged but not used in legal comparisons.
- H2 supported: True. Hard gates enforce policy-boundary and clean-panel w-star invariance for legal arms.
- H3p supported: True. This asks whether TASE improves at least two locked risk/implementation metrics versus same-budget safe configuration search without meaningful return sacrifice.
- H4p supported: True. This asks the same question versus random legal implementation patches.
- H5p supported: True. This checks whether portfolio construction gives legal harness patches non-zero bite.

## Interpretation

Raw return, annualized return, and Sharpe are secondary. The primary evidence is downside risk, drawdown duration, turnover and cost, constraint violation severity, optimizer recovery, exposure drift, and stress-scenario behavior. If TASE wins only by changing lambda, caps, alpha, objective weights, or rebalance frequency, it fails the task by definition.

## Recommendation

Continue only as a portfolio-construction safety diagnostic. Do not frame this as alpha discovery or live profitability.
