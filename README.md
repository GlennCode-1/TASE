# T.A.S.E Kill-Test

This is a 1-2 day synthetic kill-test for **T.A.S.E — Trade Agent Self-Evolve**.

It does not call an LLM, connect to trading APIs, or claim profitability. The goal is only to test one mechanism:

> Does unconstrained trading-harness evolution overfit or exploit validation, and does finance-constrained typed harness evolution reduce that failure mode?

## Run

```bash
pip install -r requirements.txt
pytest -q
python scripts/run_killtest.py --config configs/killtest.yaml
```

Smoke test:

```bash
python scripts/run_killtest.py --config configs/killtest.yaml --n-seeds 1 --patch-budget 5
```

## Outputs

- `outputs/results_by_seed.csv`
- `outputs/patch_log.csv`
- `outputs/summary_metrics.csv`
- `reports/killtest_report.md`
- `reports/plain_chinese_summary.md`

## Public ETF Toy Task

The public-data toy task is a small robustness check, not a profitability claim. It compares equal-budget harness searches on a fixed ETF universe and headlines PBO, deflated Sharpe, validation-to-OOS degradation, leakage audits, and pi-invariance audits.

```bash
python scripts/run_public_toy.py --config configs/public_toy.yaml --quick
python scripts/run_public_toy.py --config configs/public_toy.yaml
```

Outputs:

- `outputs/public_toy_results_by_split.csv`
- `outputs/public_toy_candidate_log.csv`
- `outputs/public_toy_summary_metrics.csv`
- `outputs/public_toy_missing_data_log.csv`
- `reports/public_toy_report.md`
- `reports/plain_chinese_summary_public_toy.md`
