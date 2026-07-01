# Direction A B1 Report

## B1 Scope

B1 audits candidate data sources and validates the candidate precompute machinery on a small deterministic smoke panel. It does not run a full experiment, does not search workflow patches, does not call an LLM API, and does not make a TASE effectiveness claim.

## B0 Dependency Status

B0 outputs were read successfully: candidate library, operator spec, registry schema, matrix design, and B0 report.

## Data Source Audit Summary

| source_name                                    | source_type                      | url_or_path                                                                                                    | checked_at                | reachable                 | requires_auth   | license_status                                | license_risk    | coverage_start          | coverage_end      | is_true_pit   | is_approximate_pit   | survivorship_bias_risk   | delisting_handling                                        | corporate_action_handling               | price_source_needed   | download_size_estimate   | implementation_cost   |   reproducibility_score | recommended_role                                   | decision               | notes                                                                                          |
|:-----------------------------------------------|:---------------------------------|:---------------------------------------------------------------------------------------------------------------|:--------------------------|:--------------------------|:----------------|:----------------------------------------------|:----------------|:------------------------|:------------------|:--------------|:---------------------|:-------------------------|:----------------------------------------------------------|:----------------------------------------|:----------------------|:-------------------------|:----------------------|------------------------:|:---------------------------------------------------|:-----------------------|:-----------------------------------------------------------------------------------------------|
| Wikipedia S&P 500 changes table                | public_web_table                 | https://en.wikipedia.org/wiki/List_of_S%26P_500_companies#Selected_changes_to_the_list_of_S%26P_500_components | 2026-07-01T07:49:36+00:00 | not_network_checked_in_B1 | False           | requires_manual_review                        | medium          | partial_changes_history | 2024-12-31        | False         | True                 | medium                   | membership changes only; delisted prices still unresolved | requires external adjusted price source | True                  | low                      | medium                |                    0.62 | approximate_pit_main_candidate_after_audit         | NEEDS_USER_INPUT       | Feasible approximate PIT path, but not enough in B1 to call it fully solved or unbiased.       |
| Public historical S&P 500 constituent datasets | public_github_or_kaggle_metadata | dataset_specific_url_required_before_B2                                                                        | 2026-07-01T07:49:36+00:00 | not_network_checked_in_B1 | varies          | unknown_until_dataset_selected                | medium_high     | varies                  | varies            | False         | True                 | medium                   | dataset-specific audit required                           | dataset-specific audit required         | True                  | low_to_medium            | medium                |                    0.55 | approximate_pit_main_candidate_after_license_audit | NEEDS_USER_INPUT       | Could become B2 main candidate only after provenance and license review.                       |
| Nasdaq/Stooq/yfinance liquid US ticker pool    | public_price_api_or_csv          | public endpoints or local downloader; no large download in B1                                                  | 2026-07-01T07:49:36+00:00 | not_network_checked_in_B1 | False           | requires_manual_review                        | medium          | 2007-01-01              | 2024-12-31        | False         | False                | high                     | weak unless delisted tickers are explicitly added         | depends on adjusted price source        | False                 | medium                   | low_medium            |                    0.7  | liquid_us_universe_diagnostic                      | ACCEPT_DIAGNOSTIC_ONLY | Fallback diagnostic only; claims must be downgraded because it is not PIT.                     |
| Qlib public US data feasibility                | public_research_dataset_tooling  | https://github.com/microsoft/qlib                                                                              | 2026-07-01T07:49:36+00:00 | not_network_checked_in_B1 | False           | tool_license_review_required_dataset_separate | medium          | dataset_dependent       | dataset_dependent | False         | unknown_until_audit  | unknown_medium           | bundle construction audit required                        | bundle construction audit required      | False                 | medium_high              | medium_high           |                    0.5  | B2_feasibility_audit_only                          | NEEDS_USER_INPUT       | Potential tooling path; B1 does not download or certify PIT correctness.                       |
| Current S&P 500 constituents                   | current_constituent_list         | current public constituent pages                                                                               | 2026-07-01T07:49:36+00:00 | not_network_checked_in_B1 | False           | requires_manual_review                        | low_medium      | current_only            | current_only      | False         | False                | high                     | none                                                      | none                                    | True                  | low                      | low                   |                    0.35 | not_main_evidence                                  | REJECT                 | Cannot be marked true PIT or unbiased main evidence.                                           |
| ETF universe sanity tier                       | public_etf_prices                | existing TASE ETF public data path or deterministic smoke mock                                                 | 2026-07-01T07:49:36+00:00 | local_or_mock_only_in_B1  | False           | requires_manual_review_for_real_prices        | medium          | 2007-01-01              | 2024-12-31        | False         | False                | medium                   | not adequate for stock PIT claims                         | depends on adjusted ETF price source    | False                 | low_medium               | low                   |                    0.8  | sanity_universe_only                               | ACCEPT_SANITY_ONLY     | Valid for machinery sanity, not for final stock-universe evidence.                             |
| CRSP/Compustat                                 | paid_institutional_database      | institutional access only                                                                                      | 2026-07-01T07:49:36+00:00 | not_checked_paid_source   | True            | restricted_paid                               | high_restricted | broad_historical        | 2024-12-31        | True          | False                | low_if_correctly_used    | strong                                                    | strong                                  | False                 | medium_high              | high                  |                    0.3  | not_default_low_cost_path                          | REJECT                 | Scientifically strong but cannot be default public path due to access and license constraints. |

## Main Data Path Decision

Status: PASS_WITH_DIAGNOSTIC_FALLBACK

No public source is certified as true PIT in B1. Use liquid US diagnostic fallback only with downgraded claims; keep approximate PIT sources as B2 audit candidates.

## Candidate Precompute Smoke Setting

- Smoke uses deterministic mock prices, not market evidence.
- Assets: 30
- Candidates: 56
- Train/validation days: 522
- Locked-test days: 262

## Implemented Operator Families

breakout, cross_sectional_momentum, low_volatility, moving_average_crossover, short_term_reversal, volatility, volume_liquidity

## Generated Matrices

cost_adjusted_pnl_matrix, diagnostic_matrix, gross_return_matrix, net_return_matrix, position_matrix, signal_matrix, turnover_matrix

## Candidate Registry Summary

- Rows: 56
- All four hashes present: True
- Uses future data: False

## Hash Validation Summary

The registry stores parameter, signal, PnL, turnover, and cost-adjusted PnL hashes. Hashes use deterministic SHA-256 with configured float rounding.

## Locked-Test Separation Summary

Train/validation artifacts and locked-test artifacts are written to physically separate directories. Workflow diagnostics and registry paths use train/validation artifacts only. The locked-test access report marks locked reads as forbidden before final evaluation.

## Risks / Blockers

- Public approximate PIT data remains unaudited enough for final claims.
- The smoke uses deterministic mock prices, so it validates machinery only, not market evidence.
- Liquid US fallback downgrades claims to diagnostic only.
- No full TASE proposer or workflow search is implemented in B1.

## Decision

B1 status: PASS_WITH_DIAGNOSTIC_FALLBACK

Next stage recommendation: B2 data-source repair/audit before full precompute.
