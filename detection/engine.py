"""Motor de detección de redes de riesgo (Fase 3).

El motor es no supervisado: no lee ``data/ground_truth``. Usa el grafo de la
Fase 2 para encontrar comunidades densas, ciclos de referencias y ráfagas
temporales, y les asigna una puntuación de riesgo explicable.
"""

from __future__ import annotations

import argparse
import json
import math
import pickle
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

import networkx as nx
import pandas as pd

from detection.model import DetectionConfig, DetectionResult

CLUSTER_COLUMNS = [
    "cluster_id",
    "risk_score",
    "size",
    "n_edges",
    "density",
    "weight_total",
    "mean_weight",
    "max_weight",
    "phone_edges",
    "device_edges",
    "address_edges",
    "reference_edges",
    "burst_72h",
    "multi_app_persons",
    "far_applications",
    "time_span_hours",
    "source",
    "reasons",
    "top_evidence",
    "members",
]

APPLICATION_COLUMNS = [
    "application_id",
    "risk_score",
    "rank",
    "cluster_id",
    "cluster_score",
    "individual_score",
    "top_reason",
    "top_evidence",
]


def _load_graph(graph_path: Path) -> dict[str, Any]:
    with graph_path.open("rb") as handle:
        payload = pickle.load(handle)
    if "projection" not in payload or "edges" not in payload:
        raise ValueError("El pickle no contiene el grafo de proyección")
    return payload


def _load_raw(raw_dir: Path | None) -> dict[str, pd.DataFrame] | None:
    if raw_dir is None:
        return None
    required = [
        "applications",
        "persons",
        "addresses",
        "geocells",
        "references",
    ]
    tables: dict[str, pd.DataFrame] = {}
    for name in required:
        path = raw_dir / f"{name}.csv"
        if not path.exists():
            return None
        tables[name] = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8")
    return tables


def _parse_dt(value: object) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    from math import asin, cos, radians, sin, sqrt

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    h = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * 6371.0 * asin(sqrt(h))


def _build_context(graph_payload: dict[str, Any], raw: dict[str, pd.DataFrame] | None) -> dict[str, Any]:
    projection = graph_payload["projection"]
    edges = graph_payload["edges"]
    simple = nx.Graph()
    simple.add_nodes_from(node for node in projection.nodes() if not str(node).startswith("hub:"))
    for row in edges.itertuples(index=False):
        if row.graph_layer != "projection":
            continue
        if str(row.source).startswith("hub:") or str(row.target).startswith("hub:"):
            continue
        simple.add_edge(str(row.source), str(row.target), **{
            key: getattr(row, key) for key in edges.columns
            if key not in {"edge_id", "graph_layer", "source", "target"}
        })

    app_nodes = [node for node in simple.nodes() if not str(node).startswith("hub:")]
    app_date: dict[str, datetime] = {}
    app_person: dict[str, str] = {}
    person_apps: dict[str, list[str]] = defaultdict(list)
    raw_apps = pd.DataFrame()
    if raw is not None and "applications" in raw:
        raw_apps = raw["applications"]
        for row in raw_apps.itertuples(index=False):
            app_id = str(row.application_id)
            if app_id in simple:
                parsed = _parse_dt(row.created_at)
                if parsed is not None:
                    app_date[app_id] = parsed
                app_person[app_id] = str(row.person_id)
                person_apps[str(row.person_id)].append(app_id)

    far_apps: set[str] = set()
    if raw is not None:
        try:
            applications = raw["applications"]
            persons = raw["persons"]
            addresses = raw["addresses"]
            geocells = raw["geocells"]
            address_geocell = dict(zip(addresses["address_id"], addresses["geocell_id"]))
            person_home_geo = {}
            for person in persons.itertuples(index=False):
                person_home_geo[str(person.person_id)] = address_geocell.get(str(person.home_address_id), "")
            geo_coord = {
                str(row.geocell_id): (float(row.latitude), float(row.longitude))
                for row in geocells.itertuples(index=False)
            }
            for app in applications.itertuples(index=False):
                app_id = str(app.application_id)
                if app_id not in simple:
                    continue
                person_id = str(app.person_id)
                home_geo = person_home_geo.get(person_id, "")
                app_geo = str(app.application_geocell_id)
                if home_geo and app_geo and home_geo != app_geo and home_geo in geo_coord and app_geo in geo_coord:
                    distance = _distance_km(*geo_coord[home_geo], *geo_coord[app_geo])
                    if distance >= 500:
                        far_apps.add(app_id)
        except (KeyError, ValueError, TypeError):
            far_apps = set()

    weighted_degree: dict[str, float] = defaultdict(float)
    for u, v, data in simple.edges(data=True):
        weighted_degree[u] += float(data.get("weight", 0.0))
        weighted_degree[v] += float(data.get("weight", 0.0))

    return {
        "simple": simple,
        "app_date": app_date,
        "app_person": app_person,
        "person_apps": person_apps,
        "far_apps": far_apps,
        "weighted_degree": weighted_degree,
        "raw": raw,
    }


