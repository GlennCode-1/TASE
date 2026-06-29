from __future__ import annotations

import argparse
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.public_data import load_or_download_public_data
from src.public_experiment import run_public_toy
from src.reporting import write_public_toy_reports


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run T.A.S.E public ETF toy experiment.")
    parser.add_argument("--config", required=True, help="Path to public toy yaml config.")
    parser.add_argument("--quick", action="store_true", help="Run reduced seed and search budget smoke test.")
    parser.add_argument("--allow-synthetic-fallback", action="store_true", help="Only for offline smoke tests.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = Path.cwd() / config_path
    with config_path.open("r", encoding="utf-8") as fh:
        config = yaml.safe_load(fh)
    if args.allow_synthetic_fallback:
        config["allow_synthetic_fallback"] = True

    bundle = load_or_download_public_data(config, ROOT, quick=args.quick)
    output = run_public_toy(bundle, config, quick=args.quick)
    report_config = dict(config)
    report_config["run_mode"] = "quick" if args.quick else "full"
    report_config["effective_start_date"] = output.summary.attrs.get("effective_start_date", str(bundle.start_date.date()))
    report_config["effective_end_date"] = output.summary.attrs.get("effective_end_date", str(bundle.end_date.date()))
    output.summary.attrs["run_mode"] = report_config["run_mode"]

    outputs_dir = ROOT / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    output.results_by_split.to_csv(outputs_dir / "public_toy_results_by_split.csv", index=False)
    output.candidate_log.to_csv(outputs_dir / "public_toy_candidate_log.csv", index=False)
    output.summary.to_csv(outputs_dir / "public_toy_summary_metrics.csv", index=False)
    bundle.missing_log.to_csv(outputs_dir / "public_toy_missing_data_log.csv", index=False)
    technical_path, plain_path = write_public_toy_reports(output.results_by_split, output.candidate_log, output.summary, report_config, ROOT / "reports")

    print(f"Wrote {outputs_dir / 'public_toy_results_by_split.csv'}")
    print(f"Wrote {outputs_dir / 'public_toy_candidate_log.csv'}")
    print(f"Wrote {outputs_dir / 'public_toy_summary_metrics.csv'}")
    print(f"Wrote {outputs_dir / 'public_toy_missing_data_log.csv'}")
    print(f"Wrote {technical_path}")
    print(f"Wrote {plain_path}")


if __name__ == "__main__":
    main()
