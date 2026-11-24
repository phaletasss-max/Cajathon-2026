"""Pruebas de la Fase 8: benchmark por dificultad."""

from __future__ import annotations

from pathlib import Path

from eval.benchmark import run_benchmark


def test_benchmark_runs(tmp_path: Path) -> None:
    result = run_benchmark(
        n_legit=200,
        seed=7,
        difficulties=["medium"],
        low_prevalence_rings=2,
        output_dir=tmp_path / "benchmark",
    )
    assert (tmp_path / "benchmark" / "benchmark.json").exists()
    assert (tmp_path / "benchmark" / "report.md").exists()
    assert len(result["results"]) == 2
    assert result["results"][0]["average_precision"] is not None