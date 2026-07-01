from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.direction_a.candidate_library import build_candidate_library, candidate_count_status, operator_library_spec
from src.direction_a.candidate_registry import registry_schema
from src.direction_a.data_source_check import b0_data_status, build_data_source_feasibility, validate_source_roles
from src.direction_a.matrix_design import matrix_design_markdown
from src.direction_a.patch_language import FORBIDDEN_FIELDS, FROZEN_METHOD_CONSTRAINTS
from src.direction_a.spec_loader import write_spec_inventory


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Direction A B0 structure/schema/source feasibility check.")
    parser.add_argument("--config", required=True)
    return parser.parse_args()


def _load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _write_reports(report_path: Path, plain_path: Path, inventory: dict, feasibility: pd.DataFrame, candidates: pd.DataFrame, count_status: str, data_status: str, warnings: list[str]) -> str:
    spec_missing = [doc["path"] for doc in inventory["documents"] if not doc["exists"]]
    b0_status = "PASS" if inventory["status"] == "PASS" and data_status in {"PASS", "NEEDS_USER_INPUT"} and not warnings and count_status == "PASS_WITHIN_TARGET" else "NEEDS_USER_INPUT"
    if data_status == "BLOCKED" or inventory["status"] != "PASS":
        b0_status = "NEEDS_USER_INPUT"
    constraints = "\n".join(f"- {item}" for item in FROZEN_METHOD_CONSTRAINTS)
    forbidden = ", ".join(sorted(FORBIDDEN_FIELDS))
    report = f"""# Direction A B0 Report

## Stage B0 Scope

B0 freezes the Direction A method specification, creates the isolated engineering scaffold, drafts the typed workflow patch schema, checks public data-source feasibility, designs the candidate library, and defines candidate matrix/hash/registry formats. B0 does not run a full experiment, does not call an LLM API, and does not make any result claim.

## Specs Found / Missing

- Found: {inventory['found_count']} / {inventory['spec_count']}
- Missing: {', '.join(spec_missing) if spec_missing else 'none'}
- Spec status: {inventory['status']}

## Frozen Method Constraints

{constraints}

## Typed Patch Schema Status

The B0 schema defines seven patch types with typed parameter models: ValidationSchedulePatch, PruningRulePatch, PenaltyUsagePatch, CriticLoopPatch, EnsembleRulePatch, ArchivePolicyPatch, and RetestRollbackPatch. Parameters are constrained by enums / pre-registered scalar choices, and nested free-form parameter dictionaries are rejected.

Forbidden fields: {forbidden}

## Data Source Feasibility

{feasibility.to_markdown(index=False)}

Recommended path: use an approximate PIT public source only after B1 source audit; otherwise use `liquid_us_universe_diagnostic` as a diagnostic fallback and ETF universe only as sanity tier. Current constituents must not be described as PIT.

## Candidate Library Summary

- Candidate count estimate: {len(candidates)}
- Candidate count status: {count_status}
- Operator families: {candidates['operator_family'].nunique()}
- Uses future data by default: {bool(candidates['uses_future_data'].any())}

## Matrix / Hash / Registry Design

B1 should precompute signal, position, gross return, net return, turnover, cost-adjusted PnL, and diagnostic matrices. Large matrices should use Parquet for audit tables and NumPy memmap/Zarr for dense arrays, not giant CSV. Each candidate must store signal/PnL/turnover/cost-PnL hashes using deterministic SHA-256 after configured float rounding.

## Risks / Blockers

- PIT source is not fully solved in B0; public approximate PIT candidates need B1 audit.
- Public datasets may have survivorship-bias, delisting, or license risk.
- Candidate library is pre-registered design only; no candidate PnL has been computed.
- The four method specs are required source of truth; missing specs would block B1.
- Warnings: {', '.join(warnings) if warnings else 'none'}

## Decision

B0 status: {b0_status}

Next stage recommendation: {'enter B1 source audit and candidate precompute planning' if b0_status in {'PASS', 'NEEDS_USER_INPUT'} else 'repair data-source/spec blockers before B1'}.
"""
    plain = f"""# 大白话总结

这一步是 Direction A 的 B0，不是正式实验。它没有跑 full experiment，没有证明 TASE 有效，也没有证明能赚钱或发现 alpha。

这一步做的是把方法边界先钉住：候选策略库、operator、参数网格、预算、交易成本、locked test 和最终指标都不能乱改；TASE 以后只能改筛选、复核、归档、组合这些 workflow 层面的东西。

四份 spec 当前找到 {inventory['found_count']} / {inventory['spec_count']}。候选库只是预注册设计，估计有 {len(candidates)} 个 candidate，处在 1000-2000 目标区间内。数据源方面，公开 PIT 股票池还没有完全解决，只能说有 approximate PIT 方案需要 B1 审计；current constituents 不能冒充 PIT，ETF 只能做 sanity check。

B0 状态：{b0_status}。下一步可以进入 B1 的数据源审计和 candidate precompute 设计，但还不能写成实验结果。
"""
    report_path.write_text(report, encoding="utf-8")
    plain_path.write_text(plain, encoding="utf-8")
    return b0_status


