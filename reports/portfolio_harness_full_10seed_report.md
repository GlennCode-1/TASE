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
- Run mode: full_10seed
- Seeds: 10
- Search budget: 100
- Split count: 7
- Paired observations: 70
- Bootstrap iterations: 2000

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
| Fixed Safe Portfolio Harness                |             10 |
| Portfolio Strategy Tuning Baseline          |            960 |
| Random Legal Harness Patch                  |           1000 |
| Same-Budget Safe Configuration Search       |           1000 |
| TASE Typed Portfolio Harness Reconstruction |           1000 |
| Unconstrained Portfolio Harness Search      |           1000 |

## Hard Gate Negative Control Results

| arm                                         |   candidate_count |   gate_pass_rate |   clean_panel_w_star_pass_rate |   policy_frozen_pass_rate |   leakage_pass_rate |
|:--------------------------------------------|------------------:|-----------------:|-------------------------------:|--------------------------:|--------------------:|
| Fixed Safe Portfolio Harness                |                10 |                1 |                              1 |                         1 |               1     |
| Same-Budget Safe Configuration Search       |              1000 |                1 |                              1 |                         1 |               1     |
| Random Legal Harness Patch                  |              1000 |                1 |                              1 |                         1 |               1     |
| TASE Typed Portfolio Harness Reconstruction |              1000 |                1 |                              1 |                         1 |               1     |
| Unconstrained Portfolio Harness Search      |              1000 |                0 |                              0 |                         0 |               0.765 |
| Portfolio Strategy Tuning Baseline          |               960 |                0 |                              0 |                         0 |               1     |

Negative controls are represented by invalid candidate attempts that change policy/specification, use future returns, or alter clean-panel w-star. These must be rejected before legal comparison.

## Headline Risk / Harness Metrics