def _community_features(members: set[str], context: dict[str, Any], source: str) -> dict[str, Any]:
    simple = context["simple"]
    app_date = context["app_date"]
    app_person = context["app_person"]
    person_apps = context["person_apps"]
    far_apps = context["far_apps"]
    sub = simple.subgraph(members)
    types: Counter[str] = Counter()
    weights: list[float] = []
    spans: list[float] = []
    for u, v, data in sub.edges(data=True):
        weights.append(float(data.get("weight", 0.0)))
        spans.append(float(data.get("span_hours", 0.0)))
        try:
            evidence = json.loads(data.get("evidence_json", "[]"))
        except (json.JSONDecodeError, TypeError):
            evidence = []
        for item in evidence:
            types[str(item.get("type", ""))] += 1
    dates = sorted(context["app_date"][app] for app in members if app in context["app_date"])
    burst = 0
    if dates:
        left = 0
        for right in range(len(dates)):
            while (dates[right] - dates[left]).total_seconds() > 72 * 3600:
                left += 1
            burst = max(burst, right - left + 1)
    multi_app = sum(1 for app in members if len(person_apps.get(app_person.get(app, ""), [])) > 1)
    far_count = len(members & far_apps)
    time_span = (dates[-1] - dates[0]).total_seconds() / 3600.0 if len(dates) > 1 else 0.0
    return {
        "members": sorted(members),
        "size": len(members),
        "n_edges": sub.number_of_edges(),
        "density": nx.density(sub) if len(members) > 1 else 0.0,
        "weight_total": round(sum(weights), 6),
        "mean_weight": round(sum(weights) / len(weights), 6) if weights else 0.0,
        "max_weight": round(max(weights), 6) if weights else 0.0,
        "phone_edges": types.get("phone", 0),
        "device_edges": types.get("device", 0),
        "address_edges": types.get("address", 0),
        "reference_edges": types.get("reference", 0),
        "burst_72h": burst,
        "multi_app_persons": multi_app,
        "far_applications": far_count,
        "time_span_hours": round(time_span, 3),
        "source": source,
    }


def _score(features: dict[str, Any], source: str) -> float:
    size = int(features["size"])
    size_ok = 1.0 if 3 <= size <= 30 else (0.5 if size <= 60 else 0.0)
    density = float(features["density"])
    evidence = (
        features["phone_edges"]
        + features["device_edges"] * 1.25
        + features["reference_edges"] * 1.15
        + features["address_edges"] * (1.0 if features["burst_72h"] >= 5 else (0.65 if features["burst_72h"] >= 3 or density >= 0.7 else 0.0))
    )
    evidence_per_node = evidence / max(size - 1, 1)
    burst_ratio = features["burst_72h"] / max(size, 1)
    time_span = float(features["time_span_hours"])
    time_score = 1.0 if time_span <= 72 else (168.0 / time_span if time_span > 0 else 0.0)
    multi_score = features["multi_app_persons"] / max(size, 1)
    far_score = features["far_applications"] / max(size, 1)
    maxw = min(float(features["max_weight"]) / 12.0, 1.0)
    reference_ratio = min(features["reference_edges"] / max(size, 1), 1.0)
    base = 100.0 * (
        0.24 * size_ok + 0.19 * density + 0.14 * min(evidence_per_node, 2.0) / 2.0
        + 0.14 * burst_ratio + 0.09 * time_score + 0.09 * multi_score
        + 0.06 * far_score + 0.05 * maxw + 0.01 * reference_ratio
    )
    if source == "ref_scc":
        base = max(base, 75.0)
    if size <= 2:
        base = min(base, 45.0)
    if size > 40:
        base = min(base, 35.0)
    return round(min(max(base, 0.0), 100.0), 2)


