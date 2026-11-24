"""Generación de expedientes explicables (Fase 4)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

def _mask_value(value: str, keep: int = 4) -> str:
    value = str(value or "").strip()
    if not value:
        return ""
    if len(value) <= keep:
        return "*" * len(value)
    return "*" * (len(value) - keep) + value[-keep:]


def _load_tables(raw_dir: Path | None) -> dict[str, pd.DataFrame]:
    if raw_dir is None:
        return {}
    names = ["applications", "persons", "addresses", "phones", "devices", "geocells"]
    tables: dict[str, pd.DataFrame] = {}
    for name in names:
        path = raw_dir / f"{name}.csv"
        if path.exists():
            tables[name] = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8")
    return tables


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    from math import asin, cos, radians, sin, sqrt

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    h = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * 6371.0 * asin(sqrt(h))


def _member_row(app_id: str, tables: dict[str, pd.DataFrame]) -> dict[str, Any]:
    applications = tables.get("applications", pd.DataFrame())
    persons = tables.get("persons", pd.DataFrame())
    addresses = tables.get("addresses", pd.DataFrame())
    phones = tables.get("phones", pd.DataFrame())
    devices = tables.get("devices", pd.DataFrame())
    geocells = tables.get("geocells", pd.DataFrame())

    app_row = applications[applications["application_id"] == app_id]
    app = app_row.iloc[0].to_dict() if not app_row.empty else {}
    person_row = persons[persons["person_id"] == str(app.get("person_id", ""))]
    person = person_row.iloc[0].to_dict() if not person_row.empty else {}

    home_address_id = str(person.get("home_address_id", ""))
    declared_address_id = str(app.get("declared_address_id", ""))
    home_address = addresses[addresses["address_id"] == home_address_id]
    declared_address = addresses[addresses["address_id"] == declared_address_id]
    home_geo = str(home_address.iloc[0]["geocell_id"]) if not home_address.empty else ""
    declared_geo = str(declared_address.iloc[0]["geocell_id"]) if not declared_address.empty else ""
    app_geo = str(app.get("application_geocell_id", ""))

    def _geocell_label(geocell_id: str) -> str:
        if not geocell_id or geocells.empty:
            return geocell_id
        row = geocells[geocells["geocell_id"] == geocell_id]
        if row.empty:
            return geocell_id
        return f"{row.iloc[0]['district']} ({row.iloc[0]['province']})"

    distance = None
    if home_geo and app_geo and home_geo != app_geo and not geocells.empty:
        home_cell = geocells[geocells["geocell_id"] == home_geo]
        app_cell = geocells[geocells["geocell_id"] == app_geo]
        if not home_cell.empty and not app_cell.empty:
            distance = round(_distance_km(
                float(home_cell.iloc[0]["latitude"]), float(home_cell.iloc[0]["longitude"]),
                float(app_cell.iloc[0]["latitude"]), float(app_cell.iloc[0]["longitude"]),
            ), 1)

    phone_id = str(app.get("phone_id", person.get("primary_phone_id", "")))
    device_id = str(app.get("device_id", person.get("primary_device_id", "")))
    phone_row = phones[phones["phone_id"] == phone_id]
    device_row = devices[devices["device_id"] == device_id]

    return {
        "application_id": app_id,
        "person_id": str(app.get("person_id", "")),
        "created_at": str(app.get("created_at", "")),
        "amount_pen": str(app.get("amount_pen", "")),
        "channel": str(app.get("channel", "")),
        "product": str(app.get("product", "")),
        "home_geocell": home_geo,
        "home_geocell_label": _geocell_label(home_geo),
        "declared_address_geocell": declared_geo,
        "declared_address_geocell_label": _geocell_label(declared_geo),
        "application_geocell": app_geo,
        "application_geocell_label": _geocell_label(app_geo),
        "distance_km": distance,
        "phone_masked": _mask_value(str(phone_row.iloc[0]["phone_number"]) if not phone_row.empty else phone_id),
        "device_masked": _mask_value(str(device_row.iloc[0]["device_fingerprint"]) if not device_row.empty else device_id, 6),
        "doc_masked": _mask_value(str(person.get("doc_number", ""))),
    }


def _cluster_dossier(cluster: pd.Series, tables: dict[str, pd.DataFrame], graph_context: dict[str, Any]) -> dict[str, Any]:
    members = json.loads(cluster["members"])
    member_rows = [_member_row(app_id, tables) for app_id in members]
    created = [row["created_at"] for row in member_rows if row["created_at"]]
    parsed = [pd.to_datetime(value, errors="coerce") for value in created]
    parsed = [value for value in parsed if pd.notna(value)]
    time_window = {
        "min": min(created) if created else "",
        "max": max(created) if created else "",
        "span_hours": round((max(parsed) - min(parsed)).total_seconds() / 3600.0, 2) if len(parsed) > 1 else 0.0,
    }
    reasons = json.loads(cluster["reasons"])
    evidence = json.loads(cluster["top_evidence"])
    return {
        "cluster_id": str(cluster["cluster_id"]),
        "risk_score": float(cluster["risk_score"]),
        "size": int(cluster["size"]),
        "source": str(cluster["source"]),
        "summary": reasons[0] if reasons else "Red de riesgo detectada",
        "reasons": reasons,
        "time_window": time_window,
        "shared_attributes": evidence,
        "graph_context": graph_context,
        "members": member_rows,
        "privacy_note": "Datos sintéticos; documentos, teléfonos y huellas enmascarados. La evidencia usa valores hasheados.",
    }


def _markdown(dossier: dict[str, Any]) -> str:
    lines = [
        f"# Expediente {dossier['cluster_id']}",
        "",
        f"- **Puntuación de riesgo:** {dossier['risk_score']}",
        f"- **Tamaño de la red:** {dossier['size']} solicitudes",
        f"- **Origen de detección:** {dossier['source']}",
        f"- **Resumen:** {dossier['summary']}",
        "",
        "## Motivos",
    ]
    for reason in dossier["reasons"]:
        lines.append(f"- {reason}")
    lines.extend([
        "",
        "## Ventana temporal",
        f"- Inicio: {dossier['time_window']['min']}",
        f"- Fin: {dossier['time_window']['max']}",
        f"- Duración: {dossier['time_window']['span_hours']} h",
        "",
        "## Atributos compartidos (evidencia)",
    ])
    for item in dossier["shared_attributes"]:
        lines.append(
            f"- `{item['type']}` hash `{item['value_hash']}` — peso {item['weight']}, "
            f"compartido por {item['shared_by_applications']} solicitudes (df {item['df']})"
        )
    lines.extend([
        "",
        "## Contexto del grafo",
        f"- Aristas: {dossier['graph_context'].get('n_edges', '')}",
        f"- Densidad: {dossier['graph_context'].get('density', '')}",
        f"- Peso máximo de arista: {dossier['graph_context'].get('max_weight', '')}",
        "",
        "## Solicitudes de la red",
        "",
        "| Solicitud | Fecha | Monto | Geocelda solicitud | Distancia km | Teléfono | Documento |",
        "|---|---:|---:|---|---:|---|---|",
    ])
    for member in dossier["members"]:
        lines.append(
            f"| {member['application_id'][:12]}… | {member['created_at']} | {member['amount_pen']} | "
            f"{member['application_geocell_label']} | {member['distance_km']} | {member['phone_masked']} | {member['doc_masked']} |"
        )
    lines.extend(["", dossier["privacy_note"], ""])
    return "\n".join(lines)


def run_explain(
    detection_dir: str | Path,
    graph_path: str | Path | None = None,
    raw_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    top: int = 50,
) -> dict[str, Any]:
    detection_dir = Path(detection_dir)
    clusters = pd.read_csv(detection_dir / "clusters.csv", dtype=str, keep_default_na=False)
    clusters["risk_score"] = clusters["risk_score"].astype(float)
    clusters["size"] = clusters["size"].astype(int)
    clusters = clusters.sort_values("risk_score", ascending=False).head(top).reset_index(drop=True)

    tables = _load_tables(Path(raw_dir) if raw_dir is not None else None)
    graph_context_by_cluster: dict[str, dict[str, Any]] = {}
    if graph_path is not None and Path(graph_path).exists():
        import pickle

        payload = pickle.load(Path(graph_path).open("rb"))
        edges = payload["edges"]
        # Contexto agregado simple por cluster se calcula desde el CSV de detección.
        _ = edges

    dossiers: list[dict[str, Any]] = []
    for row in clusters.itertuples(index=False):
        cluster_series = pd.Series(row._asdict())
        graph_context = {
            "n_edges": int(row.size * (row.size - 1) / 2) if False else None,
            "density": float(row.density) if hasattr(row, "density") else None,
            "max_weight": float(row.max_weight),
        }
        # Mejor: usar campos del cluster.
        graph_context = {
            "n_edges": int(clusters.loc[clusters.cluster_id == row.cluster_id, "n_edges"].iloc[0]) if "n_edges" in clusters.columns else None,
            "density": float(clusters.loc[clusters.cluster_id == row.cluster_id, "density"].iloc[0]) if "density" in clusters.columns else None,
            "max_weight": float(row.max_weight),
            "weight_total": float(row.weight_total),
        }
        dossier = _cluster_dossier(cluster_series, tables, graph_context)
        dossiers.append(dossier)

    output = Path(output_dir) if output_dir is not None else Path("outputs/explain")
    output.mkdir(parents=True, exist_ok=True)
    (output / "dossiers.json").write_text(
        json.dumps(dossiers, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    for dossier in dossiers:
        (output / f"dossier_{dossier['cluster_id']}.md").write_text(
            _markdown(dossier), encoding="utf-8"
        )

    # Registro resumido para revisión humana (Fase 5).
    register = pd.DataFrame([
        {
            "cluster_id": dossier["cluster_id"],
            "risk_score": dossier["risk_score"],
            "size": dossier["size"],
            "summary": dossier["summary"],
            "members": len(dossier["members"]),
            "file": f"dossier_{dossier['cluster_id']}.md",
        }
        for dossier in dossiers
    ])
    register.to_csv(output / "risk_register.csv", index=False, encoding="utf-8")

    meta = {
        "schema_version": "4.0",
        "n_dossiers": len(dossiers),
        "top": top,
        "files": {
            "dossiers": "dossiers.json",
            "risk_register": "risk_register.csv",
            "markdown": "dossier_C*.md",
        },
    }
    (output / "explain_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return {"dossiers": dossiers, "meta": meta}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Genera expedientes explicables de redes detectadas")
    parser.add_argument("--detection", type=Path, default=Path("outputs/detection"))
    parser.add_argument("--graph", type=Path, default=Path("outputs/graph/graph.pkl"))
    parser.add_argument("--raw", type=Path, default=Path("data/raw"))
    parser.add_argument("--output", type=Path, default=Path("outputs/explain"))
    parser.add_argument("--top", type=int, default=50)
    args = parser.parse_args(argv)

    result = run_explain(args.detection, args.graph, args.raw, args.output, args.top)
    print(json.dumps(result["meta"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())