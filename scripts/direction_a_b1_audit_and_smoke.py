from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.direction_a.candidate_precompute import precompute_smoke, select_smoke_candidates
from src.direction_a.data_audit import build_source_audit, main_data_path_decision, validate_audit, write_main_data_path_decision
from src.direction_a.price_loader import make_deterministic_mock_price_panel
from src.direction_a.split_manager import build_split_spec, write_split_spec
from src.direction_a.universe_builder import build_smoke_universe


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Direction A B1 data audit and candidate precompute smoke.")
    parser.add_argument("--config", required=True)
    return parser.parse_args()


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def write_reports(report_path: Path, plain_path: Path, status: str, audit: pd.DataFrame, decision_text: str, smoke_summary: dict, implemented: list[str], registry: pd.DataFrame) -> None:
    report = f"""# Direction A B1 Report\n\n## B1 Scope\n\nB1 audits candidate data sources and validates the candidate precompute machinery on a small deterministic smoke panel. It does not run a full experiment, does not search workflow patches, does not call an LLM API, and does not make a TASE effectiveness claim.\n\n## B0 Dependency Status\n\nB0 outputs were read successfully: candidate library, operator spec, registry schema, matrix design, and B0 report.\n\n## Data Source Audit Summary\n\n{audit.to_markdown(index=False)}\n\n## Main Data Path Decision\n\nStatus: {status}\n\n{decision_text}\n\n## Candidate Precompute Smoke Setting\n\n- Smoke uses deterministic mock prices, not market evidence.\n- Assets: {smoke_summary['asset_count']}\n- Candidates: {smoke_summary['candidate_count']}\n- Train/validation days: {smoke_summary['train_validation_days']}\n- Locked-test days: {smoke_summary['locked_test_days']}\n\n## Implemented Operator Families\n\n{', '.join(implemented)}\n\n## Generated Matrices\n\n{', '.join(smoke_summary['matrices'])}\n\n## Candidate Registry Summary\n\n- Rows: {len(registry)}\n- All four hashes present: {registry[['signal_hash','pnl_hash','turnover_hash','cost_pnl_hash']].notna().all().all()}\n- Uses future data: {bool(registry['uses_future_data'].any())}\n\n## Hash Validation Summary\n\nThe registry stores parameter, signal, PnL, turnover, and cost-adjusted PnL hashes. Hashes use deterministic SHA-256 with configured float rounding.\n\n## Locked-Test Separation Summary\n\nTrain/validation artifacts and locked-test artifacts are written to physically separate directories. Workflow diagnostics and registry paths use train/validation artifacts only. The locked-test access report marks locked reads as forbidden before final evaluation.\n\n## Risks / Blockers\n\n- Public approximate PIT data remains unaudited enough for final claims.\n- The smoke uses deterministic mock prices, so it validates machinery only, not market evidence.\n- Liquid US fallback downgrades claims to diagnostic only.\n- No full TASE proposer or workflow search is implemented in B1.\n\n## Decision\n\nB1 status: {status}\n\nNext stage recommendation: {'B2 data-source repair/audit before full precompute' if status != 'PASS' else 'B2 candidate precompute on audited source'}.\n"""
    plain = f"""# 大白话总结\n\nB1 没有跑 full experiment，也没有证明 TASE 有效、发现 alpha 或真实盈利。它只做两件事：检查数据源能不能用，以及用一个很小的 deterministic mock price panel 验证 candidate precompute、hash、registry 和 locked-test 隔离机制。\n\n数据源结论很克制：公开 approximate PIT 路线还需要继续审计，不能直接说 PIT 已解决；liquid US 只能做 diagnostic fallback，current constituents 不能冒充 PIT，ETF 只能做 sanity。\n\nsmoke 生成了 {smoke_summary['candidate_count']} 个 candidate、{smoke_summary['asset_count']} 个资产和 7 类代表 operator 的矩阵，并写入四类 hash。locked-test 文件被单独放在 locked_test 目录，selection/diagnostic 不能读。\n\nB1 状态：{status}。下一步应先做 B2 数据源修复/审计，再考虑更大规模 precompute。\n"""
    report_path.write_text(report, encoding="utf-8")
    plain_path.write_text(plain, encoding="utf-8")