| arm                                         |   locked_cvar_95 |   locked_downside_deviation |   locked_sortino |   locked_calmar |   locked_max_drawdown |   locked_drawdown_duration |   realized_volatility |     turnover |   transaction_cost_paid |   turnover_adjusted_net_return |   constraint_violation_severity |   infeasible_optimization_events |   optimizer_recovery_success_rate |   failed_rebalance_retention_rate |   cash_ratio_due_to_infeasibility |   exposure_drift |   herfindahl_index |   diversification_ratio |   asset_class_cap_violation_severity |   high_vol_return |   normal_vol_return |   stress_recovery_return |   locked_cumulative_return |   locked_annualized_return |   locked_sharpe |   valid_selected_cells |   no_valid_candidate_cells |   true_candidate_count |   valid_candidate_count |
|:--------------------------------------------|-----------------:|----------------------------:|-----------------:|----------------:|----------------------:|---------------------------:|----------------------:|-------------:|------------------------:|-------------------------------:|--------------------------------:|---------------------------------:|----------------------------------:|----------------------------------:|----------------------------------:|-----------------:|-------------------:|------------------------:|-------------------------------------:|------------------:|--------------------:|-------------------------:|---------------------------:|---------------------------:|----------------:|-----------------------:|---------------------------:|-----------------------:|------------------------:|
| Fixed Safe Portfolio Harness                |       -0.0180486 |                   0.124771  |        0.359611  |        0.245911 |             -0.178768 |                    305.857 |             0.112798  |   0.0681034  |             0.0418952   |                    0.0769338   |                     0.00083802  |                          0       |                          1        |                                 1 |                       0.021737    |      0.021737    |          0.0582366 |                1.46915  |                                 0    |       0.000565674 |         0.000145122 |              0.000152265 |                  0.118829  |                 0.0405092  |       0.404346  |                     70 |                          0 |                     10 |                      10 |
| Same-Budget Safe Configuration Search       |       -0.0174209 |                   0.121731  |        0.120287  |        0.188169 |             -0.202145 |                    335.286 |             0.111777  |   0.0498581  |             0.0301759   |                    0.07954     |                     0.000653718 |                          5.14286 |                          0.994228 |                                 1 |                       0.247603    |      0.247603    |          0.0515734 |                1.26146  |                                 0    |       0.00153575  |         9.99539e-05 |              9.62078e-05 |                  0.109716  |                 0.0347629  |       0.14646   |                     70 |                          0 |                   1000 |                    1000 |
| Random Legal Harness Patch                  |       -0.0110864 |                   0.0798067 |       -0.0553454 |        0.039941 |             -0.15044  |                    385.786 |             0.0713344 |   0.020035   |             0.0121587   |                   -0.000607739 |                     0.000278846 |                         18       |                          0.979798 |                                 1 |                       0.621684    |      0.621684    |          0.0333224 |                0.945079 |                                 0    |       0.000782958 |         2.0285e-05  |              3.68094e-05 |                  0.011551  |                 0.00241569 |      -0.0604839 |                     70 |                          0 |                   1000 |                    1000 |
| TASE Typed Portfolio Harness Reconstruction |       -0.0160487 |                   0.112397  |        0.107419  |        0.170036 |             -0.1954   |                    310     |             0.102924  |   0.0449512  |             0.0259026   |                    0.0645066   |                     0.000632118 |                         15.4286  |                          0.982684 |                                 1 |                       0.257098    |      0.257098    |          0.0502364 |                1.30609  |                                 0    |       0.00139917  |         7.79132e-05 |              6.47185e-05 |                  0.0904092 |                 0.0283805  |       0.134281  |                     70 |                          0 |                   1000 |                    1000 |
| Unconstrained Portfolio Harness Search      |      nan         |                 nan         |      nan         |      nan        |            nan        |                    nan     |           nan         | nan          |           nan           |                  nan           |                   nan           |                        nan       |                        nan        |                               nan |                     nan           |    nan           |        nan         |              nan        |                               nan    |     nan           |       nan           |            nan           |                nan         |               nan          |     nan         |                      0 |                         70 |                   1000 |                       0 |
| Portfolio Strategy Tuning Baseline          |       -0.0188208 |                   0.13284   |        0.529944  |        0.402594 |             -0.181934 |                    239.143 |             0.121074  |   0.0281138  |             0.0176754   |                    0.173024    |                     0.000879722 |                          0       |                          1        |                                 1 |                       0.00368679  |      0.00368679  |          0.0459067 |                1.39502  |                                 0    |       0.000722474 |         0.000226525 |              0.000257782 |                  0.190699  |                 0.0638143  |       0.583619  |                      0 |                          0 |                    960 |                       0 |
| Equal Weight ETF Portfolio                  |       -0.0195799 |                   0.138354  |        0.675048  |        0.488178 |             -0.189206 |                    222.714 |             0.127516  |   0.00143208 |             0.000607143 |                    0.246576    |                     0.000930851 |                          0       |                          1        |                                 1 |                       0           |      0           |          0.025641  |                1.42317  |                                 0    |       0.00102356  |         0.000307277 |              0.000323131 |                  0.247184  |                 0.0825322  |       0.728794  |                      0 |                          0 |                      1 |                       0 |
| Risk Parity Fixed Portfolio                 |       -0.0118047 |                   0.0842291 |        0.769349  |        0.582742 |             -0.117711 |                    221.857 |             0.0775714 |   0.00143208 |             0.000607143 |                    0.171069    |                     0.0553396   |                          0       |                          1        |                                 1 |                       2.22045e-16 |      2.22045e-16 |          0.0761838 |                1.54635  |                                 0    |       0.000646215 |         0.000208001 |              0.000210301 |                  0.171676  |                 0.0585504  |       0.829851  |                      0 |                          0 |                      1 |                       0 |
| 60/40 Portfolio                             |       -0.0148603 |                   0.102671  |        0.934054  |        0.861147 |             -0.129369 |                    177.143 |             0.0964534 |   0.00143208 |             0.000607143 |                    0.260198    |                     0.690931    |                          0       |                          1        |                                 1 |                       0           |      0           |          0.52      |                1.30597  |                                 0.05 |       0.000764531 |         0.000313205 |              0.000301391 |                  0.260805  |                 0.0867937  |       0.991676  |                      0 |                          0 |                      1 |                       0 |

