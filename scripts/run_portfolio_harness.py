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
from src.portfolio_experiment import finalize_portfolio_harness_output, run_portfolio_harness
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



def _is_full_10seed_run(args: argparse.Namespace) -> bool:
    return (not args.quick) and str(args.output_prefix).endswith("full_10seed")


def _validate_full_10seed_config(config: dict) -> None:
    problems = []
    if str(config.get("mode")) != "full":
        problems.append("mode must be full")
    if int(config.get("n_seeds", -1)) != 10:
        problems.append("n_seeds must be 10")
    if int(config.get("search_budget", -1)) != 100:
        problems.append("search_budget must be 100")
    if bool(config.get("allow_synthetic_fallback", True)):
        problems.append("allow_synthetic_fallback must be false")
    judgment = config.get("judgment", {}) or {}
    if float(judgment.get("return_preservation_threshold", -0.02)) != -0.02:
        problems.append("return_preservation_threshold must remain -0.0200")
    if problems:
        raise RuntimeError("full_10seed config refused: " + "; ".join(problems))


def _load_seed_checkpoint(paths: dict[str, Path]) -> tuple[pd.DataFrame, pd.DataFrame] | None:
    if paths["results"].exists() and paths["candidates"].exists():
        return pd.read_csv(paths["results"]), pd.read_csv(paths["candidates"])
    return None


def _seed_paths(checkpoints_dir: Path, prefix: str, seed: int) -> dict[str, Path]:
    seed_prefix = f"{prefix}_full_seed{seed}"
    return {
        "results": checkpoints_dir / f"{seed_prefix}_results_by_split.csv",
        "candidates": checkpoints_dir / f"{seed_prefix}_candidate_log.csv",
    }


def _run_full_10seed_with_resume(bundle, config: dict, checkpoints_dir: Path, prefix: str, resume: bool):
    results_parts = []
    candidate_parts = []
    for seed in range(10):
        paths = _seed_paths(checkpoints_dir, prefix, seed)
        cached = _load_seed_checkpoint(paths) if resume else None
        if cached is None:
            seed_config = dict(config)
            seed_config["seed_ids"] = [seed]
            seed_output = run_portfolio_harness(bundle, seed_config, quick=False)
            seed_results = seed_output.results_by_split
            seed_candidates = seed_output.candidate_log
            seed_results.to_csv(paths["results"], index=False)
            seed_candidates.to_csv(paths["candidates"], index=False)
            print(f"Completed and checkpointed seed {seed}")
        else:
            seed_results, seed_candidates = cached
            print(f"Resumed seed {seed} from checkpoint")
        results_parts.append(seed_results)
        candidate_parts.append(seed_candidates)
    results = pd.concat(results_parts, ignore_index=True)
    candidates = pd.concat(candidate_parts, ignore_index=True)
    observed = sorted(int(seed) for seed in results["seed"].dropna().unique())
    if observed != list(range(10)):
        raise RuntimeError(f"full_10seed refused incomplete seed coverage: {observed}")
    return finalize_portfolio_harness_output(results, candidates, config)

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
    prefix = str(args.output_prefix)
    if _is_full_10seed_run(args):
        _validate_full_10seed_config(config)
    suffix = "quick" if args.quick else "full"
    checkpoint_prefix = f"{prefix}_{suffix}"
    paths = {
        "results": checkpoints_dir / f"{checkpoint_prefix}_results_by_split.csv",
        "candidates": checkpoints_dir / f"{checkpoint_prefix}_candidate_log.csv",
        "summary": checkpoints_dir / f"{checkpoint_prefix}_summary_metrics.csv",
        "invalid": checkpoints_dir / f"{checkpoint_prefix}_invalid_high_score_log.csv",
        "paired": checkpoints_dir / f"{checkpoint_prefix}_paired_bootstrap.csv",
    }
    bundle = load_or_download_public_data(config, ROOT, quick=args.quick)
    if _is_full_10seed_run(args):
        output = _run_full_10seed_with_resume(bundle, config, checkpoints_dir, prefix, args.resume)
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
    else:
        can_resume = args.resume and all(path.exists() for path in paths.values())
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
    report_config["run_mode"] = "quick smoke" if args.quick else ("full_10seed" if _is_full_10seed_run(args) else str(config.get("mode", "full")))
    report_config["split_count"] = int(results["split_id"].nunique()) if "split_id" in results else "NA"
    report_config["paired_observations"] = int(results[results["arm"] == "TASE Typed Portfolio Harness Reconstruction"][["seed", "split_id"]].drop_duplicates().shape[0]) if {"arm", "seed", "split_id"}.issubset(results.columns) else "NA"
    if _is_full_10seed_run(args):
        report_config["partial_full_reference"] = {"h1a": True, "h2": True, "h3p": False, "h4p": False, "h5p": True}
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
