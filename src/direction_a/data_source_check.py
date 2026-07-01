from __future__ import annotations

import pandas as pd

DATA_SOURCE_COLUMNS = [
    "source_name",
    "source_type",
    "url_or_path",
    "requires_auth",
    "estimated_coverage_start",
    "estimated_coverage_end",
    "is_point_in_time",
    "is_approximate_pit",
    "survivorship_bias_risk",
    "delisting_handling",
    "data_license_risk",
    "download_size_risk",
    "implementation_cost",
    "recommended_role",
    "notes",
]


def build_data_source_feasibility(config: dict) -> pd.DataFrame:
    start = config.get("start_date", "2007-01-01")
    end = config.get("end_date", "2024-12-31")
    rows = [
        {
            "source_name": "Wikipedia S&P 500 changes table",
            "source_type": "public_web_table",
            "url_or_path": "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies#Selected_changes_to_the_list_of_S%26P_500_components",
            "requires_auth": False,
            "estimated_coverage_start": "partial_historical_changes",
            "estimated_coverage_end": end,
            "is_point_in_time": False,
            "is_approximate_pit": True,
            "survivorship_bias_risk": "medium",
            "delisting_handling": "membership changes only; delisted price history still needs separate handling",
            "data_license_risk": "medium_review_required",
            "download_size_risk": "low",
            "implementation_cost": "medium",
            "recommended_role": "approximate_pit_candidate_source",
            "notes": "Can reconstruct an approximate large-cap membership timeline but is not complete unbiased PIT evidence.",
        },
        {
            "source_name": "Public historical S&P 500 constituent datasets",
            "source_type": "public_github_or_kaggle_metadata",
            "url_or_path": "source_to_be_selected_in_B1; do not hard-depend in B0",
            "requires_auth": "varies",
            "estimated_coverage_start": "varies_by_dataset",
            "estimated_coverage_end": "varies_by_dataset",
            "is_point_in_time": False,
            "is_approximate_pit": True,
            "survivorship_bias_risk": "medium",
            "delisting_handling": "must audit dataset-specific construction",
            "data_license_risk": "medium_high",
            "download_size_risk": "low_to_medium",
            "implementation_cost": "medium",
            "recommended_role": "candidate_for_B1_source_audit",
            "notes": "B0 records feasibility only; B1 must choose and audit license/provenance before use.",
        },
        {
            "source_name": "Nasdaq/Stooq/yfinance liquid US ticker pool",
            "source_type": "public_price_api_or_csv",
            "url_or_path": "local downloader or public endpoints; no large download in B0",
            "requires_auth": False,
            "estimated_coverage_start": start,
            "estimated_coverage_end": end,
            "is_point_in_time": False,
            "is_approximate_pit": False,
            "survivorship_bias_risk": "high",
            "delisting_handling": "weak unless explicit delisted tickers are added",
            "data_license_risk": "medium_review_required",
            "download_size_risk": "medium",
            "implementation_cost": "low_medium",
            "recommended_role": "liquid_us_universe_diagnostic",
            "notes": "Useful fallback diagnostic only; current/liquid constituents cannot be called unbiased PIT.",
        },
        {
            "source_name": "Qlib public US data feasibility",
            "source_type": "public_research_dataset_tooling",
            "url_or_path": "https://github.com/microsoft/qlib",
            "requires_auth": False,
            "estimated_coverage_start": "dataset_dependent",
            "estimated_coverage_end": "dataset_dependent",
            "is_point_in_time": False,
            "is_approximate_pit": "unknown_until_B1_audit",
            "survivorship_bias_risk": "unknown_medium",
            "delisting_handling": "must audit Qlib bundle construction",
            "data_license_risk": "medium_review_required",
            "download_size_risk": "medium_high",
            "implementation_cost": "medium_high",
            "recommended_role": "B1_feasibility_audit_only",
            "notes": "Potential reproducible tooling path; B0 does not download or assert PIT correctness.",
        },
        {
            "source_name": "Current S&P 500 constituents",
            "source_type": "current_constituent_list",
            "url_or_path": "current public constituent pages",
            "requires_auth": False,
            "estimated_coverage_start": "current_only",
            "estimated_coverage_end": "current_only",
            "is_point_in_time": False,
            "is_approximate_pit": False,
            "survivorship_bias_risk": "high",
            "delisting_handling": "none",
            "data_license_risk": "low_medium",
            "download_size_risk": "low",
            "implementation_cost": "low",
            "recommended_role": "not_main_evidence",
            "notes": "Must not be represented as PIT; at most a biased diagnostic universe.",
        },
        {
            "source_name": "ETF universe sanity tier",
            "source_type": "public_etf_prices",
            "url_or_path": "existing TASE ETF public data path",
            "requires_auth": False,
            "estimated_coverage_start": start,
            "estimated_coverage_end": end,
            "is_point_in_time": False,
            "is_approximate_pit": False,
            "survivorship_bias_risk": "medium",
            "delisting_handling": "ETF survivorship still possible; less suitable for stock PIT claims",
            "data_license_risk": "medium_review_required",
            "download_size_risk": "low_medium",
            "implementation_cost": "low",
            "recommended_role": "sanity_universe_only",
            "notes": "Good for pipeline sanity, not for final stock-universe selection reliability claim.",
        },
        {
            "source_name": "CRSP/Compustat",
            "source_type": "paid_institutional_database",
            "url_or_path": "institutional access only",
            "requires_auth": True,
            "estimated_coverage_start": "broad_historical",
            "estimated_coverage_end": end,
            "is_point_in_time": True,
            "is_approximate_pit": False,
            "survivorship_bias_risk": "low_if_correctly_used",
            "delisting_handling": "strong",
            "data_license_risk": "high_restricted",
            "download_size_risk": "medium_high",
            "implementation_cost": "high",
            "recommended_role": "not_default_low_cost_path",
            "notes": "Scientifically strong but not the default for current low-cost public reproducibility goal.",
        },
    ]
    return pd.DataFrame(rows, columns=DATA_SOURCE_COLUMNS)


def b0_data_status(feasibility: pd.DataFrame) -> str:
    public_pit = feasibility[(feasibility["requires_auth"] == False) & (feasibility["is_point_in_time"] == True)]
    approx = feasibility[feasibility["is_approximate_pit"].astype(str).str.lower().isin(["true", "unknown_until_b1_audit"])]
    if not public_pit.empty:
        return "PASS"
    if not approx.empty:
        return "NEEDS_USER_INPUT"
    return "BLOCKED"


def validate_source_roles(feasibility: pd.DataFrame) -> list[str]:
    warnings: list[str] = []
    current = feasibility[feasibility["source_name"].str.contains("Current", case=False, na=False)]
    if not current.empty and bool(current.iloc[0]["is_point_in_time"]):
        warnings.append("current constituents cannot be marked true PIT")
    etf = feasibility[feasibility["source_name"].str.contains("ETF", case=False, na=False)]
    if not etf.empty and str(etf.iloc[0]["recommended_role"]) != "sanity_universe_only":
        warnings.append("ETF universe must remain sanity tier")
    fallback = feasibility[feasibility["recommended_role"].eq("liquid_us_universe_diagnostic")]
    if fallback.empty:
        warnings.append("diagnostic fallback universe missing")
    return warnings
