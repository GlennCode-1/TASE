# S&P 500 Short-Window Reinterpretation Note

The corrected accounting changes the interpretation from a raw-score comparison to a valid-only diagnostic comparison.

- Invalid fallback is disallowed: no-valid cells are recorded as `NO_VALID_CANDIDATE` with missing locked metrics.
- Invalid high-score candidates are evidence for H1a only, not legal locked performance.
- H1b is unsupported because legal unconstrained selections do not establish the validation-high locked-poor pattern.
- H2 is supported because finance hard gates reduce violations.
- H3 is not effectively testable in this run because TASE and Constrained Safe Search are identical, with paired CI [0,0].
- H4 is unsupported because TASE is directionally slightly negative versus Random Legal Patch and the economic size is small.
- H5 is partially supported: the cross-stage safety story is consistent, but the self-improving performance story is not established.

Research framing should emphasize a finance-constrained validation harness, invalid shortcut detection, and valid-only reporting. It should not claim improved stock-market P&L from TASE on this run.
