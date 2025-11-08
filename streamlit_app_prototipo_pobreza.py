# -------------------------------------------------------------
# Prototipo inicial – Plataforma cívica (ENAHO–INEI)
# Requisitos: streamlit, pandas, plotly, openpyxl
# Ejecución:  streamlit run streamlit_app_prototipo_pobreza.py
# -------------------------------------------------------------

import io
import unicodedata
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Comparador ciudadano – Prototipo (ENAHO–INEI)",
    page_icon="📊",
    layout="wide"
)

# --------------------------
# Estilos ligeros (elegante)
# --------------------------
CUSTOM_CSS = """
<style>
:root { --text: #0F172A; --muted:#475569; --brand:#0EA5E9; }
/* Tipografía y jerarquía */
h1, h2, h3 { font-weight: 700; letter-spacing: .2px; }
.section { padding: .6rem 1rem; border-left: 4px solid var(--brand); background: #F8FAFC; margin-bottom: .6rem; }
.kpi { border-radius: 16px; padding: 1rem; border: 1px solid #E2E8F0; background: white; }
.source { color: var(--muted); font-size: .9rem; }
.caption { color: var(--muted); font-size: .85rem; }
hr { border: none; border-top: 1px solid #E2E8F0; margin: .6rem 0; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# --------------------------
# Utilidades
# --------------------------

def normalize_str(s: str) -> str:
    """Lower-case + remove accents + trim."""
    s = s.strip().lower()
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    return s

# Column synonyms accepted
COL_SYNONYMS = {
    "region": ["region", "nombre", "departamento", "dpto", "ambito"],
    "year":   ["anio", "ano", "año", "year", "periodo"],
    "nvpov":  ["nvpov", "no pobres no vulnerables", "no_pobres_no_vulnerables"],
    "vpov":   ["vpov", "no pobres vulnerables", "no_pobres_vulnerables"],
    "pov":    ["pov", "pobres", "pobreza", "num pobrez"],
    "epov":   ["epov", "pobreza extrema", "extrema_pobreza"]
}

REQUIRED_COLS = ["region", "year", "nvpov", "vpov", "pov", "epov"]


def match_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Mapea columnas del Excel a nombres canónicos si encuentra sinónimos."""
    mapping = {}
    cols_norm = {normalize_str(c): c for c in df.columns}
    for target, syns in COL_SYNONYMS.items():
        found = None
        for s in syns:
            if s in cols_norm:
                found = cols_norm[s]
                break
        if found is not None:
            mapping[found] = target
    df2 = df.rename(columns=mapping)
    return df2


def validate_dataframe(df: pd.DataFrame) -> tuple[bool, list]:
    msgs = []
    ok = True
    for c in REQUIRED_COLS:
        if c not in df.columns:
            ok = False
            msgs.append(f"Falta la columna obligatoria: '{c}'")
    # Tipos básicos
    if ok:
        # Coerce year to int
        try:
            df['year'] = pd.to_numeric(df['year'], errors='coerce').astype('Int64')
        except Exception:
            ok = False
            msgs.append("La columna 'year' debe ser numérica (2019–2023).")
        # Coerce numeric cols
        for c in ["nvpov","vpov","pov","epov"]:
            try:
                df[c] = pd.to_numeric(df[c], errors='coerce')
            except Exception:
                ok = False
                msgs.append(f"La columna '{c}' debe ser numérica (conteo de personas).")
        # Region to string
        df['region'] = df['region'].astype(str)
        # Rangos de año
        years = sorted(df['year'].dropna().unique())
        if len(years) == 0 or years[0] > 2019 or years[-1] < 2023:
            msgs.append("Advertencia: se esperaban años 2019–2023 en el panel.")
    return ok, msgs


def peru_total(df: pd.DataFrame) -> pd.DataFrame:
    agg = df.groupby('year', as_index=False)[["nvpov","vpov","pov","epov"]].sum()
    agg.insert(0, 'region', 'Perú (suma nacional)')
    return agg


