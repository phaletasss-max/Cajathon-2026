"""Solicitudes y referencias de la población legítima.

Las referencias se generan con una mezcla de cónyuges, familiares, socios de
cooperativa, colegas de mercado y vecinos. Esa mezcla produce reciprocidad y
comunidades densas que luego deben ser explicadas, no tratadas como fraude.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd

from data.population import Population
from data.schema import GEOCELL_BY_ID, PUBLIC_SCHEMAS, fmt_dt

PRODUCTS = ["microcrédito", "capital_trabajo", "crédito_agro", "crédito_personal"]
PURPOSES = ["capital_trabajo", "inventario", "consumo", "agro", "mejora_vivienda"]
CHANNELS = ["app", "web", "agencia", "asesor"]
RELATION_WEIGHTS = {
    "conyuge": 4.0,
    "familiar": 1.4,
    "socio_cooperativa": 1.1,
    "colega_mercado": 0.9,
    "vecino": 0.5,
    "referencia_personal": 0.2,
}


def _business_hours_datetime(rng: random.Random) -> datetime:
    """Fecha aleatoria en 18 meses, concentrada en horario laboral."""
    day = datetime(2024, 1, 1) + timedelta(days=rng.randrange(0, 547))
    if day.weekday() >= 5 and rng.random() < 0.85:
        day += timedelta(days=7 - day.weekday())
    hour = rng.choices(
        list(range(8, 20)),
        weights=[1, 2, 3, 4, 4, 3, 2, 3, 4, 4, 2, 1],
        k=1,
    )[0]
    return day.replace(hour=hour, minute=rng.randrange(60), second=rng.randrange(60))


def _same_department_geocell(
    rng: random.Random, home_geocell: str, geocells: pd.DataFrame
) -> str:
    """Elige otra geocelda del mismo departamento, si existe."""
    row = geocells.loc[geocells["geocell_id"] == home_geocell].iloc[0]
    options = geocells.loc[
        (geocells["department"] == row["department"])
        & (geocells["geocell_id"] != home_geocell),
        "geocell_id",
    ].tolist()
    return str(rng.choice(options)) if options else home_geocell


def _weighted_reference_sample(
    rng: random.Random, candidates: dict[str, str], k: int
) -> list[tuple[str, str]]:
    """Muestrea referencias sin reemplazo, ponderando el tipo de vínculo."""
    pool = dict(candidates)
    chosen: list[tuple[str, str]] = []
    while pool and len(chosen) < k:
        ids = list(pool)
        weights = [RELATION_WEIGHTS.get(pool[pid], 0.2) for pid in ids]
        picked = rng.choices(ids, weights=weights, k=1)[0]
        chosen.append((picked, pool.pop(picked)))
    return chosen


def build_legit_applications(
    population: Population,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Genera una solicitud por persona legítima y sus referencias."""
    rng = population.rng
    np_rng = population.np_rng
    applications: list[dict[str, Any]] = []
    references: list[dict[str, Any]] = []

    business_address = dict(
        zip(population.businesses["business_id"], population.businesses["commercial_address_id"])
    )
    household_of: dict[str, str] = {}
    for household_id, members in population.household_members.items():
        for person_id in members:
            household_of[person_id] = household_id
    persons_by_geocell: dict[str, list[str]] = {}
    for person_id, geocell_id in population.home_geocell.items():
        persons_by_geocell.setdefault(geocell_id, []).append(person_id)
    geocells = pd.DataFrame.from_records(
        [
            {"geocell_id": gid, "department": geo["department"]}
            for gid, geo in GEOCELL_BY_ID.items()
        ]
    )

    for person in population.persons.itertuples(index=False):
        person_id = str(person.person_id)
        home_geo = population.home_geocell[person_id]
        business_id = population.business_by_person.get(person_id)
        coop_id = person.coop_id if isinstance(person.coop_id, str) else None
        created_at = _business_hours_datetime(rng)

        product = rng.choices(PRODUCTS, weights=[0.42, 0.28, 0.10, 0.20], k=1)[0]
        amount = float(np_rng.lognormal(8.55, 0.55))
        amount = max(500, min(80_000, int(round(amount, -2))))
        app_geo = home_geo if rng.random() < 0.90 else _same_department_geocell(rng, home_geo, geocells)
        declared_address = (
            business_address[business_id]
            if business_id and rng.random() < 0.20
            else person.home_address_id
        )
        application_id = population.ids.next("APP")
        applications.append({
            "application_id": application_id,
            "person_id": person_id,
            "business_id": business_id,
            "product": product,
            "amount_pen": amount,
            "term_months": rng.choices([6, 12, 18, 24, 36], weights=[0.20, 0.38, 0.22, 0.15, 0.05], k=1)[0],
            "channel": rng.choices(CHANNELS, weights=[0.38, 0.22, 0.26, 0.14], k=1)[0],
            "purpose": rng.choice(PURPOSES),
            "created_at": fmt_dt(created_at),
            "declared_address_id": declared_address,
            "application_geocell_id": app_geo,
            "device_id": population.device_by_person[person_id],
            "phone_id": population.phone_by_person[person_id],
            "coop_id": coop_id,
            "status": "recibida",
        })

        candidates: dict[str, str] = {}
        spouse = population.spouse_of.get(person_id)
        if spouse:
            candidates[spouse] = "conyuge"
        for member in population.household_members.get(household_of.get(person_id, ""), []):
            if member != person_id:
                candidates[member] = "familiar"
        if coop_id:
            for member in population.coop_members.get(coop_id, []):
                if member != person_id:
                    candidates[member] = "socio_cooperativa"
        market_id = population.market_of_person.get(person_id)
        if market_id:
            for member in population.market_members.get(market_id, []):
                if member != person_id:
                    candidates[member] = "colega_mercado"
        neighbors = persons_by_geocell.get(home_geo, [])
        if neighbors:
            for member in rng.sample(neighbors, min(25, len(neighbors))):
                if member != person_id:
                    candidates.setdefault(member, "vecino")
        if not candidates:
            fallback = rng.choice([p for p in population.persons["person_id"] if p != person_id])
            candidates[str(fallback)] = "referencia_personal"

        reference_count = rng.choices([1, 2, 3], weights=[0.25, 0.55, 0.20], k=1)[0]
        for ref_person_id, relationship in _weighted_reference_sample(rng, candidates, reference_count):
            ref_created = created_at - timedelta(days=rng.randint(1, 25), hours=rng.randint(0, 23))
            references.append({
                "reference_id": population.ids.next("REF"),
                "application_id": application_id,
                "ref_person_id": ref_person_id,
                "relationship": relationship,
                "ref_phone_id": population.phone_by_person.get(ref_person_id),
                "created_at": fmt_dt(ref_created),
            })

    return (
        pd.DataFrame(applications, columns=PUBLIC_SCHEMAS["applications"]),
        pd.DataFrame(references, columns=PUBLIC_SCHEMAS["references"]),
    )