def _candidate_clusters(context: dict[str, Any], config: DetectionConfig) -> list[tuple[set[str], dict[str, Any], str]]:
    simple = context["simple"]
    candidates: list[tuple[set[str], dict[str, Any], str]] = []

    # Comunidades de Louvain sobre la proyección sin hubs.
    try:
        communities = nx.community.louvain_communities(
            simple, weight="weight", resolution=config.resolution, seed=config.seed
        )
    except Exception:
        communities = [set(simple.nodes())]
    for community in communities:
        members = set(community) & set(simple.nodes())
        if config.min_cluster_size <= len(members) <= config.max_cluster_size:
            features = _community_features(members, context, "louvain")
            candidates.append((members, features, "louvain"))
        elif len(members) > config.max_cluster_size:
            sub = simple.subgraph(members)
            try:
                sub_comms = nx.community.louvain_communities(
                    sub, weight="weight", resolution=max(config.resolution * 2.5, 2.5), seed=config.seed
                )
            except Exception:
                sub_comms = []
            for sub_comm in sub_comms:
                sub_members = set(sub_comm) & members
                if config.min_cluster_size <= len(sub_members) <= config.max_cluster_size:
                    features = _community_features(sub_members, context, "louvain_sub")
                    if (
                        features["device_edges"] + features["phone_edges"] >= 2
                        or features["burst_72h"] >= 4
                        or features["far_applications"] >= 2
                    ):
                        candidates.append((sub_members, features, "louvain_sub"))

    # Ciclos cerrados de referencias: SCCs pequeñas del grafo dirigido persona -> referencia.
    raw = context["raw"]
    if raw is not None and "references" in raw and "applications" in raw:
        applications = raw["applications"]
        app_person = dict(zip(applications["application_id"], applications["person_id"]))
        person_apps: dict[str, list[str]] = defaultdict(list)
        for row in applications.itertuples(index=False):
            person_apps[str(row.person_id)].append(str(row.application_id))
        refs = raw["references"]
        digraph = nx.DiGraph()
        digraph.add_edges_from(
            (str(app_person.get(str(row.application_id), "")), str(row.ref_person_id))
            for row in refs.itertuples(index=False)
            if str(app_person.get(str(row.application_id), "")) and str(row.ref_person_id)
        )
        for component in nx.strongly_connected_components(digraph):
            component = set(component)
            if not (4 <= len(component) <= config.max_cluster_size):
                continue
            members: set[str] = set()
            for person in component:
                members.update(person_apps.get(person, []))
            members = {app for app in members if app in simple}
            if len(members) < config.min_cluster_size:
                continue
            features = _community_features(members, context, "ref_scc")
            candidates.append((members, features, "ref_scc"))

    # Deduplicación por Jaccard.
    ordered = sorted(candidates, key=lambda item: -_score(item[1], item[2]))
    merged: list[tuple[set[str], dict[str, Any], str]] = []
    for members, features, source in ordered:
        duplicate = False
        for existing_members, _, _ in merged:
            union = len(members | existing_members)
            if union and len(members & existing_members) / union >= 0.5:
                duplicate = True
                break
        if not duplicate:
            merged.append((members, features, source))
    return merged[: config.max_clusters]


