from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.public_data import load_or_download_public_data
from src.portfolio_experiment import run_portfolio_harness
from src.reporting import write_portfolio_harness_reports


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run T.A.S.E portfolio harness diagnostic.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--output-prefix", default="portfolio_harness")
    return parser.parse_args()


def _load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def main() -> None:
    args = parse_args()
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = Path.cwd() / config_path
    config = _load_config(config_path)
    if bool(config.get("allow_synthetic_fallback", False)) and not args.quick:
        raise RuntimeError("portfolio harness full run forbids synthetic fallback")
    run_root = Path(os.environ.get("TASE_RUN_ROOT", ROOT))
    outputs_dir = run_root / "outputs"
    checkpoints_dir = outputs_dir / "checkpoints"
    reports_dir = run_root / "reports"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    suffix = "quick" if args.quick else "full"
    prefix = str(args.output_prefix)
    checkpoint_prefix = f"{prefix}_{suffix}"
    paths = {
        "results": checkpoints_dir / f"{checkpoint_prefix}_results_by_split.csv",
        "candidates": checkpoints_dir / f"{checkpoint_prefix}_candidate_log.csv",
        "summary": checkpoints_dir / f"{checkpoint_prefix}_summary_metrics.csv",
        "invalid": checkpoints_dir / f"{checkpoint_prefix}_invalid_high_score_log.csv",
        "paired": checkpoints_dir / f"{checkpoint_prefix}_paired_bootstrap.csv",
    }
    can_resume = args.resume and all(path.exists() for path in paths.values())
    bundle = load_or_download_public_data(config, ROOT, quick=args.quick)
    if can_resume:
        results = pd.read_csv(paths["results"])
        candidates = pd.read_csv(paths["candidates"])
        summary = pd.read_csv(paths["summary"])
        invalid = pd.read_csv(paths["invalid"])
        paired = pd.read_csv(paths["paired"])
    else:
        output = run_portfolio_harness(bundle, config, quick=args.quick)
        results = output.results_by_split
        candidates = output.candidate_log
        summary = output.summary
        invalid = output.invalid_high_score_log
        paired = output.paired_bootstrap
        results.to_csv(paths["results"], index=False)
        candidates.to_csv(paths["candidates"], index=False)
        summary.to_csv(paths["summary"], index=False)
        invalid.to_csv(paths["invalid"], index=False)
        paired.to_csv(paths["paired"], index=False)
    report_config = dict(config)
    report_config["run_mode"] = "quick smoke" if args.quick else str(config.get("mode", "full"))
    report_config["retained_assets"] = len(bundle.universe)
    report_config["effective_start_date"] = str(bundle.start_date.date())
    report_config["effective_end_date"] = str(bundle.end_date.date())
    results_path = outputs_dir / f"{prefix}_results_by_split.csv"
    candidates_path = outputs_dir / f"{prefix}_candidate_log.csv"
    summary_path = outputs_dir / f"{prefix}_summary_metrics.csv"
    invalid_path = outputs_dir / f"{prefix}_invalid_high_score_log.csv"
    paired_path = outputs_dir / f"{prefix}_paired_bootstrap.csv"
    results.to_csv(results_path, index=False)
    candidates.to_csv(candidates_path, index=False)
    summary.to_csv(summary_path, index=False)
    invalid.to_csv(invalid_path, index=False)
    paired.to_csv(paired_path, index=False)
    technical_path, plain_path = write_portfolio_harness_reports(
        results, candidates, summary, invalid, paired, report_config, reports_dir, output_prefix=prefix
    )
    for path in [
        results_path,
        candidates_path,
        summary_path,
        invalid_path,
        paired_path,
        technical_path,
        plain_path,
    ]:
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