def fmt_int(x):
    try:
        return f"{int(round(x)):,}".replace(',', '.')
    except Exception:
        return "—"

# --------------------------
# Sidebar – Presentación y carga
# --------------------------
with st.sidebar:
    st.title("📊 Prototipo ciudadano")
    st.markdown(
        """
        **Plataforma de comparación** enfocada en **pobreza** con datos de la 
        **ENAHO – INEI** (2019–2023). Carga tu archivo **Excel** con las columnas:
        
        - `nombre` (o `region`/`departamento`)
        - `year` (2019–2023)
        - `nvpov`, `vpov`, `pov`, `epov`
        
        *(No se realiza scraping en este prototipo; se trabaja con tu Excel.)*
        """
    )
    uploaded = st.file_uploader("Sube el Excel (XLSX)", type=["xlsx","xls"])

# --------------------------
# Tabs principales
# --------------------------
PRESENTACION, DASHBOARD, COMPARADOR = st.tabs([
    "Presentación de la plataforma",
    "Dashboard de pobreza (ENAHO–INEI)",
    "Comparador de propuestas (ficticias)"
])

with PRESENTACION:
    st.header("Plataforma cívica para comparar propuestas con datos verificables")
    st.markdown(
        """
        Esta plataforma busca **acercar la evidencia al ciudadano**: presentamos las 
        cifras de **pobreza** a partir de tu panel **ENAHO–INEI (2019–2023)** y, en paralelo,
        un **comparador de propuestas** de *candidatos ficticios*. El objetivo es 
        **visualizar tendencias**, **cuantificar brechas** y **referenciar la fuente** en todo momento.
        
        **Alcance del prototipo**:
        - Solo se incluye el **módulo de pobreza** (cuatro variables: *nvpov*, *vpov*, *pov*, *epov*).
        - Las propuestas de los candidatos son **ficticias** y se usan solo con fines demostrativos:
          1) **Candidata A – “Mariana Quispe (Andes Unido)”**: propone **reducir a 0** el número de personas en **pobreza extrema (epov)**.
          2) **Candidato B – “Ricardo Navarro (Perú Futuro)”**: propone **reducir a la mitad** el número de personas en **pobreza (pov)**.
        - **Fuente** de datos: *Encuesta Nacional de Hogares (ENAHO), INEI*. 
        
        Para comenzar, sube tu Excel en la barra lateral. Una vez validado, podrás navegar el **dashboard** y el **comparador**.
        """
    )

