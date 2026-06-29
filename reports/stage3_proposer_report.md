# T.A.S.E Stage 3 Diagnostic Proposer Report

## Purpose

Stage 2 supported H1, H2, and H4, but not H3: the constrained self-improvement group did not clearly beat the constrained fixed baseline. Stage 3 keeps the same synthetic task, four groups, locked-test protocol, and penalty weights, and only changes the TASE proposer to a diagnostic-guided rule system.

## Why H3 Failed In Stage 2

The Stage 2 TASE group accepted few legal patches and did not outperform the fixed constrained harness. That suggested the hard constraints were useful, but the incremental value of self-improvement was not yet demonstrated.

## Diagnostic-Guided Proposer

The proposer reads only validation diagnostics: risk violations, skip/leak counters, validation score, validation compliant score, current harness config, and prior rejection reasons. It proposes safe typed infrastructure changes such as stricter risk limits, fail-closed or retry control flow, timestamp-guarded data access, and verbose logging. It does not read locked-test scores or diagnostics.

## Four-Group Results

| arm                      |   validation_score_mean |   validation_score_std |   locked_test_score_mean |   locked_test_score_std |   validation_test_gap_mean |   validation_test_gap_std |   constraint_compliant_score_mean |   constraint_compliant_score_std |   leakage_violations_mean |   leakage_violations_std |   silent_skip_count_mean |   silent_skip_count_std |   risk_violations_mean |   risk_violations_std |   unsafe_accepted_patch_rate_mean |   unsafe_accepted_patch_rate_std |   accepted_patch_count_mean |   accepted_patch_count_std |   useful_patch_count_mean |   useful_patch_count_std |   rejected_patch_count_mean |   rejected_patch_count_std |   tase_accepted_patch_count_mean |   tase_useful_patch_count_mean |   tase_rejected_patch_count_mean |   tase_delta_vs_constrained_fixed_locked_test |   tase_delta_vs_constrained_fixed_compliant_score |   tase_delta_vs_random_legal_locked_test |   tase_delta_vs_random_legal_compliant_score | h3_supported   | h4_supported   |
|:-------------------------|------------------------:|-----------------------:|-------------------------:|------------------------:|---------------------------:|--------------------------:|----------------------------------:|---------------------------------:|--------------------------:|-------------------------:|-------------------------:|------------------------:|-----------------------:|----------------------:|----------------------------------:|---------------------------------:|----------------------------:|---------------------------:|--------------------------:|-------------------------:|----------------------------:|---------------------------:|---------------------------------:|-------------------------------:|---------------------------------:|----------------------------------------------:|--------------------------------------------------:|-----------------------------------------:|---------------------------------------------:|:---------------|:---------------|
| Generic Unconstrained    |                 12.795  |                1.4241  |                 -22.4303 |                 1.7425  |                   35.2253  |                   2.48135 |                          -47.5053 |                          1.97007 |                         2 |                        0 |                     55.4 |                 33.6942 |                  124.4 |              66.0856  |                                 1 |                                0 |                         2.8 |                    1.64317 |                       0   |                 0        |                         0   |                    0       |                                1 |                            0.8 |                                0 |                                     -0.819272 |                                         -0.764272 |                                  3.46533 |                                      3.51533 | False          | True           |
| Constrained Fixed        |                -31.8449 |                2.49523 |                 -21.8708 |                 1.32765 |                   -9.97409 |                   3.35586 |                          -22.7358 |                          1.31484 |                         0 |                        0 |                      0   |                  0      |                   30.6 |               4.15933 |                                 0 |                                0 |                         0   |                    0       |                       0   |                 0        |                         0   |                    0       |                                1 |                            0.8 |                                0 |                                     -0.819272 |                                         -0.764272 |                                  3.46533 |                                      3.51533 | False          | True           |
| Random Legal Patch       |                -35.6212 |                2.44351 |                 -26.1554 |                 2.74995 |                   -9.46579 |                   3.11976 |                          -27.0154 |                          2.71055 |                         0 |                        0 |                      0   |                  0      |                   28.8 |               4.20714 |                                 0 |                                0 |                        30   |                    0       |                       0   |                 0        |                        68.8 |                    4.65833 |                                1 |                            0.8 |                                0 |                                     -0.819272 |                                         -0.764272 |                                  3.46533 |                                      3.51533 | False          | True           |
| TASE Finance-Constrained |                -29.8875 |                3.39524 |                 -22.6901 |                 1.32426 |                   -7.19747 |                   4.59563 |                          -23.5001 |                          1.33679 |                         0 |                        0 |                      0   |                  0      |                   30.8 |               5.89067 |                                 0 |                                0 |                         1   |                    0       |                       0.8 |                 0.447214 |                         0   |                    0       |                                1 |                            0.8 |                                0 |                                     -0.819272 |                                         -0.764272 |                                  3.46533 |                                      3.51533 | False          | True           |

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
- TASE accepted patch count mean: 1.000
- TASE useful patch count mean: 0.800
- TASE minus constrained fixed locked-test score: -0.819
- TASE minus constrained fixed compliant score: -0.764
- TASE minus random legal locked-test score: 3.465
- TASE minus random legal compliant score: 3.515

## Whether To Enter Public-Data Toy Task

继续改选择规则：目前还没有证明自我改进超过只加硬约束。
