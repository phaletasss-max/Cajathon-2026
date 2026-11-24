"""Orquestador del generador sintético y CLI reproducible.

Uso:
    python -m data.generator --n-legit 5000 --rings 25 --seed 42
    python -m data.generator --n-legit 5000 --rings 5 --seed 42 --difficulty hard

Salidas:
    data/raw/*.csv                  tablas públicas (sin etiquetas ocultas)
    data/ground_truth/*.csv         etiquetas para evaluación exclusivamente
    data/ground_truth/run_meta.json dificultad, prevalencia y configuración
    data/raw/dataset_meta.json      metadatos y conteos
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import numpy as np
import pandas as pd

from data.applications import build_legit_applications
from data.obfuscation import obfuscate_and_shuffle
from data.population import build_population
from data.rings import DIFFICULTY_CONFIG, RING_TYPES, inject_fraud_rings
from data.schema import (
    DEFAULT_OUT_DIR,
    FORBIDDEN_PUBLIC_TOKENS,
    PUBLIC_SCHEMAS,
    SCHEMA_VERSION,
    TRUTH_SCHEMAS,
    IdAllocator,
    ensure_output_dirs,
)


def _concat(base: pd.DataFrame, extra: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Concatena tablas respetando el contrato de columnas."""
    if base.empty and extra.empty:
        return pd.DataFrame(columns=columns)
    return pd.concat([base, extra], ignore_index=True).reindex(columns=columns)


def _check_public_columns(tables: dict[str, pd.DataFrame]) -> None:
    for table_name, frame in tables.items():
        bad = [c for c in frame.columns if any(t in c.lower() for t in FORBIDDEN_PUBLIC_TOKENS)]
        if bad:
            raise ValueError(f"Columnas con posible fuga de etiqueta en {table_name}: {bad}")


def generate_dataset(
    n_legit: int = 5000,
    n_rings: int = 25,
    seed: int = 42,
    out_dir: str | Path | None = None,
    difficulty: str = "medium",
) -> dict[str, Path]:
    """Genera el dataset completo y devuelve las rutas escritas."""
    if n_legit < 10:
        raise ValueError("n_legit debe ser >= 10 para construir hogares y mercados")
    if difficulty not in DIFFICULTY_CONFIG:
        raise ValueError(f"Dificultad inválida: {difficulty}")

    base_dir = Path(out_dir) if out_dir is not None else DEFAULT_OUT_DIR
    raw_dir, truth_dir = ensure_output_dirs(base_dir)

    rng = random.Random(seed)
    np_rng = np.random.default_rng(seed)
    ids = IdAllocator()

    population, geocells = build_population(n_legit, rng, np_rng, ids)
    applications, references = build_legit_applications(population)
    injected = inject_fraud_rings(population, n_rings, difficulty)

    tables = {
        "persons": _concat(population.persons, injected.persons, PUBLIC_SCHEMAS["persons"]),
        "businesses": _concat(population.businesses, injected.businesses, PUBLIC_SCHEMAS["businesses"]),
        "addresses": _concat(population.addresses, injected.addresses, PUBLIC_SCHEMAS["addresses"]),
        "phones": _concat(population.phones, injected.phones, PUBLIC_SCHEMAS["phones"]),
        "devices": _concat(population.devices, injected.devices, PUBLIC_SCHEMAS["devices"]),
        "applications": _concat(applications, injected.applications, PUBLIC_SCHEMAS["applications"]),
        "references": _concat(references, injected.references, PUBLIC_SCHEMAS["references"]),
        "geocells": geocells.reindex(columns=PUBLIC_SCHEMAS["geocells"]),
    }
    _check_public_columns(tables)

    tables, truth, rings = obfuscate_and_shuffle(
        tables, injected.truth, injected.rings, seed
    )

    written: dict[str, Path] = {}
    for table_name, frame in tables.items():
        path = raw_dir / f"{table_name}.csv"
        frame.to_csv(path, index=False, encoding="utf-8")
        written[table_name] = path

    for table_name, frame in {
        "ground_truth": truth,
        "rings": rings,
    }.items():
        path = truth_dir / f"{table_name}.csv"
        frame.reindex(columns=TRUTH_SCHEMAS[table_name]).to_csv(path, index=False, encoding="utf-8")
        written[table_name] = path

    meta = {
        "schema_version": SCHEMA_VERSION,
        "seed": seed,
        "difficulty": difficulty,
        "n_legit_persons_requested": n_legit,
        "n_rings_requested": n_rings,
        "prevalence_rings_per_1000_persons": round(1000 * n_rings / n_legit, 3),
        "ring_types": RING_TYPES,
        "counts": {name: int(len(frame)) for name, frame in tables.items()},
        "n_ring_persons": int(truth["person_id"].nunique()),
        "n_ring_applications": int(truth["application_id"].nunique()),
        "privacy": "100% datos sintéticos; sin PII real; IDs opacos",
    }
    meta_path = raw_dir / "dataset_meta.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    written["meta"] = meta_path

    run_meta = {
        "difficulty": difficulty,
        "seed": seed,
        "n_legit_persons": n_legit,
        "n_rings": n_rings,
        "n_ring_persons": int(truth["person_id"].nunique()),
        "n_ring_applications": int(truth["application_id"].nunique()),
        "prevalence_rings_per_1000_persons": round(1000 * n_rings / n_legit, 3),
        "ring_type_counts": {
            str(key): int(value) for key, value in rings["ring_type"].value_counts().items()
        },
        "ring_type_application_counts": {
            str(key): int(value) for key, value in truth["ring_type"].value_counts().items()
        },
        "difficulty_config": DIFFICULTY_CONFIG[difficulty],
    }
    run_meta_path = truth_dir / "run_meta.json"
    run_meta_path.write_text(json.dumps(run_meta, ensure_ascii=False, indent=2), encoding="utf-8")
    written["run_meta"] = run_meta_path
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera datos sintéticos para RIE-02")
    parser.add_argument("--n-legit", type=int, default=5000, help="personas legítimas base")
    parser.add_argument("--rings", type=int, default=25, help="anillos de fraude inyectados")
    parser.add_argument("--seed", type=int, default=42, help="semilla reproducible")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_DIR, help="directorio de salida")
    parser.add_argument(
        "--difficulty", choices=sorted(DIFFICULTY_CONFIG), default="medium",
        help="easy: señales fuertes; hard: ruido y camuflaje",
    )
    args = parser.parse_args()

    paths = generate_dataset(
        args.n_legit, args.rings, args.seed, args.out, args.difficulty
    )
    print(json.dumps({name: str(path) for name, path in paths.items()}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
