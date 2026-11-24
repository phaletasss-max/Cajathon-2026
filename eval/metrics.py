"""Métricas de evaluación offline (solo para medir, no para el motor)."""

from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd


def _average_precision_score(y_true: np.ndarray, y_score: np.ndarray) -> float:
    y_true = np.asarray(y_true).astype(int)
    y_score = np.asarray(y_score, dtype=float)
    positives = int(y_true.sum())
    if positives == 0:
        return 0.0
    order = np.argsort(-y_score, kind="mergesort")
    y_sorted = y_true[order]
    true_positions = np.flatnonzero(y_sorted == 1)
    precision_at = (np.arange(len(true_positions)) + 1) / (true_positions + 1)
    return float(precision_at.mean())


def _roc_auc_score(y_true: np.ndarray, y_score: np.ndarray) -> float | None:
    y_true = np.asarray(y_true).astype(int)
    y_score = np.asarray(y_score, dtype=float)
    positives = int(y_true.sum())
    negatives = int(len(y_true) - positives)
    if positives == 0 or negatives == 0:
        return None

    order = np.argsort(y_score, kind="mergesort")
    ranks = np.empty(len(y_score), dtype=float)
    i = 0
    while i < len(y_score):
        j = i
        while j + 1 < len(y_score) and y_score[order[j + 1]] == y_score[order[i]]:
            j += 1
        average_rank = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = average_rank
        i = j + 1
    sum_pos_ranks = float(ranks[y_true == 1].sum())
    return (sum_pos_ranks - positives * (positives + 1) / 2.0) / (positives * negatives)


def application_metrics(scores: pd.DataFrame, truth: pd.DataFrame) -> dict[str, Any]:
    """Métricas a nivel de solicitud usando la verdad terreno."""
    labels = truth[["application_id"]].copy()
    labels["is_ring"] = 1
    merged = scores[["application_id", "risk_score"]].merge(
        labels, on="application_id", how="left"
    )
    merged["is_ring"] = merged["is_ring"].fillna(0).astype(int)
    y_true = merged["is_ring"].to_numpy()
    y_score = merged["risk_score"].to_numpy(dtype=float)

    metrics: dict[str, Any] = {
        "n_applications": int(len(merged)),
        "n_rings": int(y_true.sum()),
        "average_precision": round(float(_average_precision_score(y_true, y_score)), 4),
    }
    auc = _roc_auc_score(y_true, y_score)
    metrics["roc_auc"] = round(float(auc), 4) if auc is not None else None

    ranked = merged.sort_values("risk_score", ascending=False).reset_index(drop=True)
    for k in (25, 50, 100, 200, 259, 500):
        if k > len(ranked):
            continue
        top = ranked.head(k)
        rings = int(top["is_ring"].sum())
        metrics[f"top{k}_precision"] = round(rings / k, 4)
        metrics[f"top{k}_recall"] = round(rings / max(int(y_true.sum()), 1), 4)
        metrics[f"top{k}_rings"] = rings
    return metrics


def cluster_metrics(clusters: pd.DataFrame, truth: pd.DataFrame) -> dict[str, Any]:
    """Métricas a nivel de cluster usando la verdad terreno."""
    ring_apps = set(truth["application_id"])
    ring_types = dict(zip(truth["application_id"], truth["ring_type"]))
    cluster_rows = []
    captured_rings: set[str] = set()
    for row in clusters.itertuples(index=False):
        members = set(json.loads(row.members))
        rings = members & ring_apps
        captured_rings.update(rings)
        cluster_rows.append({
            "cluster_id": row.cluster_id,
            "size": int(row.size),
            "risk_score": float(row.risk_score),
            "ring_members": len(rings),
            "purity": round(len(rings) / max(len(members), 1), 4),
            "ring_types": sorted({ring_types[app] for app in rings}),
        })
    captured = len(captured_rings)
    total_rings = len(ring_apps)
    return {
        "n_clusters": int(len(clusters)),
        "n_pure_clusters": int(sum(1 for row in cluster_rows if row["purity"] == 1.0)),
        "n_clusters_with_rings": int(sum(1 for row in cluster_rows if row["ring_members"] > 0)),
        "captured_rings": captured,
        "ring_recall": round(captured / max(total_rings, 1), 4),
        "cluster_details": cluster_rows,
    }