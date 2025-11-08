# Importaciones necesarias
import streamlit as st
from bs4 import BeautifulSoup
import requests
from datetime import datetime
import time
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
import pandas as pd
import plotly.express as px
import io
import unicodedata
import numpy as np
import openpyxl

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='scraping_log.txt'
)

# Configuración de la página
st.set_page_config(
    page_title="Comparador ciudadano – Prototipo (ENAHO–INEI)",
    page_icon="📊",
    layout="wide"
)

# Estilos CSS
CUSTOM_CSS = """<style>
:root { --text: #0F172A; --muted:#475569; --brand:#0EA5E9; }
/* Tipografía y jerarquía */
h1, h2, h3 { font-weight: 700; letter-spacing: .2px; }
.section { padding: .6rem 1rem; border-left: 4px solid var(--brand); background: #F8FAFC; margin-bottom: .6rem; }
.kpi { border-radius: 16px; padding: 1rem; border: 1px solid #E2E8F0; background: white; }
.source { color: var(--muted); font-size: .9rem; }
.caption { color: var(--muted); font-size: .85rem; }
hr { border: none; border-top: 1px solid #E2E8F0; margin: .6rem 0; }
</style>"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Funciones utilitarias
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
    """Valida el DataFrame y retorna si es válido y mensajes de error."""
    try:
        msgs = []
        ok = True
        for c in REQUIRED_COLS:
            if c not in df.columns:
                ok = False
                msgs.append(f"Falta la columna obligatoria: '{c}'")
        
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
    except Exception as e:
        logging.error(f"Error al validar el DataFrame: {str(e)}")
        return False, [f"Error al validar el DataFrame: {str(e)}"]

def peru_total(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula el total nacional para cada año."""
    agg = df.groupby('year', as_index=False)[["nvpov","vpov","pov","epov"]].sum()
    agg.insert(0, 'region', 'Perú (suma nacional)')
    return agg

def fmt_int(x):
    """Formatea números enteros con separadores de miles."""
    try:
        return f"{int(round(x)):,}".replace(',', '.')
    except Exception:
        return "—"

# Función del scraper mejorada
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def obtener_noticias_ipe(url):
    """Función para obtener noticias de IPE con manejo robusto de errores."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Implementar delay entre peticiones para evitar sobrecarga
        time.sleep(2)
        
        respuesta = requests.get(url, headers=headers, timeout=15)
        
        if respuesta.status_code == 200:
            soup = BeautifulSoup(respuesta.text, 'html.parser')
            
            try:
                titulo = soup.find('h1', class_='entry-title').text.strip()
                contenido = soup.find('div', class_='entry-content').text.strip()
                
                return {
                    'titulo': titulo,
                    'contenido': contenido,
                    'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'url': url
                }
            except AttributeError as e:
                logging.error(f"Error al extraer contenido de la noticia: {str(e)}")
                st.error(f"Error al extraer el contenido de la noticia: {str(e)}")
                return None
        else:
            logging.error(f"Error HTTP {respuesta.status_code} al obtener la noticia")
            st.error(f"Error al obtener la noticia: Código de estado {respuesta.status_code}")
            return None
            
    except requests.exceptions.ConnectionError as e:
        logging.error(f"Error de conexión: {str(e)}")
        st.error(f"Error de conexión al servidor. Intentando nuevamente...")
        raise
    except requests.exceptions.Timeout as e:
        logging.error(f"Timeout en la petición: {str(e)}")
        st.error(f"La petición tardó demasiado. Intentando nuevamente...")
        raise
    except Exception as e:
        logging.error(f"Error inesperado: {str(e)}")
        st.error(f"Error inesperado al obtener la noticia: {str(e)}")
        return None

# Definir las pestañas
PRESENTACION, DASHBOARD, COMPARADOR = st.tabs([
    "Presentación de la plataforma",
    "Dashboard de pobreza (ENAHO–INEI)",
    "Comparador de propuestas (ficticias)"
])

# Contenido de la pestaña de presentación
with PRESENTACION:
    st.header("Plataforma cívica para comparar propuestas con datos verificables")
    st.markdown("""
        Esta plataforma busca **acercar la evidencia al ciudadano**: presentamos las 
        cifras de **pobreza** a partir de tu panel **ENAHO–INEI (2019–2023)** y, en paralelo,
        un **comparador de propuestas** de *candidatos ficticios*. El objetivo es 
        **visualizar tendencias**, **cuantificar brechas** y **referenciar la fuente** en todo momento.

        **Alcance del prototipo**:
        - Solo se incluye el **módulo de pobreza** (cuatro variables: *nvpov*, *vpov*, *pov*, *epov*).
        - Las propuestas de los candidatos son **ficticias** y se usan solo con fines demostrativos:
          1) **Candidata A – "Mariana Quispe (Andes Unido)"**: propone **reducir a cero** el número de personas en **pobreza extrema (epov)**.
          2) **Candidato B – "Ricardo Navarro (Perú Futuro)"**: propone **reducir a la mitad** el número de personas en **pobreza (pov)**.
        - **Fuente** de datos: *Encuesta Nacional de Hogares (ENAHO), INEI*.

        Para comenzar, sube tu Excel en la barra lateral. Una vez validado, podrás navegar el **dashboard** y el **comparador**
