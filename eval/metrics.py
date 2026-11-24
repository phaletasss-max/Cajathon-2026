"""Métricas de evaluación offline (solo para medir, no para el motor)."""

from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score


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
        "average_precision": round(float(average_precision_score(y_true, y_score)), 4),
    }
    try:
        metrics["roc_auc"] = round(float(roc_auc_score(y_true, y_score)), 4)
    except ValueError:
        metrics["roc_auc"] = None

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