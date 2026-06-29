from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.public_data import load_or_download_public_data
from src.public_experiment import run_public_toy
from src.reporting import write_public_full_reports


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run T.A.S.E public ETF full experiment.")
    parser.add_argument("--config", required=True, help="Path to public full yaml config.")
    parser.add_argument("--quick", action="store_true", help="Run smoke-test budget.")
    parser.add_argument("--resume", action="store_true", help="Reuse completed checkpoint outputs when available.")
    return parser.parse_args()


def _load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        config = yaml.safe_load(fh)
    if bool(config.get("allow_synthetic_fallback", False)):
        raise RuntimeError("public_full forbids synthetic fallback")
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
    checkpoint_results = checkpoints_dir / f"public_full_{suffix}_results_by_split.csv"
    checkpoint_candidates = checkpoints_dir / f"public_full_{suffix}_candidate_log.csv"
    checkpoint_summary = checkpoints_dir / f"public_full_{suffix}_summary_metrics.csv"
    checkpoint_bootstrap = checkpoints_dir / f"public_full_{suffix}_bootstrap.csv"

    if args.resume and checkpoint_results.exists() and checkpoint_candidates.exists() and checkpoint_summary.exists():
        import pandas as pd

        results = pd.read_csv(checkpoint_results)
        candidates = pd.read_csv(checkpoint_candidates)
        summary = pd.read_csv(checkpoint_summary)
        bootstrap = pd.read_csv(checkpoint_bootstrap) if checkpoint_bootstrap.exists() else pd.DataFrame()
        bundle = load_or_download_public_data(config, ROOT, quick=False)
        if "effective_start_date" in results.columns:
            summary.attrs["effective_start_date"] = str(results["effective_start_date"].iloc[0])
        if "effective_end_date" in results.columns:
            summary.attrs["effective_end_date"] = str(results["effective_end_date"].iloc[0])
    else:
        bundle = load_or_download_public_data(config, ROOT, quick=False)
        output = run_public_toy(bundle, config, quick=args.quick)
        results = output.results_by_split
        candidates = output.candidate_log
        summary = output.summary
        bootstrap = output.bootstrap
        results["effective_start_date"] = summary.attrs.get("effective_start_date", str(bundle.start_date.date()))
        results["effective_end_date"] = summary.attrs.get("effective_end_date", str(bundle.end_date.date()))
        results.to_csv(checkpoint_results, index=False)
        candidates.to_csv(checkpoint_candidates, index=False)
        summary.to_csv(checkpoint_summary, index=False)
        if bootstrap is not None:
            bootstrap.to_csv(checkpoint_bootstrap, index=False)

    report_config = dict(config)
    report_config["run_mode"] = "quick smoke" if args.quick else "full"
    if hasattr(summary, "attrs"):
        report_config["effective_start_date"] = summary.attrs.get("effective_start_date", str(bundle.start_date.date()))
        report_config["effective_end_date"] = summary.attrs.get("effective_end_date", str(bundle.end_date.date()))
    else:
        report_config["effective_start_date"] = str(bundle.start_date.date())
        report_config["effective_end_date"] = str(bundle.end_date.date())
    report_config["retained_assets"] = len(bundle.universe)
    if "reason" in bundle.missing_log.columns:
        filtered = bundle.missing_log[bundle.missing_log["reason"] == "insufficient_history"]
    else:
        filtered = bundle.missing_log.iloc[0:0]
    report_config["filtered_tickers"] = ", ".join(sorted(filtered["ticker"].dropna().unique())) if not filtered.empty else "None"

    results.to_csv(outputs_dir / "public_full_results_by_split.csv", index=False)
    candidates.to_csv(outputs_dir / "public_full_candidate_log.csv", index=False)
    summary.to_csv(outputs_dir / "public_full_summary_metrics.csv", index=False)
    if bootstrap is not None:
        bootstrap.to_csv(outputs_dir / "public_full_bootstrap.csv", index=False)
    bundle.missing_log.to_csv(outputs_dir / "public_full_missing_data_log.csv", index=False)
    technical_path, plain_path = write_public_full_reports(results, candidates, summary, bootstrap, report_config, run_root / "reports")

    print(f"Wrote {outputs_dir / 'public_full_results_by_split.csv'}")
    print(f"Wrote {outputs_dir / 'public_full_candidate_log.csv'}")
    print(f"Wrote {outputs_dir / 'public_full_summary_metrics.csv'}")
    print(f"Wrote {outputs_dir / 'public_full_bootstrap.csv'}")
    print(f"Wrote {outputs_dir / 'public_full_missing_data_log.csv'}")
    print(f"Wrote {technical_path}")
    print(f"Wrote {plain_path}")


if __name__ == "__main__":
    main()
