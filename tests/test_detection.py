"""Pruebas de la Fase 3: detección de redes de riesgo."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd

from data.generator import generate_dataset
from detection.engine import run_detection
from detection.model import DetectionConfig


def test_detection_finds_risk_clusters(tmp_path: Path) -> None:
    generate_dataset(n_legit=1200, n_rings=12, seed=23, out_dir=tmp_path, difficulty="medium")
    raw_dir = tmp_path / "raw"
    graph_path = tmp_path / "graph" / "graph.pkl"
    from graph.builder import build_graph_from_dir
    from graph.export import export_graph

    result = build_graph_from_dir(raw_dir)
    export_graph(result, tmp_path / "graph")

    started = time.perf_counter()
    detection = run_detection(graph_path, raw_dir, DetectionConfig(threshold=60.0), tmp_path / "detection")
    elapsed = time.perf_counter() - started

    assert (tmp_path / "detection" / "clusters.csv").exists()
    assert (tmp_path / "detection" / "application_scores.csv").exists()
    assert (tmp_path / "detection" / "detection_meta.json").exists()
    assert len(detection.clusters) > 0
    assert len(detection.applications) >= 1200
    assert detection.applications["risk_score"].is_monotonic_decreasing
    assert detection.clusters["risk_score"].min() >= 60.0
    assert detection.stats["elapsed_seconds"] < 30.0
    assert elapsed < 60.0
    meta = json.loads((tmp_path / "detection" / "detection_meta.json").read_text(encoding="utf-8"))
    assert meta["stats"]["n_clusters"] == len(detection.clusters)


def test_detection_runs_without_raw_tables(tmp_path: Path) -> None:
    generate_dataset(n_legit=300, n_rings=5, seed=9, out_dir=tmp_path, difficulty="easy")
    raw_dir = tmp_path / "raw"
    from graph.builder import build_graph_from_dir
    from graph.export import export_graph

    graph_result = build_graph_from_dir(raw_dir)
    export_graph(graph_result, tmp_path / "graph")
    detection = run_detection(
        tmp_path / "graph" / "graph.pkl",
        None,
        None,
        tmp_path / "detection",
    )
    assert len(detection.applications) >= 300
    assert detection.clusters is not None