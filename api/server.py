"""API HTTP de RIE-02 (Fase 6)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
import pandas as pd

from review.workflow import record_decision
from api.landing import LANDING_HTML

app = FastAPI(title="RedRiesgo", version="0.4.0", description="Inteligencia de Grafos para Detección Temprana de Redes de Fraude (RIE-02)")

_env = __import__("os").environ.get("RIE_OUTPUT_DIR")
BASE_DIR = Path(_env) if _env else (Path("outputs") if (Path("outputs") / "detection" / "clusters.csv").exists() else Path("sample_outputs"))


def _read_csv(name: str, subdir: str = "") -> pd.DataFrame:
    path = BASE_DIR / subdir / name if subdir else BASE_DIR / name
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8")


def _read_json(name: str, subdir: str = "") -> dict[str, Any] | list[Any]:
    path = BASE_DIR / subdir / name if subdir else BASE_DIR / name
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    return LANDING_HTML


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "RIE-02"}


@app.get("/stats")
def stats() -> dict[str, Any]:
    return {
        "graph": _read_json("graph_meta.json", "graph"),
        "detection": _read_json("detection_meta.json", "detection"),
        "explain": _read_json("explain_meta.json", "explain"),
    }


@app.get("/clusters")
def clusters(min_score: float = Query(0.0, ge=0, le=100), limit: int = Query(100, ge=1, le=1000)) -> list[dict[str, Any]]:
    frame = _read_csv("clusters.csv", "detection")
    if frame.empty:
        return []
    frame["risk_score"] = frame["risk_score"].astype(float)
    frame = frame[frame["risk_score"] >= min_score].head(limit)
    return frame.to_dict("records")


@app.get("/clusters/{cluster_id}")
def cluster_detail(cluster_id: str) -> dict[str, Any]:
    frame = _read_csv("clusters.csv", "detection")
    if frame.empty:
        raise HTTPException(status_code=404, detail="sin datos")
    row = frame[frame["cluster_id"] == cluster_id]
    if row.empty:
        raise HTTPException(status_code=404, detail="cluster no encontrado")
    dossier_path = BASE_DIR / "explain" / f"dossier_{cluster_id}.md"
    dossier = {}
    dossiers = _read_json("dossiers.json", "explain")
    if isinstance(dossiers, list):
        for item in dossiers:
            if item.get("cluster_id") == cluster_id:
                dossier = item
                break
    return {"cluster": row.iloc[0].to_dict(), "dossier": dossier, "markdown_path": str(dossier_path)}


@app.get("/applications")
def applications(min_score: float = Query(0.0, ge=0, le=100), limit: int = Query(100, ge=1, le=5000)) -> list[dict[str, Any]]:
    frame = _read_csv("application_scores.csv", "detection")
    if frame.empty:
        return []
    frame["risk_score"] = frame["risk_score"].astype(float)
    frame = frame[frame["risk_score"] >= min_score].head(limit)
    return frame.to_dict("records")


@app.get("/metrics")
def metrics() -> dict[str, Any]:
    path = BASE_DIR / "eval" / "metrics.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/review/queue")
def review_queue(limit: int = Query(20, ge=1, le=500)) -> list[dict[str, Any]]:
    register = _read_csv("risk_register.csv", "explain")
    if register.empty:
        return []
    decisions_path = BASE_DIR / "review" / "decisions.jsonl"
    decisions: dict[str, dict[str, Any]] = {}
    if decisions_path.exists():
        for line in decisions_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            decisions[str(item.get("cluster_id", ""))] = item
    register["decision"] = register["cluster_id"].map(lambda cid: decisions.get(cid, {}).get("decision", "pendiente"))
    pending = register[register["decision"] == "pendiente"]
    ordered = pd.concat([pending, register[register["decision"] != "pendiente"]], ignore_index=True)
    return ordered.head(limit).to_dict("records")


@app.post("/review/decision")
def review_decision(payload: dict[str, Any]) -> dict[str, Any]:
    cluster_id = str(payload.get("cluster_id", ""))
    decision = str(payload.get("decision", "pendiente"))
    reviewer = str(payload.get("reviewer", "analista"))
    notes = str(payload.get("notes", ""))
    if not cluster_id:
        raise HTTPException(status_code=400, detail="cluster_id requerido")
    try:
        item = record_decision(
            BASE_DIR / "explain" / "risk_register.csv",
            BASE_DIR / "review",
            cluster_id,
            decision,
            reviewer,
            notes,
        )
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return item


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.server:app", host="0.0.0.0", port=8000, reload=False)