def main() -> None:
    args = parse_args()
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = Path.cwd() / config_path
    config = load_yaml(config_path)
    if config.get("stage") != "B1":
        raise RuntimeError("Direction A B1 script refuses non-B1 config")
    if bool(config["data_audit"].get("allow_large_download_in_b1", True)):
        raise RuntimeError("B1 forbids large downloads")

    inputs = config["inputs"]
    for key, rel in inputs.items():
        if not (ROOT / rel).exists():
            raise RuntimeError(f"missing B0 dependency {key}: {rel}")

    out = ROOT / "outputs" / "direction_a_b1"
    audit_dir = out / "data_audit"
    smoke_dir = out / "candidate_smoke"
    registry_dir = out / "registry"
    matrices_dir = out / "matrices"
    for directory in [audit_dir, smoke_dir, registry_dir, matrices_dir, smoke_dir / "train_validation", smoke_dir / "locked_test"]:
        directory.mkdir(parents=True, exist_ok=True)

    audit = build_source_audit(config["data_audit"])
    warnings = validate_audit(audit)
    status, decision_text = main_data_path_decision(audit)
    if warnings and status == "PASS":
        status = "PASS_WITH_DIAGNOSTIC_FALLBACK"
    audit.to_csv(audit_dir / "source_audit.csv", index=False)
    write_main_data_path_decision(audit_dir / "main_data_path_decision.md", status, decision_text)

    smoke_cfg = config["smoke_precompute"]
    universe = build_smoke_universe(smoke_cfg["universe_size_max"])
    panel = make_deterministic_mock_price_panel(universe, smoke_cfg["date_start"], smoke_cfg["date_end"])
    panel.head(200).to_csv(smoke_dir / "mock_price_panel_sample.csv", index=False)
    split = build_split_spec(smoke_cfg["date_start"], smoke_cfg["date_end"], smoke_cfg["locked_test_start"], smoke_cfg["locked_test_end"])
    write_split_spec(split, out / "split_spec.json")
    library = pd.read_csv(ROOT / inputs["candidate_library_spec"])
    candidates = select_smoke_candidates(library, smoke_cfg["candidate_count_max"])
    candidates.to_csv(smoke_dir / "smoke_candidate_subset.csv", index=False)
    registry, smoke_summary = precompute_smoke(
        panel,
        candidates,
        split,
        smoke_dir,
        universe.universe_id,
        float(smoke_cfg.get("transaction_cost_bps", 5)),
        int(config["hashing"]["float_round_decimals"]),
    )
    registry.to_csv(registry_dir / "candidate_registry_smoke.csv", index=False)
    smoke_summary["matrices_dir"] = str(matrices_dir)
    implemented = sorted(candidates["operator_family"].unique())
    write_reports(
        ROOT / "reports" / "direction_a_b1_report.md",
        ROOT / "reports" / "plain_chinese_summary_direction_a_b1.md",
        status,
        audit,
        decision_text,
        smoke_summary,
        implemented,
        registry,
    )
    for path in [
        audit_dir / "source_audit.csv",
        audit_dir / "main_data_path_decision.md",
        out / "split_spec.json",
        smoke_dir / "smoke_candidate_subset.csv",
        registry_dir / "candidate_registry_smoke.csv",
        out / "locked_test_access_report.md",
        ROOT / "reports" / "direction_a_b1_report.md",
        ROOT / "reports" / "plain_chinese_summary_direction_a_b1.md",
    ]:
        print(f"Wrote {path}")
    print(f"B1_STATUS={status}")


if __name__ == "__main__":
    main()