## Invalid High-Score Log

| arm                                    |   seed |   split_id | candidate_id                                | reason                                                                                              |   validation_score |   locked_score_if_computed | why_not_selected   |
|:---------------------------------------|-------:|-----------:|:--------------------------------------------|:----------------------------------------------------------------------------------------------------|-------------------:|---------------------------:|:-------------------|
| Unconstrained Portfolio Harness Search |      3 |          2 | Unconstrained Portfolio Harness Search-3-34 | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED;LOOSE_COST_ACCOUNTING |                6.5 |                        nan | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      9 |          2 | Unconstrained Portfolio Harness Search-9-98 | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED;LOOSE_COST_ACCOUNTING |                6.5 |                        nan | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      2 |          0 | Unconstrained Portfolio Harness Search-2-96 | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED;LOOSE_COST_ACCOUNTING |                6.5 |                        nan | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      1 |          0 | Unconstrained Portfolio Harness Search-1-44 | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED;LOOSE_COST_ACCOUNTING |                6.5 |                        nan | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      2 |          6 | Unconstrained Portfolio Harness Search-2-67 | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED;LOOSE_COST_ACCOUNTING |                6.5 |                        nan | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      4 |          4 | Unconstrained Portfolio Harness Search-4-42 | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED;LOOSE_COST_ACCOUNTING |                6.5 |                        nan | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      2 |          0 | Unconstrained Portfolio Harness Search-2-97 | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED;LOOSE_COST_ACCOUNTING |                6.5 |                        nan | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      3 |          4 | Unconstrained Portfolio Harness Search-3-70 | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED;LOOSE_COST_ACCOUNTING |                6.5 |                        nan | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      9 |          2 | Unconstrained Portfolio Harness Search-9-87 | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED;LOOSE_COST_ACCOUNTING |                6.5 |                        nan | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      5 |          4 | Unconstrained Portfolio Harness Search-5-43 | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED;LOOSE_COST_ACCOUNTING |                6.5 |                        nan | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      3 |          4 | Unconstrained Portfolio Harness Search-3-63 | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED;LOOSE_COST_ACCOUNTING |                6.5 |                        nan | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      1 |          0 | Unconstrained Portfolio Harness Search-1-31 | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED;LOOSE_COST_ACCOUNTING |                6.5 |                        nan | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      2 |          6 | Unconstrained Portfolio Harness Search-2-79 | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED;LOOSE_COST_ACCOUNTING |                6.5 |                        nan | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      4 |          4 | Unconstrained Portfolio Harness Search-4-50 | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED;LOOSE_COST_ACCOUNTING |                6.5 |                        nan | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      9 |          2 | Unconstrained Portfolio Harness Search-9-75 | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED;LOOSE_COST_ACCOUNTING |                6.5 |                        nan | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      7 |          2 | Unconstrained Portfolio Harness Search-7-31 | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED;LOOSE_COST_ACCOUNTING |                6.5 |                        nan | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      2 |          6 | Unconstrained Portfolio Harness Search-2-90 | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED;LOOSE_COST_ACCOUNTING |                6.5 |                        nan | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      8 |          3 | Unconstrained Portfolio Harness Search-8-36 | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED;LOOSE_COST_ACCOUNTING |                6.5 |                        nan | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      9 |          2 | Unconstrained Portfolio Harness Search-9-64 | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED;LOOSE_COST_ACCOUNTING |                6.5 |                        nan | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      1 |          0 | Unconstrained Portfolio Harness Search-1-46 | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED;LOOSE_COST_ACCOUNTING |                6.5 |                        nan | FAILED_HARD_GATE   |

## Paired Block Bootstrap

