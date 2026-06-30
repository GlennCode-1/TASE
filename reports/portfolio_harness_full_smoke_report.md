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
- Seeds: 10
- Search budget: 100
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
| Fixed Safe Portfolio Harness                |              1 |
| Portfolio Strategy Tuning Baseline          |             12 |
| Random Legal Harness Patch                  |             12 |
| Same-Budget Safe Configuration Search       |             12 |
| TASE Typed Portfolio Harness Reconstruction |             12 |
| Unconstrained Portfolio Harness Search      |             12 |

## Hard Gate Negative Control Results

| arm                                         |   candidate_count |   gate_pass_rate |   clean_panel_w_star_pass_rate |   policy_frozen_pass_rate |   leakage_pass_rate |
|:--------------------------------------------|------------------:|-----------------:|-------------------------------:|--------------------------:|--------------------:|
| Fixed Safe Portfolio Harness                |                 1 |         1        |                       1        |                         1 |            1        |
| Same-Budget Safe Configuration Search       |                12 |         0.5      |                       0.5      |                         1 |            1        |
| Random Legal Harness Patch                  |                12 |         0.5      |                       0.5      |                         1 |            1        |
| TASE Typed Portfolio Harness Reconstruction |                12 |         0.583333 |                       0.583333 |                         1 |            1        |
| Unconstrained Portfolio Harness Search      |                12 |         0        |                       0        |                         0 |            0.583333 |
| Portfolio Strategy Tuning Baseline          |                12 |         0        |                       0        |                         0 |            1        |

Negative controls are represented by invalid candidate attempts that change policy/specification, use future returns, or alter clean-panel w-star. These must be rejected before legal comparison.

## Headline Risk / Harness Metrics