with DASHBOARD:
    st.subheader("Dashboard de pobreza – ENAHO (INEI)")

    if not uploaded:
        st.info("Sube un Excel con las columnas requeridas para visualizar el dashboard.")
    else:
        try:
            raw = pd.read_excel(uploaded)
            df = match_columns(raw)
            ok, msgs = validate_dataframe(df)
            if not ok:
                st.error("No se pudo validar el archivo. Revisa los mensajes y corrige el Excel.")
                for m in msgs: st.write("• ", m)
            else:
                if msgs:
                    for m in msgs: st.warning(m)

                # Construir nacional y opciones
                total_pe = peru_total(df)
                df_all = pd.concat([total_pe, df.copy()], ignore_index=True)
                regiones = sorted(df['region'].unique().tolist())
                regiones = ["Perú (suma nacional)"] + regiones

                c1, c2 = st.columns([2,1])
                with c1:
                    region_sel = st.selectbox("Ámbito", regiones, index=0)
                with c2:
                    years = sorted(df['year'].dropna().unique())
                    y_min, y_max = (min(years), max(years))
                    rango = st.slider("Años", int(y_min), int(y_max), (int(y_min), int(y_max)))

                # Filtro por región y años
                if region_sel == "Perú (suma nacional)":
                    view = total_pe.copy()
                else:
                    view = df[df['region'] == region_sel].copy()
                view = view[(view['year'] >= rango[0]) & (view['year'] <= rango[1])].sort_values('year')

                # KPIs – último año del rango
                last_year = int(view['year'].max())
                base_year = int(view['year'].min())
                last_row = view[view['year'] == last_year].iloc[0]
                base_row = view[view['year'] == base_year].iloc[0]

                k1, k2, k3, k4 = st.columns(4)
                k1.metric("No pobres no vulnerables (nvpov)", fmt_int(last_row['nvpov']), 
                          f"Δ vs {base_year}: {fmt_int(last_row['nvpov']-base_row['nvpov'])}")
                k2.metric("No pobres vulnerables (vpov)", fmt_int(last_row['vpov']), 
                          f"Δ vs {base_year}: {fmt_int(last_row['vpov']-base_row['vpov'])}")
                k3.metric("Pobreza (pov)", fmt_int(last_row['pov']), 
                          f"Δ vs {base_year}: {fmt_int(last_row['pov']-base_row['pov'])}")
                k4.metric("Pobreza extrema (epov)", fmt_int(last_row['epov']), 
                          f"Δ vs {base_year}: {fmt_int(last_row['epov']-base_row['epov'])}")

                st.markdown("<div class='section'>Tendencias 2019–2023</div>", unsafe_allow_html=True)

                # Series largas para plotly
                long = view.melt(id_vars=["year"], value_vars=["nvpov","vpov","pov","epov"],
                                 var_name="variable", value_name="personas")
                fig = px.line(long, x="year", y="personas", color="variable",
                              markers=True, title=f"{region_sel}: series de pobreza (personas)")
                fig.update_layout(margin=dict(l=0,r=0,t=50,b=0))
                st.plotly_chart(fig, use_container_width=True)

                st.caption("**Fuente**: ENAHO – Instituto Nacional de Estadística e Informática (INEI).")

                with st.expander("Ver tabla (ámbito seleccionado)"):
                    st.dataframe(view.sort_values('year'), use_container_width=True)
        except Exception as e:
            st.error("No se pudo leer el Excel. Asegúrate de que sea un archivo válido (.xlsx) y que contenga las columnas requeridas.")
            st.exception(e)

with COMPARADOR:
    st.subheader("Comparador de propuestas (ficticias)")
    st.markdown(
        """
        En este módulo se muestran **dos propuestas simuladas** para fines de demostración del prototipo:
        
        - **Candidata A – “Mariana Quispe (Andes Unido)”**: *Reducir a **cero** el número de personas en **pobreza extrema (epov)**.*
        - **Candidato B – “Ricardo Navarro (Perú Futuro)”**: *Reducir a la **mitad** el número de personas en **pobreza (pov)**.*
        
        > **Aviso**: Las propuestas son **ficticias** y no representan a candidatos reales.
        """
    )

    if not uploaded:
        st.info("Sube un Excel para calcular brechas frente a las metas propuestas.")
    else:
        try:
            raw2 = pd.read_excel(uploaded)
            df2 = match_columns(raw2)
            ok2, msgs2 = validate_dataframe(df2)
            if not ok2:
                st.error("No se pudo validar el archivo. Revisa los mensajes y corrige el Excel.")
                for m in msgs2: st.write("• ", m)
            else:
                total_pe2 = peru_total(df2)
                regiones2 = ["Perú (suma nacional)"] + sorted(df2['region'].unique().tolist())
                c1, c2 = st.columns([2,1])
                with c1:
                    region_sel2 = st.selectbox("Ámbito", regiones2, index=0, key="cmp_region")
                with c2:
                    years = sorted(df2['year'].dropna().unique())
                    last_year2 = int(max(years))
                    st.write("")
                    st.markdown(f"**Año de referencia:** {last_year2}")

                if region_sel2 == "Perú (suma nacional)":
                    base_view = total_pe2.copy()
                else:
                    base_view = df2[df2['region'] == region_sel2].copy()

                base_last = base_view[base_view['year'] == last_year2].iloc[0]

                # Metas
                target_epov = 0  # Candidata A
                target_pov = base_last['pov'] * 0.5  # Candidato B

                cA, cB = st.columns(2)

                with cA:
                    st.markdown("### Candidata A – Meta epov = 0")
                    cur = base_last['epov']
                    gap = max(cur - target_epov, 0)
                    st.metric("Pobreza extrema actual (epov)", fmt_int(cur), f"Meta: {fmt_int(target_epov)}")
                    figA = px.bar(x=["Actual","Meta"], y=[cur, target_epov], title=f"{region_sel2} – epov: actual vs meta")
                    figA.update_layout(margin=dict(l=0,r=0,t=40,b=0))
                    st.plotly_chart(figA, use_container_width=True)
                    st.info(f"Brecha a cerrar: **{fmt_int(gap)}** personas para alcanzar la meta de 0 en epov.")

                with cB:
                    st.markdown("### Candidato B – Reducir pov a la mitad")
                    cur2 = base_last['pov']
                    gap2 = max(cur2 - target_pov, 0)
                    st.metric("Pobreza actual (pov)", fmt_int(cur2), f"Meta: {fmt_int(target_pov)}")
                    figB = px.bar(x=["Actual","Meta"], y=[cur2, target_pov], title=f"{region_sel2} – pov: actual vs meta (50%)")
                    figB.update_layout(margin=dict(l=0,r=0,t=40,b=0))
                    st.plotly_chart(figB, use_container_width=True)
                    st.info(f"Brecha a cerrar: **{fmt_int(gap2)}** personas para alcanzar la reducción del 50% en pov.")

                st.caption("**Fuente**: ENAHO – Instituto Nacional de Estadística e Informática (INEI). Contenido de propuestas: demostración ficticia.")
        except Exception as e:
            st.error("No se pudo leer el Excel o calcular las métricas.")
            st.exception(e)

