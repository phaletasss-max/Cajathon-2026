"""Modelo y configuración del grafo de riesgo (Fase 2).

El grafo tiene dos capas:

- ``bipartite``: entidades (solicitudes, personas, negocios) contra atributos
  (teléfono, dispositivo, dirección, referencia y geocelda).
- ``projection``: solicitudes conectadas por atributos compartidos. Los
  atributos de alta multiplicidad no forman cliques; se representan con un
  nodo hub para evitar una explosión cuadrática de aristas.

Las aristas guardan evidencia exacta (tipo, valor hasheado y peso) y la ventana
temporal de las solicitudes conectadas.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from typing import Any

import networkx as nx
import pandas as pd

SCHEMA_VERSION = "2.0"

# Peso máximo por tipo de atributo. Sin tope, un teléfono casi único dominaría
# cualquier agregación y una geocelda compartida por miles sería inestable.
DEFAULT_WEIGHT_CAPS: dict[str, float] = {
    "phone": 8.0,
    "device": 8.0,
    "address": 6.0,
    "reference": 7.0,
    "geocell": 1.5,
}
FALLBACK_WEIGHT_CAP = 5.0

ATTRIBUTE_TYPES = ("phone", "device", "address", "reference", "geocell")


@dataclass(frozen=True)
class GraphConfig:
    """Parámetros reproducibles del constructor de grafo.

    ``max_multiplicity`` es el umbral K: un atributo compartido por más de K
    entidades se convierte en hub y no genera aristas completas.
    """

    max_multiplicity: int = 25
    weight_caps: dict[str, float] = field(
        default_factory=lambda: dict(DEFAULT_WEIGHT_CAPS)
    )
    salt: str = "rie02-fase2"
    include_hubs: bool = True

    def __post_init__(self) -> None:
        if self.max_multiplicity < 2:
            raise ValueError("max_multiplicity debe ser >= 2")
        if not self.salt:
            raise ValueError("salt no puede estar vacío")
        for attribute_type, cap in self.weight_caps.items():
            if attribute_type not in ATTRIBUTE_TYPES:
                raise ValueError(f"tipo de atributo desconocido: {attribute_type}")
            if cap <= 0:
                raise ValueError(f"el tope de {attribute_type} debe ser > 0")


@dataclass
class GraphBuildResult:
    """Grafo construido, tablas planas y métricas de la ejecución."""

    bipartite: nx.Graph
    projection: nx.Graph
    edges: pd.DataFrame
    nodes: pd.DataFrame
    attributes: pd.DataFrame
    config: GraphConfig
    n_applications: int
    n_entities: int
    elapsed_seconds: float
    stats: dict[str, Any] = field(default_factory=dict)


def attribute_weight(
    df: int,
    n_entities: int,
    attribute_type: str,
    config: GraphConfig,
) -> float:
    """IDF suavizado con tope por tipo: log((N+1)/(df+1))."""
    if df < 1:
        raise ValueError("df debe ser >= 1")
    if n_entities < 1:
        raise ValueError("n_entities debe ser >= 1")
    idf = math.log((n_entities + 1) / (df + 1))
    cap = config.weight_caps.get(attribute_type, FALLBACK_WEIGHT_CAP)
    return round(min(idf, cap), 6)


def hash_attribute(
    attribute_type: str, raw_value: str, salt: str
) -> str:
    """Hash estable y truncado; nunca se exporta el valor crudo en la evidencia."""
    material = f"{attribute_type}|{raw_value}|{salt}".encode("utf-8")
    return hashlib.sha256(material).hexdigest()[:16]


def evidence_entry(
    attribute_type: str,
    value_hash: str,
    weight: float,
    df: int,
) -> dict[str, Any]:
    """Elemento de evidencia citable por un expediente de la Fase 4."""
    return {
        "type": attribute_type,
        "value_hash": value_hash,
        "weight": round(float(weight), 6),
        "df": int(df),
    }
