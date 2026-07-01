from __future__ import annotations

import json
from pathlib import Path

KEY_CONSTRAINT_PATTERNS = [
    "不扩张 alpha/operator/candidate space",
    "不偷看 locked test",
    "不修改 transaction cost",
    "不修改 final metric",
    "fixed candidate library",
    "fixed operator library",
    "fixed parameter grid",
    "fixed candidate budget",
    "selection reliability",
    "candidate-level alpha / P&L invariants",
    "archive completeness",
    "budget invariance",
    "locked-test isolation",
    "typed workflow patch language",
    "deterministic patch executor",
]


def load_spec_inventory(root: Path, spec_documents: list[str]) -> dict:
    docs = []
    found_count = 0
    for doc in spec_documents:
        path = root / doc
        item = {"path": doc, "exists": path.exists(), "constraints": []}
        if path.exists():
            found_count += 1
            text = path.read_text(encoding="utf-8")
            lowered = text.lower()
            constraints = []
            for pattern in KEY_CONSTRAINT_PATTERNS:
                if pattern.lower() in lowered:
                    constraints.append(pattern)
            item["constraints"] = constraints
            item["char_count"] = len(text)
        docs.append(item)
    return {
        "spec_count": len(spec_documents),
        "found_count": found_count,
        "missing_count": len(spec_documents) - found_count,
        "status": "PASS" if found_count == len(spec_documents) else "NEEDS_USER_INPUT",
        "documents": docs,
    }


def write_spec_inventory(root: Path, spec_documents: list[str], output_path: Path) -> dict:
    inventory = load_spec_inventory(root, spec_documents)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(inventory, indent=2, ensure_ascii=False), encoding="utf-8")
    return inventory
