"""Flujo de revisión humana (Fase 5).

El motor solo prioriza; la decisión final la toma una persona. Este módulo
mantiene una cola de alertas y un registro auditable de decisiones, sin usar
la verdad terreno.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

VALID_DECISIONS = {"pendiente", "confirmado", "descartado", "falso_positivo", "en_seguimiento", "escalado"}


def _load_register(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"No existe {path}")
    frame = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8")
    required = {"cluster_id", "risk_score", "size", "summary"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Faltan columnas en el registro: {sorted(missing)}")
    return frame


def _decisions_path(output_dir: Path) -> Path:
    return output_dir / "decisions.jsonl"


def _load_decisions(output_dir: Path) -> dict[str, dict[str, Any]]:
    path = _decisions_path(output_dir)
    decisions: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return decisions
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        cluster_id = str(item.get("cluster_id", ""))
        if cluster_id:
            decisions[cluster_id] = item
    return decisions


def _write_decision(output_dir: Path, decision: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = _decisions_path(output_dir)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(decision, ensure_ascii=False) + "\n")


def list_queue(register_path: Path, output_dir: Path, limit: int = 20) -> pd.DataFrame:
    register = _load_register(register_path)
    decisions = _load_decisions(output_dir)
    register = register.copy()
    register["decision"] = register["cluster_id"].map(
        lambda cluster_id: decisions.get(cluster_id, {}).get("decision", "pendiente")
    )
    register["reviewer"] = register["cluster_id"].map(
        lambda cluster_id: decisions.get(cluster_id, {}).get("reviewer", "")
    )
    register["reviewed_at"] = register["cluster_id"].map(
        lambda cluster_id: decisions.get(cluster_id, {}).get("reviewed_at", "")
    )
    register["notes"] = register["cluster_id"].map(
        lambda cluster_id: decisions.get(cluster_id, {}).get("notes", "")
    )
    pending = register[register["decision"] == "pendiente"]
    ordered = pd.concat([pending, register[register["decision"] != "pendiente"]], ignore_index=True)
    return ordered.head(limit)


def record_decision(
    register_path: Path,
    output_dir: Path,
    cluster_id: str,
    decision: str,
    reviewer: str = "analista",
    notes: str = "",
) -> dict[str, Any]:
    if decision not in VALID_DECISIONS:
        raise ValueError(f"Decisión inválida: {decision}. Válidas: {sorted(VALID_DECISIONS)}")
    register = _load_register(register_path)
    if cluster_id not in set(register["cluster_id"]):
        raise ValueError(f"Cluster no existe en el registro: {cluster_id}")
    item = {
        "cluster_id": cluster_id,
        "decision": decision,
        "reviewer": reviewer,
        "notes": notes,
        "reviewed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    _write_decision(output_dir, item)
    return item


def export_reviewed(register_path: Path, output_dir: Path) -> Path:
    register = _load_register(register_path)
    decisions = _load_decisions(output_dir)
    rows = []
    for row in register.to_dict("records"):
        item = decisions.get(str(row["cluster_id"]), {})
        rows.append({
            **row,
            "decision": item.get("decision", "pendiente"),
            "reviewer": item.get("reviewer", ""),
            "reviewed_at": item.get("reviewed_at", ""),
            "notes": item.get("notes", ""),
        })
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "reviewed_alerts.csv"
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cola de revisión humana de alertas")
    parser.add_argument("--register", type=Path, default=Path("outputs/explain/risk_register.csv"))
    parser.add_argument("--output", type=Path, default=Path("outputs/review"))
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--decide", type=str, default=None, help="cluster_id a decidir")
    parser.add_argument("--decision", choices=sorted(VALID_DECISIONS), default="pendiente")
    parser.add_argument("--reviewer", default="analista")
    parser.add_argument("--notes", default="")
    parser.add_argument("--export", action="store_true", help="exporta reviewed_alerts.csv")
    args = parser.parse_args(argv)

    if args.decide:
        item = record_decision(
            args.register, args.output, args.decide, args.decision, args.reviewer, args.notes
        )
        print(json.dumps(item, ensure_ascii=False, indent=2))
        return 0

    queue = list_queue(args.register, args.output, args.limit)
    print(queue.to_string(index=False))
    if args.export:
        path = export_reviewed(args.register, args.output)
        print(f"Exportado: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())