| arm                                         |   locked_cvar_95 |   locked_downside_deviation |   locked_sortino |   locked_calmar |   locked_max_drawdown |   locked_drawdown_duration |   realized_volatility |     turnover |   transaction_cost_paid |   turnover_adjusted_net_return |   constraint_violation_severity |   infeasible_optimization_events |   optimizer_recovery_success_rate |   failed_rebalance_retention_rate |   cash_ratio_due_to_infeasibility |   exposure_drift |   herfindahl_index |   diversification_ratio |   asset_class_cap_violation_severity |   high_vol_return |   normal_vol_return |   stress_recovery_return |   locked_cumulative_return |   locked_annualized_return |   locked_sharpe |   valid_selected_cells |   no_valid_candidate_cells |   true_candidate_count |   valid_candidate_count |
|:--------------------------------------------|-----------------:|----------------------------:|-----------------:|----------------:|----------------------:|---------------------------:|----------------------:|-------------:|------------------------:|-------------------------------:|--------------------------------:|---------------------------------:|----------------------------------:|----------------------------------:|----------------------------------:|-----------------:|-------------------:|------------------------:|-------------------------------------:|------------------:|--------------------:|-------------------------:|---------------------------:|---------------------------:|----------------:|-----------------------:|---------------------------:|-----------------------:|------------------------:|
| Fixed Safe Portfolio Harness                |       -0.0177916 |                    0.135578 |        -0.246431 |       0.0417082 |            -0.118983  |                    81.5714 |              0.133037 |   0.0780086  |             0.0067184   |                    -0.0361243  |                      0.00490704 |                                0 |                                 1 |                                 1 |                       0.0249321   |      0.0249321   |          0.0575435 |                 1.4252  |                                 0    |      -4.77975e-05 |        -0.000479847 |             -0.000833757 |               -0.0294059   |                -0.0472935  |      -0.33692   |                      7 |                          0 |                      1 |                       1 |
| Same-Budget Safe Configuration Search       |       -0.0185591 |                    0.140976 |        -0.131028 |       0.136142  |            -0.118365  |                    81.8571 |              0.141971 |   0.0781242  |             0.00673142  |                    -0.0311624  |                      0.00502263 |                                0 |                                 1 |                                 1 |                       0.0136764   |      0.0136764   |          0.0579726 |                 1.42458 |                                 0    |      -8.46996e-06 |        -0.00044981  |             -0.000784336 |               -0.024431    |                -0.0374795  |      -0.211977  |                      7 |                          0 |                     12 |                       6 |
| Random Legal Harness Patch                  |       -0.0185591 |                    0.140976 |        -0.131028 |       0.136142  |            -0.118365  |                    81.8571 |              0.141971 |   0.0781242  |             0.00673142  |                    -0.0311624  |                      0.00502263 |                                0 |                                 1 |                                 1 |                       0.0136764   |      0.0136764   |          0.0579726 |                 1.42458 |                                 0    |      -8.46996e-06 |        -0.00044981  |             -0.000784336 |               -0.024431    |                -0.0374795  |      -0.211977  |                      7 |                          0 |                     12 |                       6 |
| TASE Typed Portfolio Harness Reconstruction |       -0.0182145 |                    0.138112 |        -0.194369 |       0.121017  |            -0.120641  |                    80.1429 |              0.137253 |   0.0780802  |             0.00672448  |                    -0.0342353  |                      0.00497858 |                                0 |                                 1 |                                 1 |                       0.0210925   |      0.0210925   |          0.0568258 |                 1.42458 |                                 0    |      -4.86389e-05 |        -0.00046609  |             -0.000808229 |               -0.0275108   |                -0.0428795  |      -0.29354   |                      7 |                          0 |                     12 |                       7 |
| Unconstrained Portfolio Harness Search      |      nan         |                  nan        |       nan        |     nan         |           nan         |                   nan      |            nan        | nan          |           nan           |                   nan          |                    nan          |                              nan |                               nan |                               nan |                     nan           |    nan           |        nan         |               nan       |                               nan    |     nan           |       nan           |            nan           |              nan           |               nan          |     nan         |                      0 |                          7 |                     12 |                       0 |
| Portfolio Strategy Tuning Baseline          |       -0.0171751 |                    0.13235  |         0.222795 |       0.598831  |            -0.100268  |                    78.5714 |              0.13321  |   0.0198547  |             0.00184636  |                    -0.00125039 |                      0.00475945 |                                0 |                                 1 |                                 1 |                       0.0373182   |      0.0373182   |          0.0359196 |                 1.42452 |                                 0    |       7.85916e-05 |        -0.000191411 |             -0.000589617 |                0.000595962 |                 0.00958031 |       0.158562  |                      0 |                          0 |                     12 |                       0 |
| Equal Weight ETF Portfolio                  |       -0.0182516 |                    0.140336 |         0.255121 |       0.770836  |            -0.110002  |                    86.7143 |              0.144138 |   0.00794558 |             0.000821429 |                    -0.00221099 |                      0.00516463 |                                0 |                                 1 |                                 1 |                       0           |      0           |          0.025641  |                 1.42586 |                                 0    |       7.47865e-05 |        -0.000276065 |             -0.000564938 |               -0.00138956  |                 0.00869102 |       0.157167  |                      0 |                          0 |                      1 |                       0 |
| Risk Parity Fixed Portfolio                 |       -0.0133262 |                    0.102662 |         0.177737 |       0.745706  |            -0.0873353 |                    86.7143 |              0.105991 |   0.00794558 |             0.000821429 |                    -0.0056767  |                      0.00516463 |                                0 |                                 1 |                                 1 |                       1.11022e-16 |      1.11022e-16 |          0.0509619 |                 1.45166 |                                 0    |       5.01284e-05 |        -0.000272353 |             -0.000497372 |               -0.00485527  |                -0.00211495 |       0.0676293 |                      0 |                          0 |                      1 |                       0 |
| 60/40 Portfolio                             |       -0.0158573 |                    0.118473 |         0.269762 |       0.933283  |            -0.103616  |                    83.7143 |              0.124227 |   0.00794558 |             0.000821429 |                    -0.00820749 |                      0.695165   |                                0 |                                 1 |                                 1 |                       0           |      0           |          0.52      |                 1.24105 |                                 0.05 |      -2.14589e-05 |        -0.000360495 |             -0.000417121 |               -0.00738606  |                -0.00360321 |       0.14332   |                      0 |                          0 |                      1 |                       0 |

## Invalid High-Score Log

