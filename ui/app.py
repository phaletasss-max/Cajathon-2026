"""Interfaz de revisión humana (Fase 7)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from review.workflow import record_decision

BASE = Path("outputs")


@st.cache_data(show_spinner=False)
def load_table(name: str, subdir: str = "") -> pd.DataFrame:
    path = BASE / subdir / name if subdir else BASE / name
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8")


@st.cache_data(show_spinner=False)
def load_json(name: str, subdir: str = "") -> dict | list:
    path = BASE / subdir / name if subdir else BASE / name
    if not path.exists():
        return {}
    import json

    return json.loads(path.read_text(encoding="utf-8"))


st.set_page_config(page_title="RIE-02", layout="wide")
st.title("RIE-02 — Detección de redes de riesgo")

clusters = load_table("clusters.csv", "detection")
scores = load_table("application_scores.csv", "detection")
register = load_table("risk_register.csv", "explain")
metrics = load_json("metrics.json", "eval")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Redes detectadas", len(clusters))
col2.metric("Solicitudes en riesgo", int((scores["risk_score"].astype(float) >= 60).sum()) if not scores.empty else 0)
col3.metric("Precisión Top 259", metrics.get("application", {}).get("top259_precision", "—") if isinstance(metrics, dict) else "—")
col4.metric("AP", metrics.get("application", {}).get("average_precision", "—") if isinstance(metrics, dict) else "—")

st.subheader("Redes de riesgo")
if clusters.empty:
    st.warning("No hay resultados. Ejecuta la Fase 3 primero.")
else:
    clusters["risk_score"] = clusters["risk_score"].astype(float)
    min_score = st.slider("Puntuación mínima", 0.0, 100.0, 60.0, 1.0)
    filtered = clusters[clusters["risk_score"] >= min_score].sort_values("risk_score", ascending=False)
    st.dataframe(
        filtered[["cluster_id", "risk_score", "size", "source", "reasons"]],
        use_container_width=True,
        hide_index=True,
    )

    selected = st.selectbox("Expediente", filtered["cluster_id"].tolist() if not filtered.empty else [])
    if selected:
        dossier_path = BASE / "explain" / f"dossier_{selected}.md"
        if dossier_path.exists():
            st.markdown(dossier_path.read_text(encoding="utf-8"))
        else:
            st.info("Genera la Fase 4 para ver el expediente.")

st.subheader("Solicitudes")
if not scores.empty:
    scores["risk_score"] = scores["risk_score"].astype(float)
    min_score = st.slider("Puntuación mínima de solicitud", 0.0, 100.0, 60.0, 1.0, key="app_min")
    top = scores[scores["risk_score"] >= min_score].head(100)
    st.dataframe(
        top[["rank", "application_id", "risk_score", "cluster_id", "top_reason"]],
        use_container_width=True,
        hide_index=True,
    )

st.subheader("Revisión humana")
if not register.empty:
    cluster_id = st.selectbox("Red", register["cluster_id"].tolist(), key="review_cluster")
    decision = st.selectbox("Decisión", ["pendiente", "confirmado", "descartado", "falso_positivo"])
    reviewer = st.text_input("Revisor", value="analista")
    notes = st.text_area("Notas")
    if st.button("Guardar decisión"):
        try:
            record_decision(
                BASE / "explain" / "risk_register.csv",
                BASE / "review",
                cluster_id,
                decision,
                reviewer,
                notes,
            )
            st.success("Decisión registrada")
        except Exception as exc:  # noqa: BLE001
            st.error(str(exc))
PY