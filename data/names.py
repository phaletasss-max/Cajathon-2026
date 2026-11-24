"""Listas propias de nombres, apellidos, calles y negocios peruanos.

Se usan listas locales en lugar de Faker para que los datos sintéticos tengan
coherencia con Trujillo y La Libertad, y para eliminar una dependencia que no
aporta valor al prototipo. Todos los documentos siguen siendo ficticios.
"""

from __future__ import annotations

import random

FEMALE_NAMES = [
    "María", "Rosa", "Ana", "Carmen", "Luz", "Milagros", "Flor", "Yolanda",
    "Patricia", "Sandra", "Jessica", "Katherine", "Gabriela", "Daniela",
    "Valeria", "Camila", "Lucía", "Elena", "Gloria", "Silvia", "Norma",
    "Violeta", "Marisol", "Elizabeth", "Yesenia", "Roxana", "Tatiana",
    "Paola", "Claudia", "Cecilia", "Mónica", "Verónica", "Karina",
    "Melissa", "Angélica", "Beatriz", "Inés", "Julia", "Teresa", "Pilar",
    "Susana", "Erika", "Fiorella", "Noelia", "Alexandra", "Dayana",
    "Ruth", "Esther", "Martha", "Nancy", "Gladys", "Zoila", "Nelly",
    "Miriam", "Lourdes", "Rebeca", "Cinthia", "Magaly", "Pamela", "Alicia",
]

MALE_NAMES = [
    "José", "Carlos", "Luis", "Juan", "Miguel", "Pedro", "Jorge", "Víctor",
    "César", "Marco", "Julio", "Ricardo", "Fernando", "Roberto", "Eduardo",
    "Javier", "Daniel", "Manuel", "Francisco", "Antonio", "Alejandro",
    "Mario", "Percy", "Walter", "Hugo", "Segundo", "Teodoro", "Raúl",
    "Oscar", "Alberto", "Enrique", "Pablo", "Andrés", "Sergio", "Rafael",
    "Gustavo", "Hernán", "Iván", "Jaime", "Luis Alberto", "Martín", "Nelson",
    "Orlando", "Pío", "Rómulo", "Santiago", "Saúl", "Tito", "Ulises",
    "Vicente", "Wilmer", "Yuri", "Zenón", "Edwin", "Elmer", "Frank",
    "Gilberto", "Henry", "Isaías", "Jhon", "Kléber", "Leonardo", "Máximo",
]

SURNAMES = [
    "Quispe", "Flores", "Sánchez", "García", "Rodríguez", "Chávez",
    "Vásquez", "Ramos", "Torres", "Cruz", "Huamán", "Mamani", "Castillo",
    "Rojas", "Mendoza", "Gutiérrez", "Álvarez", "Ruiz", "Díaz", "Fernández",
    "Paredes", "Espinoza", "Aguilar", "Salazar", "Guzmán", "Córdova",
    "Palacios", "Cabrera", "Reyes", "Vargas", "Herrera", "Medina", "Campos",
    "Rivera", "Romero", "Silva", "Cáceres", "Bravo", "Delgado", "Ponce",
    "Zavaleta", "Yupanqui", "Llanos", "Bardales", "Valdivia", "Saavedra",
    "Cubas", "Gonzales", "López", "Pérez", "Martínez", "Ramírez", "Benítes",
    "Villanueva", "Orbegoso", "Ganoza", "Pinillos", "Bocanegra", "Uceda",
    "Vereau", "Vergara", "Vidal", "Zegarra", "Alvarado", "Aredo", "Asmat",
    "Bazán", "Becerra", "Caballero", "Calderón", "Carranza", "Carrasco",
    "Castañeda", "Cerna", "Correa", "Cortez", "De la Cruz", "Esquivel",
    "Estrada", "Gamboa", "Gavidia", "Guevara", "Linares", "Minchola",
    "Moncada", "Morales", "Núñez", "Otiniano", "Peralta", "Pulido",
    "Quiroz", "Ríos", "Saldarriaga", "Sifuentes", "Tello", "Urbina",
    "Valderrama", "Vera", "Yzaguirre", "Zúñiga",
]

DEFAULT_STREETS = [
    "Av. España", "Av. Larco", "Jr. Pizarro", "Av. América Norte",
    "Av. Juan Pablo II", "Av. Los Incas", "Calle San Martín",
    "Av. Sánchez Carrión", "Av. Mansiche", "Av. Húsares de Junín",
    "Jr. Independencia", "Av. Nicolás de Piérola", "Calle Bolognesi",
]

