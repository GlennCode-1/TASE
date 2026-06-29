# T.A.S.E Kill-Test Report

## Experiment Purpose

This kill-test asks whether generic, unconstrained harness evolution can look strong on a validation window while failing on a locked test window or accepting unsafe trading-process changes. It compares that behavior against a finance-constrained typed harness evolution setup where the base strategy is frozen and unsafe infrastructure changes are rejected.

## Synthetic Data Design

- Assets: 20
- Splits: train 600 days, validation 200 days, locked test 200 days
- Seeds: 5
- Injected traps: future-data leakage, silent skipping of difficult days, risk-gate bypass, and validation-only spurious signal.
- Locked test has more Regime B, higher volatility, more crash days, and the validation spurious signal reverses.

## Arm Definitions

- Generic Unconstrained: free harness patch sampling, weak inner selection, future fields/skipping/risk weakening/spurious validation features can be accepted.
- TASE Finance-Constrained: typed infrastructure-only patching, frozen strategy, timestamp guard, risk gate, patch validator, fixed outer evaluator, and fixed financial meta-fitness.

## Metrics

| arm                      |   validation_score_mean |   validation_score_std |   locked_test_score_mean |   locked_test_score_std |   validation_test_gap_mean |   validation_test_gap_std |   constraint_compliant_score_mean |   constraint_compliant_score_std |   leakage_violations_mean |   leakage_violations_std |   silent_skip_count_mean |   silent_skip_count_std |   risk_violations_mean |   risk_violations_std |   unsafe_accepted_patch_rate_mean |   unsafe_accepted_patch_rate_std |   accepted_patch_count_mean |   accepted_patch_count_std |   rejected_patch_count_mean |   rejected_patch_count_std |
|:-------------------------|------------------------:|-----------------------:|-------------------------:|------------------------:|---------------------------:|--------------------------:|----------------------------------:|---------------------------------:|--------------------------:|-------------------------:|-------------------------:|------------------------:|-----------------------:|----------------------:|----------------------------------:|---------------------------------:|----------------------------:|---------------------------:|----------------------------:|---------------------------:|
| Generic Unconstrained    |                 12.795  |                1.4241  |                 -22.4303 |                 1.7425  |                   35.2253  |                   2.48135 |                          -47.5053 |                          1.97007 |                         2 |                        0 |                     55.4 |                 33.6942 |                  124.4 |              66.0856  |                                 1 |                                0 |                         2.8 |                   1.64317  |                         0   |                    0       |
| TASE Finance-Constrained |                -29.8875 |                3.39524 |                 -22.6901 |                 1.32426 |                   -7.19747 |                   4.59563 |                          -23.5001 |                          1.33679 |                         0 |                        0 |                      0   |                  0      |                   30.8 |               5.89067 |                                 0 |                                0 |                         0.6 |                   0.894427 |                        58.8 |                    9.62808 |

## Result Interpretation

- Generic unconstrained validation score mean: 12.795
- Generic unconstrained locked-test score mean: -22.430
- Generic unconstrained gap mean: 35.225
- TASE constrained validation score mean: -29.888
- TASE constrained locked-test score mean: -22.690
- TASE constrained gap mean: -7.197
- Generic unsafe accepted patch rate mean: 1.000
- TASE unsafe accepted patch rate mean: 0.000

H1 supported: True

H2 supported: True

## Whether Divergence Appears

The divergence pattern is considered present when the unconstrained arm wins validation but loses stability or compliance on locked test. In this run, divergence appears: True.

## Next-Step Recommendation

继续做完整实验，但下一轮要加入更干净的对照组。

Recommended next controls:

1. Add a constrained-no-evolution baseline.
2. Add a random-legal-patch baseline.
3. Keep locked-test discipline unchanged and do not tune penalties after seeing locked-test outcomes.
