"""Exportación reutilizable del grafo: GraphML, pickle, CSV y metadatos."""

from __future__ import annotations

import json
import pickle
from dataclasses import asdict
from pathlib import Path
from typing import Any

import networkx as nx

from graph.model import SCHEMA_VERSION, GraphBuildResult


def _graphml_value(value: Any) -> Any:
    """Convierte valores no soportados por GraphML a tipos escalares."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    if isinstance(value, (list, tuple, dict)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    if isinstance(value, (str, int, float)):
        return value
    return str(value)


def _sanitized_copy(graph: nx.Graph) -> nx.Graph:
    clean = nx.Graph()
    for node_id, attributes in graph.nodes(data=True):
        clean.add_node(
            str(node_id),
            **{key: _graphml_value(value) for key, value in attributes.items()},
        )
    for source, target, attributes in graph.edges(data=True):
        clean.add_edge(
            str(source),
            str(target),
            **{key: _graphml_value(value) for key, value in attributes.items()},
        )
    return clean


def export_graph(
    result: GraphBuildResult,
    output_dir: str | Path,
) -> dict[str, Path]:
    """Escribe el grafo en formatos reutilizables y devuelve las rutas."""
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}

    bipartite_path = target / "graph.graphml"
    projection_path = target / "projection.graphml"
    nx.write_graphml(_sanitized_copy(result.bipartite), bipartite_path, encoding="utf-8")
    nx.write_graphml(_sanitized_copy(result.projection), projection_path, encoding="utf-8")
    paths["bipartite_graphml"] = bipartite_path
    paths["projection_graphml"] = projection_path

    pickle_path = target / "graph.pkl"
    payload = {
        "schema_version": SCHEMA_VERSION,
        "config": asdict(result.config),
        "stats": result.stats,
        "bipartite": result.bipartite,
        "projection": result.projection,
        "edges": result.edges,
        "nodes": result.nodes,
        "attributes": result.attributes,
    }
    with pickle_path.open("wb") as handle:
        pickle.dump(payload, handle, protocol=pickle.HIGHEST_PROTOCOL)
    paths["pickle"] = pickle_path

    edge_path = target / "graph_edges.csv"
    node_path = target / "graph_nodes.csv"
    attribute_path = target / "graph_attributes.csv"
    result.edges.to_csv(edge_path, index=False, encoding="utf-8")
    result.nodes.to_csv(node_path, index=False, encoding="utf-8")
    result.attributes.to_csv(attribute_path, index=False, encoding="utf-8")
    paths["edges_csv"] = edge_path
    paths["nodes_csv"] = node_path
    paths["attributes_csv"] = attribute_path

    meta = {
        "schema_version": SCHEMA_VERSION,
        "config": asdict(result.config),
        "stats": result.stats,
        "counts": {
            "applications": result.n_applications,
            "entities": result.n_entities,
            "attributes": int(len(result.attributes)),
            "bipartite_nodes": result.bipartite.number_of_nodes(),
            "bipartite_edges": result.bipartite.number_of_edges(),
            "projection_nodes": result.projection.number_of_nodes(),
            "projection_edges": result.projection.number_of_edges(),
        },
        "files": {name: path.name for name, path in paths.items()},
    }
    meta_path = target / "graph_meta.json"
    meta_path.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    paths["meta"] = meta_path
    return paths
