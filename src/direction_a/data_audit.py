from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

AUDIT_COLUMNS = [
    "source_name", "source_type", "url_or_path", "checked_at", "reachable", "requires_auth",
    "license_status", "license_risk", "coverage_start", "coverage_end", "is_true_pit",
    "is_approximate_pit", "survivorship_bias_risk", "delisting_handling",
    "corporate_action_handling", "price_source_needed", "download_size_estimate",
    "implementation_cost", "reproducibility_score", "recommended_role", "decision", "notes",
]

DECISIONS = {
    "ACCEPT_MAIN_CANDIDATE",
    "ACCEPT_DIAGNOSTIC_ONLY",
    "ACCEPT_SANITY_ONLY",
    "REJECT",
    "NEEDS_USER_INPUT",
}


def build_source_audit(config: dict) -> pd.DataFrame:
    checked_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    start = config.get("start_date", "2007-01-01")
    end = config.get("end_date", "2024-12-31")
    rows = [
        {
            "source_name": "Wikipedia S&P 500 changes table",
            "source_type": "public_web_table",
            "url_or_path": "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies#Selected_changes_to_the_list_of_S%26P_500_components",
            "checked_at": checked_at,
            "reachable": "not_network_checked_in_B1",
            "requires_auth": False,
            "license_status": "requires_manual_review",
            "license_risk": "medium",
            "coverage_start": "partial_changes_history",
            "coverage_end": end,
            "is_true_pit": False,
            "is_approximate_pit": True,
            "survivorship_bias_risk": "medium",
            "delisting_handling": "membership changes only; delisted prices still unresolved",
            "corporate_action_handling": "requires external adjusted price source",
            "price_source_needed": True,
            "download_size_estimate": "low",
            "implementation_cost": "medium",
            "reproducibility_score": 0.62,
            "recommended_role": "approximate_pit_main_candidate_after_audit",
            "decision": "NEEDS_USER_INPUT",
            "notes": "Feasible approximate PIT path, but not enough in B1 to call it fully solved or unbiased.",
        },
        {
            "source_name": "Public historical S&P 500 constituent datasets",
            "source_type": "public_github_or_kaggle_metadata",
            "url_or_path": "dataset_specific_url_required_before_B2",
            "checked_at": checked_at,
            "reachable": "not_network_checked_in_B1",
            "requires_auth": "varies",
            "license_status": "unknown_until_dataset_selected",
            "license_risk": "medium_high",
            "coverage_start": "varies",
            "coverage_end": "varies",
            "is_true_pit": False,
            "is_approximate_pit": True,
            "survivorship_bias_risk": "medium",
            "delisting_handling": "dataset-specific audit required",
            "corporate_action_handling": "dataset-specific audit required",
            "price_source_needed": True,
            "download_size_estimate": "low_to_medium",
            "implementation_cost": "medium",
            "reproducibility_score": 0.55,
            "recommended_role": "approximate_pit_main_candidate_after_license_audit",
            "decision": "NEEDS_USER_INPUT",
            "notes": "Could become B2 main candidate only after provenance and license review.",
        },
        {
            "source_name": "Nasdaq/Stooq/yfinance liquid US ticker pool",
            "source_type": "public_price_api_or_csv",
            "url_or_path": "public endpoints or local downloader; no large download in B1",
            "checked_at": checked_at,
            "reachable": "not_network_checked_in_B1",
            "requires_auth": False,
            "license_status": "requires_manual_review",
            "license_risk": "medium",
            "coverage_start": start,
            "coverage_end": end,
            "is_true_pit": False,
            "is_approximate_pit": False,
            "survivorship_bias_risk": "high",
            "delisting_handling": "weak unless delisted tickers are explicitly added",
            "corporate_action_handling": "depends on adjusted price source",
            "price_source_needed": False,
            "download_size_estimate": "medium",
            "implementation_cost": "low_medium",
            "reproducibility_score": 0.70,
            "recommended_role": "liquid_us_universe_diagnostic",
            "decision": "ACCEPT_DIAGNOSTIC_ONLY",
            "notes": "Fallback diagnostic only; claims must be downgraded because it is not PIT.",
        },
        {
            "source_name": "Qlib public US data feasibility",
            "source_type": "public_research_dataset_tooling",
            "url_or_path": "https://github.com/microsoft/qlib",
            "checked_at": checked_at,
            "reachable": "not_network_checked_in_B1",
            "requires_auth": False,
            "license_status": "tool_license_review_required_dataset_separate",
            "license_risk": "medium",
            "coverage_start": "dataset_dependent",
            "coverage_end": "dataset_dependent",
            "is_true_pit": False,
            "is_approximate_pit": "unknown_until_audit",
            "survivorship_bias_risk": "unknown_medium",
            "delisting_handling": "bundle construction audit required",
            "corporate_action_handling": "bundle construction audit required",
            "price_source_needed": False,
            "download_size_estimate": "medium_high",
            "implementation_cost": "medium_high",
            "reproducibility_score": 0.50,
            "recommended_role": "B2_feasibility_audit_only",
            "decision": "NEEDS_USER_INPUT",
            "notes": "Potential tooling path; B1 does not download or certify PIT correctness.",
        },
        {
            "source_name": "Current S&P 500 constituents",
            "source_type": "current_constituent_list",
            "url_or_path": "current public constituent pages",
            "checked_at": checked_at,
            "reachable": "not_network_checked_in_B1",
            "requires_auth": False,
            "license_status": "requires_manual_review",
            "license_risk": "low_medium",
            "coverage_start": "current_only",
            "coverage_end": "current_only",
            "is_true_pit": False,
            "is_approximate_pit": False,
            "survivorship_bias_risk": "high",
            "delisting_handling": "none",
            "corporate_action_handling": "none",
            "price_source_needed": True,
            "download_size_estimate": "low",
            "implementation_cost": "low",
            "reproducibility_score": 0.35,
            "recommended_role": "not_main_evidence",
            "decision": "REJECT",
            "notes": "Cannot be marked true PIT or unbiased main evidence.",
        },
        {
            "source_name": "ETF universe sanity tier",
            "source_type": "public_etf_prices",
            "url_or_path": "existing TASE ETF public data path or deterministic smoke mock",
            "checked_at": checked_at,
            "reachable": "local_or_mock_only_in_B1",
            "requires_auth": False,
            "license_status": "requires_manual_review_for_real_prices",
            "license_risk": "medium",
            "coverage_start": start,
            "coverage_end": end,
            "is_true_pit": False,
            "is_approximate_pit": False,
            "survivorship_bias_risk": "medium",
            "delisting_handling": "not adequate for stock PIT claims",
            "corporate_action_handling": "depends on adjusted ETF price source",
            "price_source_needed": False,
            "download_size_estimate": "low_medium",
            "implementation_cost": "low",
            "reproducibility_score": 0.80,
            "recommended_role": "sanity_universe_only",
            "decision": "ACCEPT_SANITY_ONLY",
            "notes": "Valid for machinery sanity, not for final stock-universe evidence.",
        },
        {
            "source_name": "CRSP/Compustat",
            "source_type": "paid_institutional_database",
            "url_or_path": "institutional access only",
            "checked_at": checked_at,
            "reachable": "not_checked_paid_source",
            "requires_auth": True,
            "license_status": "restricted_paid",
            "license_risk": "high_restricted",
            "coverage_start": "broad_historical",
            "coverage_end": end,
            "is_true_pit": True,
            "is_approximate_pit": False,
            "survivorship_bias_risk": "low_if_correctly_used",
            "delisting_handling": "strong",
            "corporate_action_handling": "strong",
            "price_source_needed": False,
            "download_size_estimate": "medium_high",
            "implementation_cost": "high",
            "reproducibility_score": 0.30,
            "recommended_role": "not_default_low_cost_path",
            "decision": "REJECT",
            "notes": "Scientifically strong but cannot be default public path due to access and license constraints.",
        },
    ]
    return pd.DataFrame(rows, columns=AUDIT_COLUMNS)


