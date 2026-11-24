"""Pipeline completo RIE-02: datos -> grafo -> detección -> expedientes -> evaluación."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import argparse
import json
import time
from pathlib import Path

from data.generator import generate_dataset
from detection.engine import run_detection
from detection.model import DetectionConfig
from eval.evaluate import main as evaluate_main
from explain.dossier import run_explain
from graph.builder import build_graph_from_dir
from graph.export import export_graph


def run_pipeline(
    n_legit: int = 5000,
    n_rings: int = 25,
    seed: int = 42,
    difficulty: str = "medium",
    out_data: Path | None = None,
) -> dict[str, object]:
    started = time.perf_counter()
    out_data = out_data or Path("data")
    raw_dir = out_data / "raw"
    graph_dir = Path("outputs/graph")
    detection_dir = Path("outputs/detection")
    explain_dir = Path("outputs/explain")
    eval_dir = Path("outputs/eval")

    generate_dataset(n_legit=n_legit, n_rings=n_rings, seed=seed, out_dir=out_data, difficulty=difficulty)
    graph_result = build_graph_from_dir(raw_dir)
    export_graph(graph_result, graph_dir)
    detection = run_detection(graph_dir / "graph.pkl", raw_dir, DetectionConfig(threshold=60.0), detection_dir)
    run_explain(detection_dir, graph_dir / "graph.pkl", raw_dir, explain_dir, top=min(50, len(detection.clusters)))
    evaluate_main(["--detection", str(detection_dir), "--truth", str(out_data / "ground_truth"), "--output", str(eval_dir)])

    elapsed = round(time.perf_counter() - started, 2)
    summary = {
        "n_legit": n_legit,
        "n_rings": n_rings,
        "difficulty": difficulty,
        "seed": seed,
        "n_applications": len(detection.applications),
        "n_clusters": len(detection.clusters),
        "n_risk_applications": detection.stats["n_risk_applications"],
        "elapsed_seconds": elapsed,
    }
    Path("outputs/pipeline_meta.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ejecuta el pipeline completo de RIE-02")
    parser.add_argument("--n-legit", type=int, default=5000)
    parser.add_argument("--rings", type=int, default=25)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--difficulty", choices=["easy", "medium", "hard"], default="medium")
    parser.add_argument("--out-data", type=Path, default=Path("data"))
    args = parser.parse_args(argv)
    run_pipeline(args.n_legit, args.rings, args.seed, args.difficulty, args.out_data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())