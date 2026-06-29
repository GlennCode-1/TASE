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
