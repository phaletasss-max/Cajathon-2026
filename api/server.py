"""API HTTP de RIE-02 (Fase 6)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
import pandas as pd

from review.workflow import record_decision
from api.landing import LANDING_HTML
from api.platform import PLATFORM_HTML
from api.platform_data import ROOT, SAMPLE_RAW, case_graph, rerun_sample, summarize
from detection.engine import score_components

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


@app.get("/app", response_class=HTMLResponse)
@app.get("/app/panel", response_class=HTMLResponse)
@app.get("/app/alertas", response_class=HTMLResponse)
@app.get("/app/bitacora", response_class=HTMLResponse)
@app.get("/app/caso/{case_id}", response_class=HTMLResponse)
@app.get("/validacion", response_class=HTMLResponse)
@app.get("/metodologia", response_class=HTMLResponse)
@app.get("/privacidad", response_class=HTMLResponse)
def platform(case_id: str = "") -> str:
    return PLATFORM_HTML


@app.get("/platform/alerts")
def platform_alerts() -> dict[str, Any]:
    raw = SAMPLE_RAW if BASE_DIR.name == "sample_outputs" else Path(os.getenv("RIE_RAW_DIR", "data/raw"))
    path = raw / "applications.csv"
    applications = pd.read_csv(path, dtype=str, keep_default_na=False).to_dict("records") if path.exists() else []
    items = _read_csv("clusters.csv", "detection").to_dict("records")
    return {"alerts": summarize(items, applications), "audit_writable": not bool(os.getenv("VERCEL"))}


@app.get("/platform/cases/{cluster_id}")
def platform_case(cluster_id: str, k: int | None = Query(None, ge=2, le=50)) -> dict[str, Any]:
    if k is not None:
        result = rerun_sample(k, cluster_id)
        if result is None:
            raise HTTPException(status_code=404, detail="El caso no existe en esta ejecución.")
        return result
    details = cluster_detail(cluster_id)
    details.pop("markdown_path")
    cluster = details["cluster"]
    nodes = _read_csv("graph_nodes.csv", "graph")
    edges = _read_csv("graph_edges.csv", "graph")
    details["graph"] = case_graph(cluster, nodes, edges) if not nodes.empty and not edges.empty else {"nodes": [], "edges": []}
    for field in ("size", "density", "phone_edges", "device_edges", "address_edges", "reference_edges",
                  "burst_72h", "time_span_hours", "multi_app_persons", "far_applications", "max_weight"):
        cluster[field] = float(cluster[field])
    details["components"] = score_components(cluster, cluster["source"])
    return details


@app.post("/platform/analyze")
def platform_analyze(k: int = Query(25, ge=2, le=50)) -> dict[str, Any]:
    return rerun_sample(k)


@app.get("/platform/benchmark")
def platform_benchmark() -> Any:
    return json.loads((ROOT / "sample_outputs/eval/comparison.json").read_text(encoding="utf-8"))


def _audit_dir() -> Path:
    return Path(os.getenv("RIE_AUDIT_DIR", str(BASE_DIR / "review")))


@app.get("/platform/audit")
def platform_audit() -> dict[str, Any]:
    path = _audit_dir() / "decisions.jsonl"
    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()] if path.exists() else []
    return {"events": events, "writable": not bool(os.getenv("VERCEL"))}


@app.post("/platform/audit")
def write_platform_audit(payload: dict[str, Any]) -> dict[str, Any]:
    if os.getenv("VERCEL"):
        raise HTTPException(status_code=503, detail="El despliegue necesita almacenamiento persistente para registrar decisiones.")
    if any(not isinstance(payload.get(key), str) or not payload[key].strip() for key in ("cluster_id", "decision", "reviewer", "notes")):
        raise HTTPException(status_code=400, detail="Completa el resultado, el analista y las observaciones.")
    return review_decision(payload)


@app.get("/logo.jpg")
def logo() -> FileResponse:
    logo_path = Path("assets/redriesgo-logo.jpg")
    if not logo_path.exists():
        raise HTTPException(status_code=404, detail="logo no encontrado")
    return FileResponse(logo_path, media_type="image/jpeg")


@app.get("/assets/{filename}")
def asset_file(filename: str) -> FileResponse:
    allowed = {"redriesgo-logo.jpg", "arquitectura.jpg", "patrones-grafos.jpg"}
    if filename not in allowed:
        raise HTTPException(status_code=404, detail="recurso no encontrado")
    path = Path("assets") / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="recurso no encontrado")
    return FileResponse(path, media_type="image/jpeg")


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
    decisions_path = _audit_dir() / "decisions.jsonl"
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
            _audit_dir(),
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