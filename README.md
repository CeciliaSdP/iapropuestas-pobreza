# iapropuestas-pobreza
# Prototipo – Comparador ciudadano (Módulo Pobreza, ENAHO–INEI)

Este prototipo en Streamlit muestra un dashboard de pobreza (ENAHO–INEI, 2019–2023) y un comparador de propuestas ficticias.
- **Variables:** nvpov, vpov, pov, epov.
- **Ámbito:** Perú / regiones (columna `nombre`).
- **Fuente:** ENAHO – INEI.

## Uso local
1) `pip install -r requirements.txt`
2) `streamlit run streamlit_app_prototipo_pobreza.py`
3) En la barra lateral, sube `data/pobreza_enaho.xlsx`.

## Estructura del Excel
Encabezados: `nombre`, `year`, `nvpov`, `vpov`, `pov`, `epov`.
Años: 2019, 2020, 2021, 2022, 2023.
Una fila por región-año.