| comparison                                                                          | metric                          |     mean_diff |         ci_low |       ci_high |   n_pairs |   block_size |
|:------------------------------------------------------------------------------------|:--------------------------------|--------------:|---------------:|--------------:|----------:|-------------:|
| TASE Typed Portfolio Harness Reconstruction - Fixed Safe Portfolio Harness          | cvar_95                         |   0.00199994  |    0.00123877  |   0.00276924  |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Fixed Safe Portfolio Harness          | drawdown_duration               |   4.14286     |  -12.4004      |  20.3604      |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Fixed Safe Portfolio Harness          | turnover                        |  -0.0231522   |   -0.0275586   |  -0.0183469   |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Fixed Safe Portfolio Harness          | transaction_cost_paid           |  -0.0159926   |   -0.0188141   |  -0.0130814   |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Fixed Safe Portfolio Harness          | constraint_violation_severity   |  -0.000205902 |   -0.000254934 |  -0.000149217 |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Fixed Safe Portfolio Harness          | optimizer_recovery_success_rate |  -0.017316    |   -0.0196248   |  -0.01443     |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Fixed Safe Portfolio Harness          | turnover_adjusted_net_return    |  -0.0124272   |   -0.0277756   |   0.00223284  |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Fixed Safe Portfolio Harness          | locked_cumulative_return        |  -0.0284198   |   -0.0464923   |  -0.00934103  |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Fixed Safe Portfolio Harness          | locked_sharpe                   |  -0.270065    |   -0.355218    |  -0.179878    |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Same-Budget Safe Configuration Search | cvar_95                         |   0.00137223  |    0.00105983  |   0.00165344  |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Same-Budget Safe Configuration Search | drawdown_duration               | -25.2857      |  -32.2725      | -17.9571      |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Same-Budget Safe Configuration Search | turnover                        |  -0.00490694  |   -0.00614895  |  -0.00346521  |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Same-Budget Safe Configuration Search | transaction_cost_paid           |  -0.00427324  |   -0.00535445  |  -0.00301697  |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Same-Budget Safe Configuration Search | constraint_violation_severity   |  -2.16004e-05 |   -2.81964e-05 |  -1.4968e-05  |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Same-Budget Safe Configuration Search | optimizer_recovery_success_rate |  -0.011544    |   -0.01443     |  -0.00808081  |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Same-Budget Safe Configuration Search | turnover_adjusted_net_return    |  -0.0150334   |   -0.0176695   |  -0.0122405   |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Same-Budget Safe Configuration Search | locked_cumulative_return        |  -0.0193067   |   -0.022876    |  -0.0151878   |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Same-Budget Safe Configuration Search | locked_sharpe                   |  -0.0121786   |   -0.0151379   |  -0.00905116  |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Random Legal Harness Patch            | cvar_95                         |  -0.00496229  |   -0.00782701  |  -0.00213318  |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Random Legal Harness Patch            | drawdown_duration               | -75.7857      | -136.763       | -14.2         |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Random Legal Harness Patch            | turnover                        |   0.0249162   |    0.0105592   |   0.0391746   |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Random Legal Harness Patch            | transaction_cost_paid           |   0.0137439   |    0.00512243  |   0.0226619   |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Random Legal Harness Patch            | constraint_violation_severity   |   0.000353272 |    0.000123036 |   0.000561195 |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Random Legal Harness Patch            | optimizer_recovery_success_rate |   0.002886    |   -0.00634921  |   0.011544    |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Random Legal Harness Patch            | turnover_adjusted_net_return    |   0.0651143   |    0.0263659   |   0.104299    |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Random Legal Harness Patch            | locked_cumulative_return        |   0.0788583   |    0.0316649   |   0.122998    |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Random Legal Harness Patch            | locked_sharpe                   |   0.194765    |    0.0136323   |   0.373988    |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Risk Parity Fixed Portfolio           | cvar_95                         |  -0.00424394  |   -0.00486586  |  -0.00362645  |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Risk Parity Fixed Portfolio           | drawdown_duration               |  88.1429      |   62.2286      | 111.976       |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Risk Parity Fixed Portfolio           | turnover                        |   0.0435191   |    0.0385298   |   0.0487594   |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Risk Parity Fixed Portfolio           | transaction_cost_paid           |   0.0252955   |    0.0220021   |   0.0286166   |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Risk Parity Fixed Portfolio           | constraint_violation_severity   |  -0.0547075   |   -0.0547741   |  -0.0546351   |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Risk Parity Fixed Portfolio           | optimizer_recovery_success_rate |  -0.017316    |   -0.020202    |  -0.01443     |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Risk Parity Fixed Portfolio           | turnover_adjusted_net_return    |  -0.106562    |   -0.126251    |  -0.0849008   |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Risk Parity Fixed Portfolio           | locked_cumulative_return        |  -0.0812668   |   -0.104721    |  -0.0569268   |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Risk Parity Fixed Portfolio           | locked_sharpe                   |  -0.69557     |   -0.814782    |  -0.578155    |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Equal Weight ETF Portfolio            | cvar_95                         |   0.0035312   |    0.00321864  |   0.00379893  |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Equal Weight ETF Portfolio            | drawdown_duration               |  87.2857      |   63.0232      | 110.19        |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Equal Weight ETF Portfolio            | turnover                        |   0.0435191   |    0.0385731   |   0.0486337   |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Equal Weight ETF Portfolio            | transaction_cost_paid           |   0.0252955   |    0.022103    |   0.0286423   |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Equal Weight ETF Portfolio            | constraint_violation_severity   |  -0.000298734 |   -0.000365433 |  -0.000225784 |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Equal Weight ETF Portfolio            | optimizer_recovery_success_rate |  -0.017316    |   -0.020202    |  -0.01443     |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Equal Weight ETF Portfolio            | turnover_adjusted_net_return    |  -0.18207     |   -0.201728    |  -0.162499    |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Equal Weight ETF Portfolio            | locked_cumulative_return        |  -0.156774    |   -0.178928    |  -0.133086    |        70 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Equal Weight ETF Portfolio            | locked_sharpe                   |  -0.594513    |   -0.709497    |  -0.477077    |        70 |            5 |