| arm                                    |   seed |   split_id | candidate_id                                | reason                                                                        |   validation_score |   locked_score_if_computed | why_not_selected   |
|:---------------------------------------|-------:|-----------:|:--------------------------------------------|:------------------------------------------------------------------------------|-------------------:|---------------------------:|:-------------------|
| Unconstrained Portfolio Harness Search |      0 |          6 | Unconstrained Portfolio Harness Search-0-2  | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED |           3.89902  |                 0.961563   | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          0 | Unconstrained Portfolio Harness Search-0-2  | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED |           3.35031  |                 0.650384   | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          5 | Unconstrained Portfolio Harness Search-0-2  | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED |           3.02599  |                 0.810707   | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          4 | Unconstrained Portfolio Harness Search-0-2  | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED |           2.82246  |                 1.22772    | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          1 | Unconstrained Portfolio Harness Search-0-2  | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED |           2.71882  |                 0.52945    | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          3 | Unconstrained Portfolio Harness Search-0-2  | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED |           2.3613   |                 1.45287    | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          2 | Unconstrained Portfolio Harness Search-0-2  | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED |           2.14445  |                 1.1036     | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          0 | Unconstrained Portfolio Harness Search-0-9  | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED |           0.734137 |                -0.00167668 | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          6 | Unconstrained Portfolio Harness Search-0-9  | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED |           0.574811 |                 0.210912   | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          1 | Unconstrained Portfolio Harness Search-0-9  | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED |           0.474138 |                -0.0537531  | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          0 | Unconstrained Portfolio Harness Search-0-5  | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED |           0.45204  |                -0.0364015  | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          1 | Unconstrained Portfolio Harness Search-0-5  | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED |           0.402328 |                -0.114466   | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          6 | Unconstrained Portfolio Harness Search-0-5  | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED |           0.388965 |                 0.120945   | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          5 | Unconstrained Portfolio Harness Search-0-9  | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED |           0.324217 |                 0.135342   | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          4 | Unconstrained Portfolio Harness Search-0-9  | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED |           0.22802  |                 0.300088   | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          6 | Unconstrained Portfolio Harness Search-0-4  | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED |           0.202692 |                 0.0653521  | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          0 | Unconstrained Portfolio Harness Search-0-11 | POLICY_SPECIFICATION_CHANGED;CLEAN_PANEL_W_STAR_CHANGED                       |           0.199084 |                -0.133547   | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          2 | Unconstrained Portfolio Harness Search-0-9  | POLICY_SPECIFICATION_CHANGED;FUTURE_RETURN_LEAKAGE;CLEAN_PANEL_W_STAR_CHANGED |           0.195408 |                 0.202845   | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          0 | Unconstrained Portfolio Harness Search-0-8  | POLICY_SPECIFICATION_CHANGED;CLEAN_PANEL_W_STAR_CHANGED;LOOSE_COST_ACCOUNTING |           0.180838 |                -0.134837   | FAILED_HARD_GATE   |
| Unconstrained Portfolio Harness Search |      0 |          0 | Unconstrained Portfolio Harness Search-0-1  | POLICY_SPECIFICATION_CHANGED;CLEAN_PANEL_W_STAR_CHANGED                       |           0.177648 |                -0.127774   | FAILED_HARD_GATE   |

## Paired Block Bootstrap

