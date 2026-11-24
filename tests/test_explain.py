"""Pruebas de la Fase 4: expedientes explicables."""

from __future__ import annotations

import json
from pathlib import Path

from explain.dossier import run_explain


def test_explain_generates_dossiers(tmp_path: Path) -> None:
    detection_dir = Path("outputs/detection")
    if not detection_dir.exists():
        return
    result = run_explain(
        detection_dir,
        Path("outputs/graph/graph.pkl"),
        Path("data/raw"),
        tmp_path / "explain",
        5,
    )
    assert (tmp_path / "explain" / "dossiers.json").exists()
    assert (tmp_path / "explain" / "risk_register.csv").exists()
    assert (tmp_path / "explain" / "explain_meta.json").exists()
    dossiers = json.loads((tmp_path / "explain" / "dossiers.json").read_text(encoding="utf-8"))
    assert len(dossiers) == 5
    assert dossiers[0]["shared_attributes"]
    assert dossiers[0]["members"]
    assert dossiers[0]["privacy_note"]
    assert (tmp_path / "explain" / f"dossier_{dossiers[0]['cluster_id']}.md").exists()