"""Población sintética: hogares, teléfonos, dispositivos, negocios y cooperativas.

La generación crea relaciones benignas densas (familias, mercados, cooperativas)
para que el motor tenga que distinguirlas de los anillos inyectados. Ninguna
columna pública identifica si una persona pertenece a un anillo.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

from data.names import (
    business_name,
    first_name,
    market_name,
    street_address,
    surname as random_surname,
)
from data.schema import (
    CITY_WEIGHTS,
    GEOCELL_BY_ID,
    GEOCELLS,
    PUBLIC_SCHEMAS,
    IdAllocator,
    fmt_dt,
    jitter_coords,
    pick_weighted,
)

OCCUPATIONS = [
    "comerciante", "transportista", "docente", "agricultor", "independiente",
    "empleado", "artesano", "técnico", "vendedor", "confeccionista",
]
MARKET_SECTORS = ["abarrotes", "ropa", "calzado", "comida", "artesanía", "servicios"]
BUSINESS_SECTORS = MARKET_SECTORS + ["manufactura", "transporte", "agropecuario", "tecnología"]


@dataclass
class Population:
    """Tablas base y mapas internos necesarios para generar solicitudes."""

    ids: IdAllocator
    rng: random.Random
    np_rng: np.random.Generator
    persons: pd.DataFrame
    businesses: pd.DataFrame
    addresses: pd.DataFrame
    phones: pd.DataFrame
    devices: pd.DataFrame
    household_members: dict[str, list[str]]
    spouse_of: dict[str, str]
    coop_members: dict[str, list[str]]
    market_members: dict[str, list[str]]
    market_addresses: dict[str, str]
    coop_of_person: dict[str, str]
    market_of_person: dict[str, str]
    home_geocell: dict[str, str]
    phone_by_person: dict[str, str]
    device_by_person: dict[str, str]
    home_address_by_person: dict[str, str]
    business_by_person: dict[str, str]
    used_phones: set[str]
    used_docs: set[str]


def build_population(
    n_legit: int,
    rng: random.Random,
    np_rng: np.random.Generator,
    ids: IdAllocator,
) -> tuple[Population, pd.DataFrame]:
    """Construye una población legítima con estructura familiar y comercial."""
    addresses: list[dict[str, object]] = []
    persons: list[dict[str, object]] = []
    phones: list[dict[str, object]] = []
    devices: list[dict[str, object]] = []
    businesses: list[dict[str, object]] = []

    person_by_id: dict[str, dict[str, object]] = {}
    household_members: dict[str, list[str]] = {}
    spouse_of: dict[str, str] = {}
    coop_members: dict[str, list[str]] = {}
    market_members: dict[str, list[str]] = {}
    market_addresses: dict[str, str] = {}
    coop_of_person: dict[str, str] = {}
    market_of_person: dict[str, str] = {}
    home_geocell: dict[str, str] = {}
    phone_by_person: dict[str, str] = {}
    device_by_person: dict[str, str] = {}
    home_address_by_person: dict[str, str] = {}
    business_by_person: dict[str, str] = {}
    used_phones: set[str] = set()
    used_docs: set[str] = set()

    def add_address(geocell_id: str, address_type: str = "vivienda", street: str | None = None) -> str:
        geo = GEOCELL_BY_ID[geocell_id]
        address_id = ids.next("ADR")
        lat, lon = jitter_coords(rng, geocell_id)
        addresses.append({
            "address_id": address_id,
            "address_type": address_type,
            "street": street or street_address(rng, geocell_id),
            "district": geo["district"],
            "province": geo["province"],
            "department": geo["department"],
            "geocell_id": geocell_id,
            "latitude": lat,
            "longitude": lon,
        })
        return address_id

    def add_phone(owner_person_id: str | None = None) -> str:
        phone_id = ids.next("PHN")
        while True:
            number = f"9{rng.randint(0, 99_999_999):08d}"
            if number not in used_phones:
                used_phones.add(number)
                break
        activation = datetime(2016, 1, 1) + timedelta(days=rng.randrange(0, 3200))
        phones.append({
            "phone_id": phone_id,
            "phone_number": number,
            "line_type": "móvil",
            "owner_person_id": owner_person_id,
            "activation_date": fmt_dt(activation),
        })
        return phone_id

    def add_device(owner_person_id: str | None = None, device_type: str | None = None) -> str:
        device_id = ids.next("DEV")
        first_seen = datetime(2017, 1, 1) + timedelta(days=rng.randrange(0, 2900))
        devices.append({
            "device_id": device_id,
            "device_fingerprint": f"FP-{rng.getrandbits(48):012x}",
            "device_type": device_type or rng.choices(
                ["smartphone", "tablet", "laptop"], weights=[0.82, 0.09, 0.09]
            )[0],
            "owner_person_id": owner_person_id,
            "first_seen": fmt_dt(first_seen),
        })
        return device_id

    def unique_doc() -> str:
        while True:
            number = f"{rng.randint(0, 99_999_999):08d}"
            if number not in used_docs:
                used_docs.add(number)
                return number

    def add_person(
        home_address_id: str,
        geocell_id: str,
        primary_phone_id: str,
        primary_device_id: str,
        surname: str,
    ) -> str:
        person_id = ids.next("PER")
        gender = rng.choice(["F", "M"])
        first = first_name(rng, gender)
        birth = date(1960, 1, 1) + timedelta(days=rng.randrange(0, 43 * 365))
        created = datetime(2017, 1, 1) + timedelta(days=rng.randrange(0, 2550), seconds=rng.randrange(86400))
        income = max(900, min(25_000, int(round(rng.lognormvariate(7.95, 0.55), -2))))
        row = {
            "person_id": person_id,
            "full_name": f"{first} {surname}",
            "doc_type": "DNI",
            "doc_number": unique_doc(),
            "birth_date": birth.isoformat(),
            "gender": gender,
            "home_address_id": home_address_id,
            "primary_phone_id": primary_phone_id,
            "primary_device_id": primary_device_id,
            "occupation": rng.choice(OCCUPATIONS),
            "monthly_income_pen": income,
            "coop_id": None,
            "created_at": fmt_dt(created),
            "surname": surname,
        }
        persons.append(row)
        person_by_id[person_id] = row
        home_geocell[person_id] = geocell_id
        phone_by_person[person_id] = primary_phone_id
        device_by_person[person_id] = primary_device_id
        home_address_by_person[person_id] = home_address_id
        return person_id

    # --- Hogares y familiares -------------------------------------------------
    household_no = 0
    while len(persons) < n_legit:
        remaining = n_legit - len(persons)
        size = min(rng.choices([1, 2, 2, 3, 4, 5], weights=[0.18, 0.34, 0.17, 0.19, 0.09, 0.03])[0], remaining)
        household_no += 1
        household_id = f"H{household_no:05d}"
        geocell_id = pick_weighted(rng, list(CITY_WEIGHTS), list(CITY_WEIGHTS.values()))
        address_id = add_address(geocell_id)
        surname = random_surname(rng)
        family_phone = add_phone(None) if size >= 2 and rng.random() < 0.30 else None
        family_device = add_device(None, "tablet") if size >= 2 and rng.random() < 0.09 else None
        members: list[str] = []
        for _ in range(size):
            own_phone = add_phone(None)
            own_device = add_device(None)
            primary_phone = family_phone if family_phone and rng.random() < 0.35 else own_phone
            primary_device = family_device if family_device and rng.random() < 0.30 else own_device
            person_id = add_person(address_id, geocell_id, primary_phone, primary_device, surname)
            members.append(person_id)
        household_members[household_id] = members
        if size >= 2 and rng.random() < 0.65:
            spouse_of[members[0]] = members[1]
            spouse_of[members[1]] = members[0]

    person_ids = [p["person_id"] for p in persons]  # type: ignore[misc]
    pool = person_ids[:]
    rng.shuffle(pool)
    cursor = 0

    # --- Cooperativas (relaciones legítimas, no fraude) ----------------------
    n_coops = max(3, len(person_ids) // 700)
    for index in range(n_coops):
        if cursor >= len(pool):
            break
        coop_id = f"COOP-{index + 1:03d}"
        size = min(rng.randint(18, 38), len(pool) - cursor)
        if size < 10:
            break
        members = pool[cursor:cursor + size]
        cursor += size
        coop_members[coop_id] = members
        for person_id in members:
            person_by_id[person_id]["coop_id"] = coop_id
            coop_of_person[person_id] = coop_id

    # --- Mercados: 30+ personas comparten dirección comercial -----------------
    n_markets = max(3, len(person_ids) // 800)
    for index in range(n_markets):
        if cursor >= len(pool):
            break
        size = min(rng.randint(30, 55), len(pool) - cursor)
        if size < 10:
            break
        market_id = f"MKT-{index + 1:03d}"
        members = pool[cursor:cursor + size]
        cursor += size
        geocell_id = pick_weighted(
            rng,
            ["GEO-TRU-01", "GEO-TRU-02", "GEO-TRU-03", "GEO-LIB-01", "GEO-LIB-02"],
            [0.35, 0.25, 0.15, 0.15, 0.10],
        )
        address_id = add_address(geocell_id, "comercial", market_name(rng))
        market_members[market_id] = members
        market_addresses[market_id] = address_id
        for person_id in members:
            market_of_person[person_id] = market_id
            person_by_id[person_id]["occupation"] = "comerciante"
            person_by_id[person_id]["monthly_income_pen"] = rng.randint(1800, 6500)
            business_id = ids.next("BUS")
            businesses.append({
                "business_id": business_id,
                "owner_person_id": person_id,
                "business_name": f"Puesto {person_by_id[person_id]['surname']}",
                "sector": rng.choice(MARKET_SECTORS),
                "commercial_address_id": address_id,
                "monthly_sales_pen": rng.randint(3000, 18_000),
                "created_at": fmt_dt(datetime(2019, 1, 1) + timedelta(days=rng.randrange(0, 1800))),
            })
            business_by_person[person_id] = business_id

    # --- Negocios fuera de mercados ------------------------------------------
    for person in persons:
        person_id = str(person["person_id"])
        if person_id in market_of_person or rng.random() >= 0.38:
            continue
        if rng.random() < 0.45:
            address_id = str(person["home_address_id"])
        else:
            address_id = add_address(str(home_geocell[person_id]), "comercial")
        business_id = ids.next("BUS")
        sector = rng.choice(BUSINESS_SECTORS)
        businesses.append({
            "business_id": business_id,
            "owner_person_id": person_id,
            "business_name": business_name(
                rng, sector, str(person_by_id[person_id]["surname"])
            ),
            "sector": sector,
            "commercial_address_id": address_id,
            "monthly_sales_pen": max(1200, int(round(rng.lognormvariate(8.7, 0.7), -2))),
            "created_at": fmt_dt(datetime(2020, 1, 1) + timedelta(days=rng.randrange(0, 1700))),
        })
        business_by_person[person_id] = business_id

    return Population(
        ids=ids,
        rng=rng,
        np_rng=np_rng,
        persons=pd.DataFrame(persons, columns=PUBLIC_SCHEMAS["persons"]),
        businesses=pd.DataFrame(businesses, columns=PUBLIC_SCHEMAS["businesses"]),
        addresses=pd.DataFrame(addresses, columns=PUBLIC_SCHEMAS["addresses"]),
        phones=pd.DataFrame(phones, columns=PUBLIC_SCHEMAS["phones"]),
        devices=pd.DataFrame(devices, columns=PUBLIC_SCHEMAS["devices"]),
        household_members=household_members,
        spouse_of=spouse_of,
        coop_members=coop_members,
        market_members=market_members,
        market_addresses=market_addresses,
        coop_of_person=coop_of_person,
        market_of_person=market_of_person,
        home_geocell=home_geocell,
        phone_by_person=phone_by_person,
        device_by_person=device_by_person,
        home_address_by_person=home_address_by_person,
        business_by_person=business_by_person,
        used_phones=used_phones,
        used_docs=used_docs,
    ), pd.DataFrame(GEOCELLS, columns=PUBLIC_SCHEMAS["geocells"])