def _top_evidence(members: set[str], context: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    simple = context["simple"]
    sub = simple.subgraph(members)
    counter: Counter[tuple[str, str]] = Counter()
    weight_map: dict[tuple[str, str], float] = {}
    df_map: dict[tuple[str, str], int] = {}
    for _, _, data in sub.edges(data=True):
        try:
            evidence = json.loads(data.get("evidence_json", "[]"))
        except (json.JSONDecodeError, TypeError):
            evidence = []
        for item in evidence:
            key = (str(item.get("type", "")), str(item.get("value_hash", "")))
            counter[key] += 1
            weight_map[key] = float(item.get("weight", 0.0))
            df_map[key] = int(item.get("df", 0))
    ordered = sorted(counter, key=lambda key: (counter[key] * weight_map[key], counter[key]), reverse=True)
    result = []
    for key in ordered[:limit]:
        result.append({
            "type": key[0],
            "value_hash": key[1],
            "weight": round(weight_map[key], 6),
            "df": df_map[key],
            "shared_by_applications": counter[key],
        })
    return result


def _reasons(features: dict[str, Any], source: str) -> list[str]:
    reasons: list[str] = []
    size = int(features["size"])
    if features["device_edges"] >= max(1, size // 3):
        reasons.append(f"Dispositivo compartido en {features['device_edges']} aristas")
    if features["phone_edges"] >= max(1, size // 3):
        reasons.append(f"Teléfono compartido en {features['phone_edges']} aristas")
    if features["address_edges"] > 0 and features["burst_72h"] >= max(3, size // 2):
        reasons.append(
            f"Ráfaga temporal: {features['burst_72h']} solicitudes en <=72 h con dirección compartida"
        )
    if source == "ref_scc":
        reasons.append(f"Ciclo cerrado de referencias entre {size} personas")
    if features["reference_edges"] >= max(1, size // 2) and source != "ref_scc":
        reasons.append(f"Referencias compartidas en {features['reference_edges']} aristas")
    if features["multi_app_persons"] > 0:
        reasons.append(f"{features['multi_app_persons']} personas con solicitudes en geoceldas incompatibles")
    if features["far_applications"] > 0:
        reasons.append(f"{features['far_applications']} solicitudes a >=500 km del domicilio")
    if features["density"] >= 0.8 and size >= 3:
        reasons.append(f"Comunidad densa: {features['n_edges']} aristas entre {size} solicitudes")
    if features["time_span_hours"] <= 168 and size >= 3:
        reasons.append(f"Ventana temporal compacta: {features['time_span_hours']:.0f} h")
    if features["max_weight"] >= 10:
        reasons.append(f"Atributo de alto peso compartido (peso {features['max_weight']:.1f})")
    if not reasons:
        reasons.append("Señales débiles; revisión preventiva")
    return reasons[:6]


def run_detection(
    graph_path: str | Path,
    raw_dir: str | Path | None = None,
    config: DetectionConfig | None = None,
    output_dir: str | Path | None = None,
) -> DetectionResult:
    started = time.perf_counter()
    config = config or DetectionConfig()
    graph_path = Path(graph_path)
    payload = _load_graph(graph_path)
    context = _build_context(payload, _load_raw(Path(raw_dir) if raw_dir is not None else None))

    merged = _candidate_clusters(context, config)
    cluster_rows: list[dict[str, Any]] = []
    for index, (members, features, source) in enumerate(merged, start=1):
        score = _score(features, source)
        if score < config.threshold:
            continue
        evidence = _top_evidence(members, context, config.top_evidence)
        cluster_rows.append({
            "cluster_id": f"C{index:05d}",
            "risk_score": score,
            "size": features["size"],
            "n_edges": features["n_edges"],
            "density": round(float(features["density"]), 6),
            "weight_total": features["weight_total"],
            "mean_weight": features["mean_weight"],
            "max_weight": features["max_weight"],
            "phone_edges": features["phone_edges"],
            "device_edges": features["device_edges"],
            "address_edges": features["address_edges"],
            "reference_edges": features["reference_edges"],
            "burst_72h": features["burst_72h"],
            "multi_app_persons": features["multi_app_persons"],
            "far_applications": features["far_applications"],
            "time_span_hours": features["time_span_hours"],
            "source": source,
            "reasons": json.dumps(_reasons(features, source), ensure_ascii=False),
            "top_evidence": json.dumps(evidence, ensure_ascii=False),
            "members": json.dumps(sorted(members), ensure_ascii=False),
        })

    clusters = pd.DataFrame(cluster_rows, columns=CLUSTER_COLUMNS)
    if not clusters.empty:
        clusters = clusters.sort_values(
            ["risk_score", "size", "cluster_id"], ascending=[False, False, True]
        ).reset_index(drop=True)
        clusters["cluster_id"] = [f"C{index:05d}" for index in range(1, len(clusters) + 1)]

    # Puntuación por solicitud.
    app_cluster: dict[str, tuple[str, float]] = {}
    for row in clusters.itertuples(index=False):
        for member in json.loads(row.members):
            current = app_cluster.get(member)
            if current is None or row.risk_score > current[1] or (
                row.risk_score == current[1] and int(row.size) < int(
                    clusters.loc[clusters.cluster_id == current[0], "size"].iloc[0]
                )
            ):
                app_cluster[member] = (str(row.cluster_id), float(row.risk_score))

    weighted_degree = context["weighted_degree"]
    if weighted_degree:
        values = list(weighted_degree.values())
        minimum = min(values)
        maximum = max(values)
        span = maximum - minimum if maximum > minimum else 1.0
        individual = {
            app: round(100.0 * (degree - minimum) / span, 2)
            for app, degree in weighted_degree.items()
        }
    else:
        individual = {}

    application_rows: list[dict[str, Any]] = []
    all_apps = sorted(context["simple"].nodes())
    for app in all_apps:
        cluster_id, cluster_score = app_cluster.get(app, ("", 0.0))
        ind_score = individual.get(app, 0.0)
        risk_score = max(cluster_score, round(0.2 * ind_score, 2))
        if cluster_id:
            cluster_row = clusters.loc[clusters.cluster_id == cluster_id].iloc[0]
            top_reason = json.loads(cluster_row["reasons"])[0]
            top_evidence = cluster_row["top_evidence"]
        else:
            top_reason = "Sin cluster de riesgo"
            top_evidence = "[]"
        application_rows.append({
            "application_id": app,
            "risk_score": risk_score,
            "cluster_id": cluster_id,
            "cluster_score": cluster_score,
            "individual_score": ind_score,
            "top_reason": top_reason,
            "top_evidence": top_evidence,
        })

    applications = pd.DataFrame(application_rows, columns=APPLICATION_COLUMNS[:-1] + ["top_evidence"])
    # Reordenar columnas exactas.
    applications = applications[
        ["application_id", "risk_score", "cluster_id", "cluster_score", "individual_score", "top_reason", "top_evidence"]
    ]
    applications = applications.sort_values(
        ["risk_score", "cluster_score", "application_id"], ascending=[False, False, True]
    ).reset_index(drop=True)
    applications.insert(1, "rank", range(1, len(applications) + 1))
    applications = applications[
        ["application_id", "risk_score", "rank", "cluster_id", "cluster_score", "individual_score", "top_reason", "top_evidence"]
    ]

    elapsed = round(time.perf_counter() - started, 4)
    stats = {
        "n_applications": len(all_apps),
        "n_clusters": len(clusters),
        "n_risk_applications": int((applications["risk_score"] >= config.threshold).sum()),
        "n_clustered_applications": int(applications["cluster_id"].astype(bool).sum()),
        "threshold": config.threshold,
        "resolution": config.resolution,
        "elapsed_seconds": elapsed,
    }

    result = DetectionResult(
        clusters=clusters,
        applications=applications,
        config=config,
        elapsed_seconds=elapsed,
        stats=stats,
    )

    if output_dir is not None:
        _export(result, Path(output_dir))
    return result


def _export(result: DetectionResult, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    result.clusters.to_csv(output_dir / "clusters.csv", index=False, encoding="utf-8")
    result.applications.to_csv(output_dir / "application_scores.csv", index=False, encoding="utf-8")
    meta = {
        "schema_version": "3.0",
        "config": {
            "threshold": result.config.threshold,
            "resolution": result.config.resolution,
            "min_cluster_size": result.config.min_cluster_size,
            "max_cluster_size": result.config.max_cluster_size,
            "seed": result.config.seed,
        },
        "stats": result.stats,
        "files": {
            "clusters": "clusters.csv",
            "application_scores": "application_scores.csv",
        },
    }
    (output_dir / "detection_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Detecta redes de riesgo sobre el grafo")
    parser.add_argument("--graph", type=Path, default=Path("outputs/graph/graph.pkl"))
    parser.add_argument("--raw", type=Path, default=Path("data/raw"))
    parser.add_argument("--output", type=Path, default=Path("outputs/detection"))
    parser.add_argument("--threshold", type=float, default=60.0)
    parser.add_argument("--resolution", type=float, default=1.0)
    parser.add_argument("--min-cluster-size", type=int, default=2)
    parser.add_argument("--max-cluster-size", type=int, default=60)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)

    config = DetectionConfig(
        threshold=args.threshold,
        resolution=args.resolution,
        min_cluster_size=args.min_cluster_size,
        max_cluster_size=args.max_cluster_size,
        seed=args.seed,
    )
    result = run_detection(args.graph, args.raw, config, args.output)
    print(json.dumps(result.stats, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