| comparison                                                                          | metric                          |    mean_diff |        ci_low |      ci_high |   n_pairs |   block_size |
|:------------------------------------------------------------------------------------|:--------------------------------|-------------:|--------------:|-------------:|----------:|-------------:|
| TASE Typed Portfolio Harness Reconstruction - Fixed Safe Portfolio Harness          | cvar_95                         | -0.000422975 |  -0.000739102 | -0.000106849 |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Fixed Safe Portfolio Harness          | drawdown_duration               | -1.42857     |  -3           |  0.142857    |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Fixed Safe Portfolio Harness          | turnover                        |  7.15467e-05 |   8.97259e-06 |  0.000134121 |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Fixed Safe Portfolio Harness          | transaction_cost_paid           |  6.08329e-06 |   4.27624e-07 |  1.1739e-05  |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Fixed Safe Portfolio Harness          | constraint_violation_severity   |  7.15467e-05 |   8.97259e-06 |  0.000134121 |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Fixed Safe Portfolio Harness          | optimizer_recovery_success_rate |  0           |   0           |  0           |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Fixed Safe Portfolio Harness          | turnover_adjusted_net_return    |  0.00188904  |  -0.000365972 |  0.00414406  |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Fixed Safe Portfolio Harness          | locked_cumulative_return        |  0.00189513  |  -0.000365009 |  0.00415526  |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Fixed Safe Portfolio Harness          | locked_sharpe                   |  0.0433795   |   0.0109865   |  0.0757724   |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Same-Budget Safe Configuration Search | cvar_95                         |  0.000344571 |   0           |  0.000689142 |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Same-Budget Safe Configuration Search | drawdown_duration               | -1.71429     |  -3.42857     |  0           |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Same-Budget Safe Configuration Search | turnover                        | -4.40506e-05 |  -8.81012e-05 |  0           |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Same-Budget Safe Configuration Search | transaction_cost_paid           | -6.93797e-06 |  -1.38759e-05 |  0           |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Same-Budget Safe Configuration Search | constraint_violation_severity   | -4.40506e-05 |  -8.81012e-05 |  0           |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Same-Budget Safe Configuration Search | optimizer_recovery_success_rate |  0           |   0           |  0           |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Same-Budget Safe Configuration Search | turnover_adjusted_net_return    | -0.00307288  |  -0.00614577  |  0           |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Same-Budget Safe Configuration Search | locked_cumulative_return        | -0.00307982  |  -0.00615964  |  0           |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Same-Budget Safe Configuration Search | locked_sharpe                   | -0.0815632   |  -0.163126    |  0           |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Random Legal Harness Patch            | cvar_95                         |  0.000344571 |   0           |  0.000689142 |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Random Legal Harness Patch            | drawdown_duration               | -1.71429     |  -3.42857     |  0           |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Random Legal Harness Patch            | turnover                        | -4.40506e-05 |  -8.81012e-05 |  0           |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Random Legal Harness Patch            | transaction_cost_paid           | -6.93797e-06 |  -1.38759e-05 |  0           |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Random Legal Harness Patch            | constraint_violation_severity   | -4.40506e-05 |  -8.81012e-05 |  0           |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Random Legal Harness Patch            | optimizer_recovery_success_rate |  0           |   0           |  0           |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Random Legal Harness Patch            | turnover_adjusted_net_return    | -0.00307288  |  -0.00614577  |  0           |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Random Legal Harness Patch            | locked_cumulative_return        | -0.00307982  |  -0.00615964  |  0           |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Random Legal Harness Patch            | locked_sharpe                   | -0.0815632   |  -0.163126    |  0           |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Risk Parity Fixed Portfolio           | cvar_95                         | -0.0048883   |  -0.00577402  | -0.00400258  |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Risk Parity Fixed Portfolio           | drawdown_duration               | -6.57143     | -18.4286      |  5.28571     |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Risk Parity Fixed Portfolio           | turnover                        |  0.0701346   |   0.0696329   |  0.0706363   |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Risk Parity Fixed Portfolio           | transaction_cost_paid           |  0.00590305  |   0.00447286  |  0.00733324  |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Risk Parity Fixed Portfolio           | constraint_violation_severity   | -0.000186043 |  -0.000259392 | -0.000112693 |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Risk Parity Fixed Portfolio           | optimizer_recovery_success_rate |  0           |   0           |  0           |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Risk Parity Fixed Portfolio           | turnover_adjusted_net_return    | -0.0285586   |  -0.0435737   | -0.0135435   |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Risk Parity Fixed Portfolio           | locked_cumulative_return        | -0.0226555   |  -0.0367375   | -0.00857358  |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Risk Parity Fixed Portfolio           | locked_sharpe                   | -0.36117     |  -0.434457    | -0.287883    |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Equal Weight ETF Portfolio            | cvar_95                         |  3.71209e-05 |  -0.000396486 |  0.000470728 |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Equal Weight ETF Portfolio            | drawdown_duration               | -6.57143     | -18.5714      |  5.42857     |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Equal Weight ETF Portfolio            | turnover                        |  0.0701346   |   0.0696329   |  0.0706363   |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Equal Weight ETF Portfolio            | transaction_cost_paid           |  0.00590305  |   0.00447286  |  0.00733324  |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Equal Weight ETF Portfolio            | constraint_violation_severity   | -0.000186043 |  -0.000259392 | -0.000106558 |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Equal Weight ETF Portfolio            | optimizer_recovery_success_rate |  0           |   0           |  0           |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Equal Weight ETF Portfolio            | turnover_adjusted_net_return    | -0.0320243   |  -0.0376187   | -0.0264299   |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Equal Weight ETF Portfolio            | locked_cumulative_return        | -0.0261212   |  -0.0311886   | -0.0210156   |         7 |            5 |
| TASE Typed Portfolio Harness Reconstruction - Equal Weight ETF Portfolio            | locked_sharpe                   | -0.450708    |  -0.538717    | -0.362698    |         7 |            5 |

## Return Preservation / Trade-Off Analysis

- TASE vs Same-Budget Safe Search risk improvements: drawdown_duration, turnover, transaction_cost_paid, constraint_violation_severity. Return preservation: False (worst return CI low -0.1631 vs threshold -0.0200).
- TASE vs Random Legal Patch risk improvements: drawdown_duration, turnover, transaction_cost_paid, constraint_violation_severity. Return preservation: False (worst return CI low -0.1631 vs threshold -0.0200).

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
- If this is a quick smoke or staged full run, it should not be described as final evidence.

## Recommendation

Continue only as a portfolio-construction safety diagnostic. Do not frame this as alpha discovery or live profitability.
