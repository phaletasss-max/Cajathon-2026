# Expediente C00005

- **Puntuación de riesgo:** 68.58
- **Tamaño de la red:** 14 solicitudes
- **Origen de detección:** louvain
- **Resumen:** Dispositivo compartido en 6 aristas

## Motivos
- Dispositivo compartido en 6 aristas
- Teléfono compartido en 6 aristas
- Ráfaga temporal: 8 solicitudes en <=72 h con dirección compartida
- 12 personas con solicitudes en geoceldas incompatibles
- 8 solicitudes a >=500 km del domicilio
- Atributo de alto peso compartido (peso 16.2)

## Ventana temporal
- Inicio: 2024-07-23 19:34:20
- Fin: 2024-08-10 02:34:20
- Duración: 415.0 h

## Atributos compartidos (evidencia)
- `geocell` hash `1ec8a116096fb25b` — peso 1.5, compartido por 28 solicitudes (df 8)
- `phone` hash `83309a7745578f06` — peso 5.392491, compartido por 1 solicitudes (df 3)
- `device` hash `08f1486aab7c4f39` — peso 5.392491, compartido por 1 solicitudes (df 3)
- `address` hash `960512cf2de78013` — peso 5.392491, compartido por 1 solicitudes (df 3)
- `phone` hash `41b91d831efdc277` — peso 5.392491, compartido por 1 solicitudes (df 3)

## Contexto del grafo
- Aristas: 34
- Densidad: 0.373626
- Peso máximo de arista: 16.177473

## Solicitudes de la red

| Solicitud | Fecha | Monto | Geocelda solicitud | Distancia km | Teléfono | Documento |
|---|---:|---:|---|---:|---|---|
| 0867b7315c53… | 2024-07-31 17:34:20 | 20979 | La Esperanza (Trujillo) | None | *****6124 | ****7669 |
| 11526db2e80b… | 2024-08-06 13:34:20 | 11698 | La Esperanza (Trujillo) | None | *****1259 | ****3139 |
| 20e57f90ba50… | 2024-08-10 02:34:20 | 14421 | La Esperanza (Trujillo) | None | *****2027 | ****2151 |
| 235eca9ea855… | 2024-08-07 18:34:20 | 21963 | La Esperanza (Trujillo) | None | *****9166 | ****1448 |
| 29dcfa0f6da5… | 2024-08-09 04:34:20 | 15539 | La Esperanza (Trujillo) | None | *****3144 | ****7898 |
| 9f966419c6b3… | 2024-08-08 04:34:20 | 16818 | Puno (Puno) | 1306.3 | *****3144 | ****7898 |
| b826d7451ea8… | 2024-07-23 19:34:20 | 15605 | Puno (Puno) | 1306.3 | *****5976 | ****9874 |
| bd28efdfc6c1… | 2024-08-07 14:34:20 | 13408 | Puno (Puno) | 1306.3 | *****0970 | ****9749 |
| c0c465272ca9… | 2024-07-30 01:34:20 | 15483 | La Esperanza (Trujillo) | None | *****2119 | ****5123 |
| d52ea1b65d01… | 2024-07-30 19:34:20 | 19413 | Puno (Puno) | 1306.3 | *****6124 | ****7669 |
| d7c2d0671d2e… | 2024-08-06 21:34:20 | 19125 | Puno (Puno) | 1306.3 | *****9166 | ****1448 |
| d88650fb42a5… | 2024-08-09 07:34:20 | 16708 | Puno (Puno) | 1306.3 | *****2027 | ****2151 |
| e1e249b3519e… | 2024-08-06 08:34:20 | 13664 | Puno (Puno) | 1306.3 | *****1259 | ****3139 |
| e8e543f31b9f… | 2024-07-28 17:34:20 | 17303 | Puno (Puno) | 1306.3 | *****2119 | ****5123 |

Datos sintéticos; documentos, teléfonos y huellas enmascarados. La evidencia usa valores hasheados.
