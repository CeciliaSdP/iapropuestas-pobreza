# Importaciones necesarias (agregar al inicio de tu archivo)
from bs4 import BeautifulSoup
import requests
from datetime import datetime

# Función del scraper (agregar después de tus funciones utilitarias)
def obtener_noticias_ipe(url):
    """
    Función para obtener noticias de IPE
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        respuesta = requests.get(url, headers=headers, timeout=10)
        
        if respuesta.status_code == 200:
            soup = BeautifulSoup(respuesta.text, 'html.parser')
            
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

# Modificar la sección de COMPARADOR para incluir el scraper
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

    # Agregar sección de noticias
    st.subheader("Noticias Relevantes")
    urls_noticias = [
        'https://ipe.org.pe/cajamarca-lidera-en-pobreza-y-desigualdad-salarial-en-el-pais/',
        'https://ipe.org.pe/la-pobreza-en-el-peru-afecta-a-1-de-cada-4-ciudadanos/'
    ]
    
    for url in urls_noticias:
        noticia = obtener_noticias_ipe(url)
        if noticia:
            st.subheader(noticia['titulo'])
            st.write(noticia['contenido'][:500] + '...')
            st.markdown(f'[Ver noticia completa]({noticia["url"]})')
            st.write(f'Fecha de extracción: {noticia["fecha"]}')
            st.markdown("---")

    # Continuar con el resto del código existente del COMPARADOR
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
                # ... resto del código existente del COMPARADOR ...
        except Exception as e:
            st.error("No se pudo leer el Excel o calcular las métricas.")
            st.exception(e)