## Return Preservation / Trade-Off Analysis

- TASE vs Same-Budget Safe Search risk improvements: cvar_95, drawdown_duration, turnover, transaction_cost_paid, constraint_violation_severity. Return preservation: False (worst return CI low -0.0229 vs threshold -0.0200).
- TASE vs Random Legal Patch risk improvements: drawdown_duration. Return preservation: True (worst return CI low 0.0136 vs threshold -0.0200).

## Comparison With Partial Full

The 10-seed full run agrees with the prior partial_full headline: H1a/H2/H5p supported, H3p/H4p not supported.

## H1a-H5p Judgment

- H1a supported: True. Unconstrained portfolio harness search produced invalid candidates that are logged but not used in legal comparisons.
- H2 supported: True. Hard gates enforce policy-boundary and clean-panel w-star invariance for legal arms.
- H3p supported: False. This asks whether TASE improves at least two locked risk/implementation metrics versus same-budget safe configuration search without meaningful return sacrifice.
- H4p supported: False. This asks the same question versus random legal implementation patches.
- H5p supported: True. This checks whether portfolio construction gives legal harness patches non-zero bite.

## Interpretation

Raw return, annualized return, and Sharpe are secondary. The primary evidence is downside risk, drawdown duration, turnover and cost, constraint violation severity, optimizer recovery, exposure drift, and stress-scenario behavior. If TASE wins only by changing lambda, caps, alpha, objective weights, or rebalance frequency, it fails the task by definition.

## Limitations

- ETF universe only; this is not a live trading result.
- Alpha, risk appetite, constraints, objective weights, and rebalance frequency are fixed by design.
- Stress scenarios are pre-registered but still controlled diagnostics, not a full institutional portfolio system.
- Strategy/policy tuning baseline is not a legal harness comparison.
- This report may be described as final full evidence only when Run mode is full_10seed with Seeds = 10 and Search budget = 100.

## Recommendation

Continue only as a portfolio-construction safety diagnostic. Do not frame this as alpha discovery or live profitability.