# Pie de página
st.markdown("""
---
<div class='caption'>Este es un prototipo académico. No realiza recomendaciones de voto ni representa a actores reales. Cada cifra debe interpretarse en relación con la cobertura y definiciones de ENAHO–INEI.</div>
""", unsafe_allow_html=True)

import streamlit as st
from bs4 import BeautifulSoup
import requests
from datetime import datetime

def obtener_noticias_ipe(url):
    """
    Función para obtener noticias de IPE
    """
    try:
        # Configurar headers para evitar bloqueos
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Realizar la petición HTTP
        respuesta = requests.get(url, headers=headers, timeout=10)
        
        # Verificar si la petición fue exitosa
        if respuesta.status_code == 200:
            soup = BeautifulSoup(respuesta.text, 'html.parser')
            
            # Extraer título y contenido
            titulo = soup.find('h1', class_='entry-title').text.strip()
            contenido = soup.find('div', class_='entry-content').text.strip()
            
            return {
                'titulo': titulo,
                'contenido': contenido,
                'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'url': url
            }
        else:
            st.error(f'Error al obtener la noticia: Código de estado {respuesta.status_code}')
            return None
            
    except Exception as e:
        st.error(f'Error en el scraping: {str(e)}')
        return None

# Crear la pestaña de noticias
st.header('Noticias Relevantes')

urls_noticias = [
    'https://ipe.org.pe/cajamarca-lidera-en-pobreza-y-desigualdad-salarial-en-el-pais/',
    'https://ipe.org.pe/la-pobreza-en-el-peru-afecta-a-1-de-cada-4-ciudadanos/'
]

# Contenedor para las noticias
with st.container():
    for url in urls_noticias:
        noticia = obtener_noticias_ipe(url)
        if noticia:
            col1, col2 = st.columns([2, 1])
            
            # Mostrar información en columnas
            with col1:
                st.subheader(noticia['titulo'])
                st.write(noticia['contenido'][:500] + '...')
                
            with col2:
                st.write(f'Fecha de extracción: {noticia["fecha"]}')
                st.markdown(f'[Ver noticia completa]({noticia["url"]})')
