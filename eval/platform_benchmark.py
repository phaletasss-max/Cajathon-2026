"""Evaluación reproducible de reglas de contacto y motor de grafos."""

import argparse
import json
from tempfile import TemporaryDirectory
from pathlib import Path

import pandas as pd

from eval.benchmark import _run_one
from detection.engine import run_detection
from detection.model import DetectionConfig
from graph.builder import build_graph_from_dir
from graph.export import export_graph
from graph.model import GraphConfig


def measurements(predicted, positives, total):
    tp = len(predicted & positives)
    fp = len(predicted - positives)
    fn = len(positives - predicted)
    tn = total - tp - fp - fn
    return dict(tp=tp, fp=fp, fn=fn, tn=tn,
                precision=tp / max(tp + fp, 1), recall=tp / max(tp + fn, 1),
                fpr=fp / max(fp + tn, 1), review_minutes=2 * (tp + fp))


def precision_recall(scored, positives):
    counts = scored.assign(positive=scored.application_id.isin(positives)).groupby("risk_score").positive.agg(["size", "sum"]).sort_index(ascending=False)
    seen = counts["size"].cumsum()
    found = counts["sum"].cumsum()
    return [[0, 1], *[[round(recall, 5), round(precision, 5)]
                       for recall, precision in zip(found / max(len(positives), 1), found / seen)]]


def ablation():
    root = Path(__file__).resolve().parents[1] / "sample_data"
    truth = pd.read_csv(root / "ground_truth/ground_truth.csv", dtype=str)
    positives = set(truth.application_id)
    variants = {
        "Motor completo": (GraphConfig(), DetectionConfig()),
        "Peso uniforme sin IDF": (GraphConfig(use_idf=False), DetectionConfig()),
        "Sin agrupación por hubs": (GraphConfig(max_multiplicity=10000), DetectionConfig()),
        "Sin puntos temporales": (GraphConfig(), DetectionConfig(use_temporal_score=False)),
    }
    result = {}
    with TemporaryDirectory() as directory:
        path = Path(directory)
        for label, (graph_config, detection_config) in variants.items():
            export_graph(build_graph_from_dir(root / "raw", graph_config), path)
            scores = run_detection(path / "graph.pkl", root / "raw", detection_config).applications
            predicted = set(scores.loc[scores.risk_score >= 60, "application_id"])
            result[label] = measurements(predicted, positives, len(scores))
    return result


def comparison(directory, difficulty, rings, population, summary=None):
    if summary is None:
        summary = _run_one(directory, population, rings, difficulty, 42)
    raw = pd.read_csv(directory / "raw/applications.csv", dtype=str, keep_default_na=False)
    truth = pd.read_csv(directory / "ground_truth/ground_truth.csv", dtype=str)
    scores = pd.read_csv(directory / "detection/application_scores.csv")
    positives = set(truth.application_id)
    flagged = pd.Series(False, index=raw.index)
    for field in ("device_id", "phone_id"):
        flagged |= raw[field].ne("") & raw[field].duplicated(keep=False)
    baseline = set(raw.loc[flagged, "application_id"])
    redriesgo = set(scores.loc[scores.risk_score >= 60, "application_id"])
    return {
        **summary,
        "baseline": measurements(baseline, positives, len(raw)),
        "redriesgo": measurements(redriesgo, positives, len(raw)),
        "pr": {
            "baseline": precision_recall(raw.assign(risk_score=flagged.astype(int)), positives),
            "redriesgo": precision_recall(scores, positives),
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, default=Path("outputs/comparison"))
    parser.add_argument("--output", type=Path, default=Path("sample_outputs/eval/comparison.json"))
    parser.add_argument("--population", type=int, default=5000)
    args = parser.parse_args()
    results = {}
    for key in ("easy", "medium", "hard", "low"):
        results[key] = comparison(args.work / key, "hard" if key == "low" else key,
                                  max(1, args.population // (1000 if key == "low" else 200)),
                                  args.population)
        print(key, results[key]["n_applications"], flush=True)
    results["ablation"] = ablation()
    args.output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