def validate_audit(audit: pd.DataFrame) -> list[str]:
    warnings: list[str] = []
    current = audit[audit["source_name"].str.contains("Current", case=False, na=False)]
    if not current.empty and bool(current.iloc[0]["is_true_pit"]):
        warnings.append("current constituents cannot be true PIT")
    etf = audit[audit["source_name"].str.contains("ETF", case=False, na=False)]
    if not etf.empty and str(etf.iloc[0]["decision"]) != "ACCEPT_SANITY_ONLY":
        warnings.append("ETF tier cannot be main PIT evidence")
    missing_license = audit[audit["license_status"].astype(str).str.contains("unknown|requires_manual_review", case=False, na=False)]
    if not missing_license.empty:
        warnings.append("some public sources still require license review")
    auth_default = audit[(audit["requires_auth"] == True) & audit["decision"].eq("ACCEPT_MAIN_CANDIDATE")]
    if not auth_default.empty:
        warnings.append("auth-required source cannot be default public path")
    return warnings


def main_data_path_decision(audit: pd.DataFrame) -> tuple[str, str]:
    accepted_main = audit[audit["decision"].eq("ACCEPT_MAIN_CANDIDATE")]
    if not accepted_main.empty:
        return "PASS", "Approximate PIT main candidate accepted for B2/B3 after B1 audit."
    diagnostic = audit[audit["decision"].eq("ACCEPT_DIAGNOSTIC_ONLY")]
    if not diagnostic.empty:
        return (
            "PASS_WITH_DIAGNOSTIC_FALLBACK",
            "No public source is certified as true PIT in B1. Use liquid US diagnostic fallback only with downgraded claims; keep approximate PIT sources as B2 audit candidates.",
        )
    return "BLOCKED_NEEDS_DATA_SOURCE", "No usable public diagnostic fallback found; user must provide a data source."


def write_main_data_path_decision(path: Path, status: str, decision_text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""# Direction A B1 Main Data Path Decision\n\nStatus: {status}\n\n{decision_text}\n\nRules preserved:\n\n- Current constituents are not point-in-time evidence.\n- Liquid US fallback is diagnostic only and cannot support unbiased PIT claims.\n- ETF universe is sanity tier only.\n- Public approximate PIT sources need license, survivorship-bias, delisting, and corporate-action audit before final experiments.\n""",
        encoding="utf-8",
    )
