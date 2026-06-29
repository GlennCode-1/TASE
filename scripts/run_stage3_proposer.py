from __future__ import annotations

import argparse
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.experiments import run_stage3_proposer
from src.reporting import write_stage3_reports


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run T.A.S.E Stage 3 diagnostic proposer.")
    parser.add_argument("--config", required=True, help="Path to stage3 yaml config.")
    parser.add_argument("--n-seeds", type=int, default=None, help="Override number of seeds.")
    parser.add_argument("--patch-budget", type=int, default=None, help="Override patch budget.")
    parser.add_argument("--candidate-per-round", type=int, default=None, help="Override candidates per round.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = Path.cwd() / config_path

    with config_path.open("r", encoding="utf-8") as fh:
        config = yaml.safe_load(fh)

    if args.n_seeds is not None:
        config["n_seeds"] = args.n_seeds
    if args.patch_budget is not None:
        config["patch_budget"] = args.patch_budget
    if args.candidate_per_round is not None:
        config["candidate_per_round"] = args.candidate_per_round

    results, patch_log, summary = run_stage3_proposer(config)

    outputs_dir = ROOT / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    results.to_csv(outputs_dir / "results_by_seed_stage3.csv", index=False)
    patch_log.to_csv(outputs_dir / "patch_log_stage3.csv", index=False)
    summary.to_csv(outputs_dir / "summary_metrics_stage3.csv", index=False)
    technical_path, plain_path = write_stage3_reports(results, summary, config, ROOT / "reports")

    print(f"Wrote {outputs_dir / 'results_by_seed_stage3.csv'}")
    print(f"Wrote {outputs_dir / 'patch_log_stage3.csv'}")
    print(f"Wrote {outputs_dir / 'summary_metrics_stage3.csv'}")
    print(f"Wrote {technical_path}")
    print(f"Wrote {plain_path}")


if __name__ == "__main__":
    main()
