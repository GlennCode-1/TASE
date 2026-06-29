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

from src.sp500_data import load_or_download_sp500_data
from src.stock_experiment import run_sp500_short
from src.reporting import write_sp500_short_reports


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run T.A.S.E S&P 500 short-window diagnostic task.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--refresh-constituents", action="store_true")
    return parser.parse_args()


def _load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        config = yaml.safe_load(fh)
    if bool(config.get("allow_synthetic_fallback", False)):
        raise RuntimeError("sp500_short forbids synthetic fallback in configured runs")
    return config


def main() -> None:
    args = parse_args()
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = Path.cwd() / config_path
    config = _load_config(config_path)
    run_root = Path(os.environ.get("TASE_RUN_ROOT", ROOT))
    outputs_dir = run_root / "outputs"
    checkpoints_dir = outputs_dir / "checkpoints"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    suffix = "quick" if args.quick else "full"
    checkpoint_results = checkpoints_dir / f"sp500_short_{suffix}_results_by_split.csv"
    checkpoint_candidates = checkpoints_dir / f"sp500_short_{suffix}_candidate_log.csv"
    checkpoint_summary = checkpoints_dir / f"sp500_short_{suffix}_summary_metrics.csv"
    checkpoint_paired = checkpoints_dir / f"sp500_short_{suffix}_paired_bootstrap.csv"
    checkpoint_exclusion = checkpoints_dir / f"sp500_short_{suffix}_exclusion_log.csv"

    if args.resume and checkpoint_results.exists() and checkpoint_candidates.exists() and checkpoint_summary.exists():
        results = pd.read_csv(checkpoint_results)
        candidates = pd.read_csv(checkpoint_candidates)
        summary = pd.read_csv(checkpoint_summary)
        paired = pd.read_csv(checkpoint_paired) if checkpoint_paired.exists() else pd.DataFrame()
        exclusion = pd.read_csv(checkpoint_exclusion) if checkpoint_exclusion.exists() else pd.DataFrame()
        bundle = load_or_download_sp500_data(config, ROOT, quick=args.quick, refresh_constituents=args.refresh_constituents)
    else:
        bundle = load_or_download_sp500_data(config, ROOT, quick=args.quick, refresh_constituents=args.refresh_constituents)
        output = run_sp500_short(bundle, config, quick=args.quick)
        results = output.results_by_split
        candidates = output.candidate_log
        summary = output.summary
        paired = output.paired_bootstrap
        exclusion = output.exclusion_log
        results.to_csv(checkpoint_results, index=False)
        candidates.to_csv(checkpoint_candidates, index=False)
        summary.to_csv(checkpoint_summary, index=False)
        paired.to_csv(checkpoint_paired, index=False)
        exclusion.to_csv(checkpoint_exclusion, index=False)

    report_config = dict(config)
    report_config["run_mode"] = "quick smoke" if args.quick else "full"
    report_config["retained_assets"] = len(bundle.universe)
    report_config["effective_start_date"] = str(bundle.start_date.date())
    report_config["effective_end_date"] = str(bundle.end_date.date())
    if "retrieved_at" in bundle.constituents.columns and not bundle.constituents.empty:
        report_config["constituents_retrieved_at"] = str(bundle.constituents["retrieved_at"].iloc[0])
    results.to_csv(outputs_dir / "sp500_short_results_by_split.csv", index=False)
    candidates.to_csv(outputs_dir / "sp500_short_candidate_log.csv", index=False)
    summary.to_csv(outputs_dir / "sp500_short_summary_metrics.csv", index=False)
    paired.to_csv(outputs_dir / "sp500_short_paired_bootstrap.csv", index=False)
    bundle.missing_log.to_csv(outputs_dir / "sp500_short_missing_data_log.csv", index=False)
    exclusion.to_csv(outputs_dir / "sp500_short_exclusion_log.csv", index=False)
    technical_path, plain_path = write_sp500_short_reports(results, candidates, summary, paired, report_config, run_root / "reports")
    for path in [
        outputs_dir / "sp500_short_results_by_split.csv",
        outputs_dir / "sp500_short_candidate_log.csv",
        outputs_dir / "sp500_short_summary_metrics.csv",
        outputs_dir / "sp500_short_paired_bootstrap.csv",
        outputs_dir / "sp500_short_missing_data_log.csv",
        outputs_dir / "sp500_short_exclusion_log.csv",
        technical_path,
        plain_path,
    ]:
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
