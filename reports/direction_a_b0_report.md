# Direction A B0 Report

## Stage B0 Scope

B0 freezes the Direction A method specification, creates the isolated engineering scaffold, drafts the typed workflow patch schema, checks public data-source feasibility, designs the candidate library, and defines candidate matrix/hash/registry formats. B0 does not run a full experiment, does not call an LLM API, and does not make any result claim.

## Specs Found / Missing

- Found: 4 / 4
- Missing: none
- Spec status: PASS

## Frozen Method Constraints

- fixed candidate strategy library
- fixed operator library
- fixed parameter grid
- fixed candidate budget
- fixed transaction cost
- fixed locked-test window and final metric
- candidate signal/PnL/turnover/cost-PnL invariance by hash
- archive completeness and no hidden candidate drops
- locked-test inaccessible during B0 and workflow selection

## Typed Patch Schema Status

The B0 schema defines seven patch types with typed parameter models: ValidationSchedulePatch, PruningRulePatch, PenaltyUsagePatch, CriticLoopPatch, EnsembleRulePatch, ArchivePolicyPatch, and RetestRollbackPatch. Parameters are constrained by enums / pre-registered scalar choices, and nested free-form parameter dictionaries are rejected.

Forbidden fields: arbitrary_code, candidate_budget_increase, final_metric_after_validation, future_return, hidden_candidate_drop, locked_test_metric, locked_test_window, operator_library_extension, parameter_grid_extension, pnl_curve_override, python_code, raw_signal_override, transaction_cost_override

## Data Source Feasibility

| source_name                                    | source_type                      | url_or_path                                                                                                    | requires_auth   | estimated_coverage_start   | estimated_coverage_end   | is_point_in_time   | is_approximate_pit     | survivorship_bias_risk   | delisting_handling                                                            | data_license_risk      | download_size_risk   | implementation_cost   | recommended_role                 | notes                                                                                                   |
|:-----------------------------------------------|:---------------------------------|:---------------------------------------------------------------------------------------------------------------|:----------------|:---------------------------|:-------------------------|:-------------------|:-----------------------|:-------------------------|:------------------------------------------------------------------------------|:-----------------------|:---------------------|:----------------------|:---------------------------------|:--------------------------------------------------------------------------------------------------------|
| Wikipedia S&P 500 changes table                | public_web_table                 | https://en.wikipedia.org/wiki/List_of_S%26P_500_companies#Selected_changes_to_the_list_of_S%26P_500_components | False           | partial_historical_changes | 2024-12-31               | False              | True                   | medium                   | membership changes only; delisted price history still needs separate handling | medium_review_required | low                  | medium                | approximate_pit_candidate_source | Can reconstruct an approximate large-cap membership timeline but is not complete unbiased PIT evidence. |
| Public historical S&P 500 constituent datasets | public_github_or_kaggle_metadata | source_to_be_selected_in_B1; do not hard-depend in B0                                                          | varies          | varies_by_dataset          | varies_by_dataset        | False              | True                   | medium                   | must audit dataset-specific construction                                      | medium_high            | low_to_medium        | medium                | candidate_for_B1_source_audit    | B0 records feasibility only; B1 must choose and audit license/provenance before use.                    |
| Nasdaq/Stooq/yfinance liquid US ticker pool    | public_price_api_or_csv          | local downloader or public endpoints; no large download in B0                                                  | False           | 2007-01-01                 | 2024-12-31               | False              | False                  | high                     | weak unless explicit delisted tickers are added                               | medium_review_required | medium               | low_medium            | liquid_us_universe_diagnostic    | Useful fallback diagnostic only; current/liquid constituents cannot be called unbiased PIT.             |
| Qlib public US data feasibility                | public_research_dataset_tooling  | https://github.com/microsoft/qlib                                                                              | False           | dataset_dependent          | dataset_dependent        | False              | unknown_until_B1_audit | unknown_medium           | must audit Qlib bundle construction                                           | medium_review_required | medium_high          | medium_high           | B1_feasibility_audit_only        | Potential reproducible tooling path; B0 does not download or assert PIT correctness.                    |
| Current S&P 500 constituents                   | current_constituent_list         | current public constituent pages                                                                               | False           | current_only               | current_only             | False              | False                  | high                     | none                                                                          | low_medium             | low                  | low                   | not_main_evidence                | Must not be represented as PIT; at most a biased diagnostic universe.                                   |
| ETF universe sanity tier                       | public_etf_prices                | existing TASE ETF public data path                                                                             | False           | 2007-01-01                 | 2024-12-31               | False              | False                  | medium                   | ETF survivorship still possible; less suitable for stock PIT claims           | medium_review_required | low_medium           | low                   | sanity_universe_only             | Good for pipeline sanity, not for final stock-universe selection reliability claim.                     |
| CRSP/Compustat                                 | paid_institutional_database      | institutional access only                                                                                      | True            | broad_historical           | 2024-12-31               | True               | False                  | low_if_correctly_used    | strong                                                                        | high_restricted        | medium_high          | high                  | not_default_low_cost_path        | Scientifically strong but not the default for current low-cost public reproducibility goal.             |

Recommended path: use an approximate PIT public source only after B1 source audit; otherwise use `liquid_us_universe_diagnostic` as a diagnostic fallback and ETF universe only as sanity tier. Current constituents must not be described as PIT.

## Candidate Library Summary

- Candidate count estimate: 1008
- Candidate count status: PASS_WITHIN_TARGET
- Operator families: 15
- Uses future data by default: False

## Matrix / Hash / Registry Design

B1 should precompute signal, position, gross return, net return, turnover, cost-adjusted PnL, and diagnostic matrices. Large matrices should use Parquet for audit tables and NumPy memmap/Zarr for dense arrays, not giant CSV. Each candidate must store signal/PnL/turnover/cost-PnL hashes using deterministic SHA-256 after configured float rounding.

## Risks / Blockers

- PIT source is not fully solved in B0; public approximate PIT candidates need B1 audit.
- Public datasets may have survivorship-bias, delisting, or license risk.
- Candidate library is pre-registered design only; no candidate PnL has been computed.
- The four method specs are required source of truth; missing specs would block B1.
- Warnings: none

## Decision

B0 status: PASS

Next stage recommendation: enter B1 source audit and candidate precompute planning.
