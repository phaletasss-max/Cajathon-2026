"""Configuración y resultado del motor de detección (Fase 3)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class DetectionConfig:
    """Parámetros del detector no supervisado."""

    threshold: float = 60.0
    resolution: float = 1.0
    min_cluster_size: int = 2
    max_cluster_size: int = 60
    seed: int = 42
    top_evidence: int = 5
    max_clusters: int = 1000

    def __post_init__(self) -> None:
        if not 0 <= self.threshold <= 100:
            raise ValueError("threshold debe estar entre 0 y 100")
        if self.min_cluster_size < 1:
            raise ValueError("min_cluster_size debe ser >= 1")
        if self.max_cluster_size < self.min_cluster_size:
            raise ValueError("max_cluster_size debe ser >= min_cluster_size")


@dataclass
class DetectionResult:
    """Clusters detectados y puntuación por solicitud."""

    clusters: pd.DataFrame
    applications: pd.DataFrame
    config: DetectionConfig
    elapsed_seconds: float
    stats: dict[str, Any] = field(default_factory=dict)
