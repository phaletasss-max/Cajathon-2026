"""Evaluación offline de la detección (usa verdad terreno solo aquí)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from eval.metrics import application_metrics, cluster_metrics


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evalúa la detección contra la verdad terreno")
    parser.add_argument("--detection", type=Path, default=Path("outputs/detection"))
    parser.add_argument("--truth", type=Path, default=Path("data/ground_truth"))
    parser.add_argument("--output", type=Path, default=Path("outputs/eval"))
    args = parser.parse_args(argv)

    scores = pd.read_csv(args.detection / "application_scores.csv", dtype=str, keep_default_na=False)
    scores["risk_score"] = scores["risk_score"].astype(float)
    clusters = pd.read_csv(args.detection / "clusters.csv", dtype=str, keep_default_na=False)
    truth = pd.read_csv(args.truth / "ground_truth.csv", dtype=str, keep_default_na=False)

    metrics = {
        "application": application_metrics(scores, truth),
        "cluster": cluster_metrics(clusters, truth),
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(metrics["application"], ensure_ascii=False, indent=2))
    print(json.dumps({k: v for k, v in metrics["cluster"].items() if k != "cluster_details"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
PY