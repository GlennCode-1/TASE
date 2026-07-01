# Direction A B0 Candidate Matrix Design

B0 does not generate full matrices. B1 should precompute candidate-level artifacts once and treat them as frozen inputs for every workflow arm.

## Required Matrices

- `signal_matrix`: candidate x date x asset signal values, rounded before hashing.
- `position_matrix`: candidate x date x asset positions under the frozen signal-to-position rule.
- `gross_return_matrix`: candidate x date gross PnL before costs.
- `net_return_matrix`: candidate x date net PnL under the fixed transaction cost assumption.
- `turnover_matrix`: candidate x date turnover.
- `cost_adjusted_pnl_matrix`: candidate x date cost-adjusted PnL curve used for invariant hashes.
- `diagnostic_matrix`: validation-only diagnostics such as PBO proxy, degradation proxy, turnover, drawdown, family label, and stability.

## Storage Format

- Use Parquet for long-form audit tables and candidate metadata.
- Use NumPy memmap or Zarr for large dense candidate x time matrices.
- Store metadata as JSON/YAML next to each shard.
- Do not store giant matrix CSV files in Git.

## Hashing Contract

For each candidate, B1 must store:

- `candidate_signal_hash`
- `candidate_pnl_hash`
- `candidate_turnover_hash`
- `candidate_cost_pnl_hash`

Hashing must round floats to the configured decimal count, serialize in deterministic order, and use SHA-256. Any workflow patch that changes these hashes is invalid because it changed the candidate rather than the workflow.

## Locked-Test Isolation

B0 and B1 matrix precompute may create locked-test candidate artifacts only as physically separated, read-final files. Workflow selection code must not read locked-test metrics, and registry metadata must mark locked paths as inaccessible before final evaluation.