def main() -> None:
    args = parse_args()
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = Path.cwd() / config_path
    config = _load_config(config_path)
    if config.get("stage") != "B0":
        raise RuntimeError("Direction A B0 script refuses non-B0 config")
    if bool(config.get("data_source_check", {}).get("allow_large_download_in_b0", True)):
        raise RuntimeError("B0 forbids large data downloads")
    if bool(config.get("locked_test", {}).get("accessible_in_b0", True)):
        raise RuntimeError("B0 forbids locked-test access")

    output_dir = ROOT / "outputs" / "direction_a_b0"
    report_dir = ROOT / "reports"
    docs_b0_dir = ROOT / "docs" / "b0"
    output_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    docs_b0_dir.mkdir(parents=True, exist_ok=True)

    inventory = write_spec_inventory(ROOT, config["spec_documents"], output_dir / "spec_inventory.json")
    feasibility = build_data_source_feasibility(config["data_source_check"])
    warnings = validate_source_roles(feasibility)
    data_status = b0_data_status(feasibility)
    operators = operator_library_spec()
    candidates = build_candidate_library(config["data_source_check"]["preferred_main_universe"])
    count_status = candidate_count_status(
        len(candidates),
        int(config["candidate_library"]["target_candidate_count_min"]),
        int(config["candidate_library"]["target_candidate_count_max"]),
    )
    registry = registry_schema()

    feasibility.to_csv(output_dir / "data_source_feasibility.csv", index=False)
    operators.to_csv(output_dir / "operator_library_spec.csv", index=False)
    candidates.to_csv(output_dir / "candidate_library_spec.csv", index=False)
    (output_dir / "candidate_matrix_design.md").write_text(matrix_design_markdown(), encoding="utf-8")
    registry.to_csv(output_dir / "candidate_registry_schema.csv", index=False)

    status = _write_reports(
        report_dir / "direction_a_b0_report.md",
        report_dir / "plain_chinese_summary_direction_a_b0.md",
        inventory,
        feasibility,
        candidates,
        count_status,
        data_status,
        warnings,
    )

    for path in [
        output_dir / "spec_inventory.json",
        output_dir / "data_source_feasibility.csv",
        output_dir / "operator_library_spec.csv",
        output_dir / "candidate_library_spec.csv",
        output_dir / "candidate_matrix_design.md",
        output_dir / "candidate_registry_schema.csv",
        report_dir / "direction_a_b0_report.md",
        report_dir / "plain_chinese_summary_direction_a_b0.md",
    ]:
        print(f"Wrote {path}")
    print(f"B0_STATUS={status}")


if __name__ == "__main__":
    main()
