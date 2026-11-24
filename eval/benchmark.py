"""Benchmark de detección por dificultad (Fase 8)."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import pandas as pd

from data.generator import generate_dataset
from detection.engine import run_detection
from detection.model import DetectionConfig
from eval.metrics import application_metrics, cluster_metrics
from graph.builder import build_graph_from_dir
from graph.export import export_graph


def _run_one(out_dir: Path, n_legit: int, n_rings: int, difficulty: str, seed: int) -> dict[str, Any]:
    started = time.perf_counter()
    generate_dataset(n_legit=n_legit, n_rings=n_rings, seed=seed, out_dir=out_dir, difficulty=difficulty)
    raw_dir = out_dir / "raw"
    graph_dir = out_dir / "graph"
    graph_result = build_graph_from_dir(raw_dir)
    export_graph(graph_result, graph_dir)
    detection_dir = out_dir / "detection"
    detection = run_detection(graph_dir / "graph.pkl", raw_dir, DetectionConfig(threshold=60.0), detection_dir)
    scores = pd.read_csv(detection_dir / "application_scores.csv", dtype=str, keep_default_na=False)
    scores["risk_score"] = scores["risk_score"].astype(float)
    clusters = pd.read_csv(detection_dir / "clusters.csv", dtype=str, keep_default_na=False)
    truth = pd.read_csv(out_dir / "ground_truth" / "ground_truth.csv", dtype=str, keep_default_na=False)
    app_metrics = application_metrics(scores, truth)
    cl_metrics = cluster_metrics(clusters, truth)
    return {
        "difficulty": difficulty,
        "n_legit": n_legit,
        "n_rings": n_rings,
        "prevalence_per_1000": round(1000 * n_rings / n_legit, 3),
        "n_applications": int(len(scores)),
        "n_clusters": int(len(clusters)),
        "captured_rings": int(cl_metrics["captured_rings"]),
        "ring_recall": cl_metrics["ring_recall"],
        "average_precision": app_metrics["average_precision"],
        "roc_auc": app_metrics["roc_auc"],
        "top100_precision": app_metrics.get("top100_precision"),
        "top100_recall": app_metrics.get("top100_recall"),
        "elapsed_seconds": round(time.perf_counter() - started, 2),
    }


def run_benchmark(
    n_legit: int = 2000,
    seed: int = 42,
    difficulties: list[str] | None = None,
    low_prevalence_rings: int = 5,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    difficulties = difficulties or ["easy", "medium", "hard"]
    output_dir = output_dir or Path("outputs/benchmark")
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for difficulty in difficulties:
        rows.append(_run_one(output_dir / f"{difficulty}", n_legit, max(1, int(0.005 * n_legit)), difficulty, seed))
    rows.append(_run_one(output_dir / "low_prevalence", n_legit, low_prevalence_rings, "hard", seed))
    rows[-1]["difficulty"] = "hard (baja prevalencia)"
    result = {"n_legit": n_legit, "seed": seed, "results": rows}
    (output_dir / "benchmark.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Benchmark de detección RIE-02",
        "",
        f"Cartera base: {n_legit} personas legítimas, semilla {seed}.",
        "",
        "| Escenario | Anillos | AP | AUC | Clusters | Anillos capturados | Recall |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['difficulty']} | {row['n_rings']} | {row['average_precision']} | {row['roc_auc']} | "
            f"{row['n_clusters']} | {row['captured_rings']} | {row['ring_recall']} |"
        )
    lines.extend([
        "",
        "Los escenarios easy/medium/hard usan 5 anillos por 1.000 personas. "
        "El escenario de baja prevalencia usa 5 anillos por toda la cartera.",
        "",
    ])
    (output_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Benchmark de detección por dificultad")
    parser.add_argument("--n-legit", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=Path("outputs/benchmark"))
    parser.add_argument("--difficulties", nargs="*", default=["easy", "medium", "hard"])
    parser.add_argument("--low-prevalence-rings", type=int, default=5)
    args = parser.parse_args(argv)
    result = run_benchmark(
        n_legit=args.n_legit,
        seed=args.seed,
        difficulties=args.difficulties,
        low_prevalence_rings=args.low_prevalence_rings,
        output_dir=args.output,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())