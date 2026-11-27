"""Datos de la plataforma de revisión y análisis de la muestra pública."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

import pandas as pd

from detection.engine import run_detection, score_components
from explain.dossier import run_explain
from detection.model import DetectionConfig
from graph.builder import build_graph_from_dir
from graph.export import export_graph
from graph.model import GraphConfig

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_RAW = ROOT / "sample_data" / "raw"


def summarize(clusters, applications):
    indexed = {row["application_id"]: row for row in applications}
    for cluster in clusters:
        members = [indexed[item] for item in json.loads(cluster["members"]) if item in indexed]
        amounts = [float(row["amount_pen"]) for row in members if row.get("amount_pen")]
        dates = sorted(row["created_at"] for row in members if row.get("created_at"))
        cluster.update(
            exposure_pen=round(sum(amounts), 2) if amounts else None,
            evidence_count=len(json.loads(cluster["top_evidence"])),
            reasons=json.loads(cluster["reasons"]),
            channels=sorted({row["channel"] for row in members if row.get("channel")}),
            date_start=dates[0] if dates else None,
            date_end=dates[-1] if dates else None,
        )
    return clusters


def case_graph(cluster, nodes, edges):
    members = set(json.loads(cluster["members"]))
    bipartite = nodes[nodes.graph_layer == "bipartite"]
    selected = bipartite[bipartite.node_id.isin(members)]
    parties = set(selected.person_id) | set(selected.business_id)
    entities = members | (parties - {""})
    incident = edges[(edges.graph_layer == "bipartite") &
                     edges.source.isin(entities)]
    included = entities | set(incident.target)
    fields = ["node_id", "node_type", "attribute_type", "multiplicity", "created_at", "high_multiplicity"]
    links = incident[["source", "target", "weight", "edge_type"]].to_dict("records")
    for app in selected.itertuples(index=False):
        for identifier, relation in [(app.person_id, "solicitante"), (app.business_id, "negocio declarado")]:
            if identifier:
                links.append({"source": app.node_id, "target": identifier, "weight": None, "edge_type": relation})
    return {"nodes": bipartite[bipartite.node_id.isin(included)][fields].to_dict("records"), "edges": links}


def rerun_sample(k, case_id=None):
    started = perf_counter()
    with TemporaryDirectory() as directory:
        path = Path(directory)
        graph = build_graph_from_dir(SAMPLE_RAW, GraphConfig(max_multiplicity=k))
        export_graph(graph, path)
        detection_dir = path / "detection" if case_id else None
        detection = run_detection(path / "graph.pkl", SAMPLE_RAW, DetectionConfig(), detection_dir)
        if case_id:
            matched = detection.clusters[detection.clusters.cluster_id == case_id].to_dict("records")
            if not matched:
                return None
            cluster = matched[0]
            run_explain(detection_dir, path / "graph.pkl", SAMPLE_RAW, path / "explain", top=len(detection.clusters))
            dossiers = json.loads((path / "explain/dossiers.json").read_text(encoding="utf-8"))
            dossier = next(item for item in dossiers if item["cluster_id"] == case_id)
            return {"cluster": cluster, "dossier": dossier, "graph": case_graph(cluster, graph.nodes, graph.edges),
                    "components": score_components(cluster, cluster["source"]), "experimental": True}
        applications = pd.read_csv(SAMPLE_RAW / "applications.csv", dtype=str, keep_default_na=False)
        return {
            "k": k,
            "hubs": graph.stats["n_high_multiplicity_attributes"],
            "applications": len(detection.applications),
            "elapsed_seconds": round(perf_counter() - started, 2),
            "clusters": summarize(detection.clusters.to_dict("records"), applications.to_dict("records")),
        }
