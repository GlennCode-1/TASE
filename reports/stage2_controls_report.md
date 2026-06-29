# T.A.S.E Stage 2 Controls Report

## Purpose

Stage 1 showed that unconstrained harness evolution can win validation while failing locked-test discipline. Stage 2 adds two controls to ask whether TASE's benefit comes from hard finance constraints alone or from typed self-improvement and validation-based selection.

## Four Groups

- Generic Unconstrained: free harness evolution with weak inner selection.
- Constrained Fixed: strong timestamp/risk/no-skip constraints, no harness evolution.
- Random Legal Patch: same legal patch space and validator as TASE, but random legal acceptance without validation-based selection.
- TASE Finance-Constrained: legal typed patches plus validation selection by fixed financial composite score.

## Metrics

| arm                      |   validation_score_mean |   validation_score_std |   locked_test_score_mean |   locked_test_score_std |   validation_test_gap_mean |   validation_test_gap_std |   constraint_compliant_score_mean |   constraint_compliant_score_std |   leakage_violations_mean |   leakage_violations_std |   silent_skip_count_mean |   silent_skip_count_std |   risk_violations_mean |   risk_violations_std |   unsafe_accepted_patch_rate_mean |   unsafe_accepted_patch_rate_std |   accepted_patch_count_mean |   accepted_patch_count_std |   rejected_patch_count_mean |   rejected_patch_count_std |
|:-------------------------|------------------------:|-----------------------:|-------------------------:|------------------------:|---------------------------:|--------------------------:|----------------------------------:|---------------------------------:|--------------------------:|-------------------------:|-------------------------:|------------------------:|-----------------------:|----------------------:|----------------------------------:|---------------------------------:|----------------------------:|---------------------------:|----------------------------:|---------------------------:|
| Generic Unconstrained    |                 12.795  |                1.4241  |                 -22.4303 |                 1.7425  |                   35.2253  |                   2.48135 |                          -47.5053 |                          1.97007 |                         2 |                        0 |                     55.4 |                 33.6942 |                  124.4 |              66.0856  |                                 1 |                                0 |                         2.8 |                   1.64317  |                         0   |                    0       |
| Constrained Fixed        |                -31.8449 |                2.49523 |                 -21.8708 |                 1.32765 |                   -9.97409 |                   3.35586 |                          -22.7358 |                          1.31484 |                         0 |                        0 |                      0   |                  0      |                   30.6 |               4.15933 |                                 0 |                                0 |                         0   |                   0        |                         0   |                    0       |
| Random Legal Patch       |                -35.6212 |                2.44351 |                 -26.1554 |                 2.74995 |                   -9.46579 |                   3.11976 |                          -27.0154 |                          2.71055 |                         0 |                        0 |                      0   |                  0      |                   28.8 |               4.20714 |                                 0 |                                0 |                        30   |                   0        |                        68.8 |                    4.65833 |
| TASE Finance-Constrained |                -29.8875 |                3.39524 |                 -22.6901 |                 1.32426 |                   -7.19747 |                   4.59563 |                          -23.5001 |                          1.33679 |                         0 |                        0 |                      0   |                  0      |                   30.8 |               5.89067 |                                 0 |                                0 |                         0.6 |                   0.894427 |                        58.8 |                    9.62808 |

## H1-H4 Judgment

- H1 supported: True
- H2 supported: True
- H3 supported: False
- H4 supported: True

## Key Comparisons

- Free validation mean: 12.795; locked-test mean: -22.430; gap: 35.225
- Constrained fixed locked-test mean: -21.871; compliant mean: -22.736
- Random legal locked-test mean: -26.155; compliant mean: -27.015
- TASE locked-test mean: -22.690; compliant mean: -23.500
- TASE minus constrained fixed compliant score: -0.764
- TASE minus random legal compliant score: 3.515
- TASE accepted legal patches mean: 0.600

## Consistency With Stage 1

The Stage 1 divergence check remains consistent when the unconstrained group has higher validation score, a larger validation-test gap, and more violations than the finance-constrained group. In this run, consistency holds: True.

## Next Step

改 proposer：当前主要证明约束有用，自我改进贡献还不稳。