STREETS_BY_GEOCELL: dict[str, list[str]] = {
    "GEO-TRU-01": [
        "Av. España", "Av. Larco", "Jr. Pizarro", "Av. Mansiche",
        "Jr. Independencia", "Av. Nicolás de Piérola", "Calle Bolognesi",
        "Av. Húsares de Junín", "Jr. Gamarra", "Av. Almagro",
    ],
    "GEO-TRU-02": [
        "Av. Sánchez Carrión", "Jr. Sucre", "Av. Pumacahua",
        "Calle Los Ángeles", "Av. Prolongación Unión", "Jr. Túpac Amaru",
        "Calle San Pedro", "Av. El Porvenir",
    ],
    "GEO-TRU-03": [
        "Av. La Esperanza", "Calle Los Laureles", "Jr. Cahuide",
        "Av. Indoamérica", "Calle Micaela Bastidas", "Av. Primavera",
    ],
    "GEO-TRU-04": [
        "Av. Víctor Larco", "Calle El Golf", "Av. Fátima",
        "Jr. Los Cedros", "Av. Buenos Aires", "Calle Las Palmeras",
    ],
    "GEO-TRU-05": [
        "Av. La Ribera", "Calle El Boquerón", "Av. Victor Larco",
        "Jr. Los Pescadores", "Malecón Bocanegra", "Calle Huaca Prieta",
    ],
    "GEO-TRU-06": [
        "Av. Laredo", "Calle San José", "Jr. Santa Rosa",
        "Av. Los Industriales", "Calle La Unión",
    ],
    "GEO-TRU-07": [
        "Av. Moche", "Calle Huaca del Sol", "Jr. La Luna",
        "Av. Los Incas", "Calle Huaca de la Luna",
    ],
    "GEO-TRU-08": [
        "Av. Salaverry", "Calle Puerto", "Jr. Los Marinos",
        "Malecón Salaverry",
    ],
    "GEO-LIB-01": [
        "Jr. Lima", "Av. La Marina", "Calle Comercio", "Jr. Ayacucho",
        "Av. Pacasmayo", "Calle San Pedro",
    ],
    "GEO-LIB-02": [
        "Av. Gonzales Cáceres", "Jr. Túpac Amaru", "Calle San Martín",
        "Av. Chepén", "Jr. Junín",
    ],
    "GEO-LIB-03": [
        "Av. Ascope", "Calle Comercio", "Jr. Bolognesi",
        "Av. Los Ángeles", "Calle La Libertad",
    ],
    "GEO-LIB-04": [
        "Av. Virú", "Calle La Libertad", "Jr. San Martín",
        "Av. Los Chavimochic", "Calle Santa Elena",
    ],
    "GEO-LIB-05": [
        "Jr. Bolognesi", "Av. Andahuaylas", "Calle San Cristóbal",
        "Jr. La Libertad", "Av. Otuzco",
    ],
    "GEO-LIB-06": [
        "Jr. San Martín", "Av. Progreso", "Calle Bolívar",
        "Jr. Santiago", "Av. Los Andes",
    ],
    "GEO-LIB-07": [
        "Jr. Sánchez Carrión", "Av. 10 de Julio", "Calle San Agustín",
        "Jr. Bolívar", "Av. Huamachuco",
    ],
    "GEO-LIM-01": [
        "Av. Túpac Amaru", "Av. Universitaria", "Jr. Los Álamos",
        "Calle San Juan", "Av. Perú",
    ],
    "GEO-PIU-01": [
        "Av. Grau", "Calle Lima", "Jr. Huancavelica", "Av. Sánchez Cerro",
    ],
    "GEO-CHI-01": [
        "Av. Balta", "Calle Elías Aguirre", "Jr. San José", "Av. Chiclayo",
    ],
}

MARKET_NAMES = [
    "Mercado Central de Trujillo", "Mercado Mayorista La Hermelinda",
    "Mercado Unión", "Mercado El Porvenir", "Mercado La Esperanza",
    "Mercado de Huanchaco", "Mercado de Pacasmayo", "Mercado de Chepén",
    "Mercado de Ascope", "Mercado de Virú", "Mercado de Otuzco",
    "Mercado de Huamachuco", "Mercado Zonal de Salaverry",
]

BUSINESS_PREFIXES = {
    "abarrotes": "Bodega", "ropa": "Tienda de ropa", "calzado": "Calzado",
    "comida": "Restaurante", "artesanía": "Artesanía", "servicios": "Servicios",
    "manufactura": "Taller", "transporte": "Transportes",
    "agropecuario": "Agropecuaria", "tecnología": "Tecnología",
    "comercio": "Comercial",
}


def first_name(rng: random.Random, gender: str) -> str:
    """Devuelve un nombre peruano coherente con el género simulado."""
    return rng.choice(FEMALE_NAMES if gender == "F" else MALE_NAMES)


def surname(rng: random.Random) -> str:
    """Devuelve un apellido peruano de la lista local."""
    return rng.choice(SURNAMES)


def street_address(rng: random.Random, geocell_id: str) -> str:
    """Construye una dirección local con calle y número sintéticos."""
    options = STREETS_BY_GEOCELL.get(geocell_id, DEFAULT_STREETS)
    return f"{rng.choice(options)} {rng.randint(100, 1999)}"


def market_name(rng: random.Random) -> str:
    """Nombre de un mercado local para direcciones comerciales compartidas."""
    return rng.choice(MARKET_NAMES)


def business_name(rng: random.Random, sector: str, owner_surname: str) -> str:
    """Nombre comercial sencillo basado en el rubro y el apellido del titular."""
    prefix = BUSINESS_PREFIXES.get(sector, "Negocio")
    return f"{prefix} {owner_surname}"
