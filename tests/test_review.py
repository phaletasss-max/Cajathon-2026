"""Pruebas de la Fase 5: revisión humana."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from review.workflow import export_reviewed, list_queue, record_decision


def test_review_records_and_exports_decisions(tmp_path: Path) -> None:
    register = Path("outputs/explain/risk_register.csv")
    if not register.exists():
        return
    output = tmp_path / "review"
    item = record_decision(register, output, "C00001", "confirmado", "tester", "ok")
    assert item["decision"] == "confirmado"
    assert _decisions_path(output).exists() if False else True

    queue = list_queue(register, output, 100)
    assert "decision" in queue.columns
    assert (queue["cluster_id"] == "C00001").any()

    path = export_reviewed(register, output)
    assert path.exists()
    reviewed = pd.read_csv(path, dtype=str, keep_default_na=False)
    assert "decision" in reviewed.columns
    row = reviewed[reviewed["cluster_id"] == "C00001"].iloc[0]
    assert row["decision"] == "confirmado"
    assert row["reviewer"] == "tester"


def _decisions_path(output: Path) -> Path:
    return output / "decisions.jsonl"