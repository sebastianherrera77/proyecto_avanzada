import streamlit as st
import pandas as pd
import altair as alt
import matplotlib.pyplot as plt
import warnings
import base64

# Suprimir warnings de deprecación
warnings.filterwarnings('ignore', category=DeprecationWarning)

# Función para cargar imagen de fondo
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

# Configurar el fondo y estilos
def set_background_and_style(image_path):
    base64_img = get_base64_image(image_path)
    
    if base64_img:
        # Con imagen de fondo
        page_bg = f"""
        <style>
        /* Fondo general */
        .stApp {{
            background-image: url("data:image/png;base64,{base64_img}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        
        /* Fuente global */
        * {{
            font-family: Arial, Helvetica, sans-serif !important;
        }}
        
        /* Sidebar con imagen de fondo */
        [data-testid="stSidebar"] {{
            background-image: url("data:image/png;base64,{base64_img}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }}
        
        /* Contenido del sidebar con transparencia */
        [data-testid="stSidebar"] > div:first-child {{
            background-color: rgba(255, 255, 255, 0.9);
            padding: 1rem;
            border-radius: 10px;
        }}
        
        /* Contenido principal con fondo semi-transparente */
        .main .block-container {{
            background-color: rgba(255, 255, 255, 0.85);
            padding: 2rem;
            border-radius: 10px;
        }}
        
        /* Títulos */
        h1, h2, h3 {{
            font-weight: 700 !important;
        }}
        
        /* Botones */
        .stButton>button {{
            font-weight: 500 !important;
        }}
        </style>
        """
    else:
        # Sin imagen de fondo (solo fuente)
        page_bg = """
        <style>
        * {{
            font-family: Arial, Helvetica, sans-serif !important;
        }}
        
        h1, h2, h3 {{
            font-weight: 700 !important;
        }}
        
        .stButton>button {{
            font-weight: 500 !important;
        }}
        </style>
        """
    
    st.markdown(page_bg, unsafe_allow_html=True)

# Configuración de la página
st.set_page_config(page_title="Dashboard de Residuos", layout="wide")

# ⚠️ CAMBIA AQUÍ EL NOMBRE DE TU IMAGEN DE FONDO ⚠️
# Ejemplos: "fondo.jpg", "background.png", "mi_fondo.jpeg"
set_background_and_style("fondo.png")

# Cargar datos
@st.cache_data
def load_data():
    return pd.read_csv("dataser.csv", sep=";")

df = load_data()

# Obtener columnas de residuos
res_cols = [c for c in df.columns if "RESIDUO" in c.upper() or "ENVOLT" in c.upper()]

# Menú lateral
st.sidebar.title("MENÚ")
opcion = st.sidebar.radio(
    "Navegación",
    ["INICIO", "GRÁFICAS", "NOSOTROS"]
)

# ==================== PÁGINA DE INICIO ====================
if opcion == "INICIO":
    st.title("🌍 SISTEMA DE ANÁLISIS DE RESIDUOS SÓLIDOS")
    st.markdown("---")
    
    # Aquí puedes agregar tu imagen
    st.image("logo.png", use_container_width=True)
    st.markdown("""
    ### Bienvenido al Dashboard de Análisis de Residuos
    
    Esta aplicación te permite visualizar y analizar datos sobre residuos sólidos 
    en diferentes departamentos, provincias y distritos del Perú.
    
    **Características principales:**
    - 📊 Visualización de residuos por departamento
    - 🥧 Top 5 distritos con más residuos
    - 📈 Evolución temporal de residuos
    - 🏆 Distritos más limpios (menor residuo per cápita)
    
    👈 **Usa el menú lateral para navegar**
    """)

# ==================== PÁGINA DE GRÁFICAS ====================
elif opcion == "GRÁFICAS":
    st.title("📊 ANÁLISIS DE GRÁFICAS")
    st.markdown("### Selecciona una gráfica para visualizar:")
    
    # Crear 4 columnas para los botones
    col1, col2, col3, col4 = st.columns(4)
    
    # Inicializar la variable en session_state si no existe
    if 'grafica_seleccionada' not in st.session_state:
        st.session_state.grafica_seleccionada = None
    
    # Botones en cada columna
    with col1:
        if st.button("📊 Residuos por Departamento", use_container_width=True):
            st.session_state.grafica_seleccionada = "Gráfica 1"
    
    with col2:
        if st.button("🥧 Top 5 Distritos", use_container_width=True):
            st.session_state.grafica_seleccionada = "Gráfica 2"
    
    with col3:
        if st.button("📈 Evolución Temporal", use_container_width=True):
            st.session_state.grafica_seleccionada = "Gráfica 3"
    
    with col4:
        if st.button("🏆 Distritos Más Limpios", use_container_width=True):
            st.session_state.grafica_seleccionada = "Gráfica 4"
    
    st.markdown("---")
    
    tipo_grafica = st.session_state.grafica_seleccionada
    
    # ==================== GRÁFICA 1 ====================
    if tipo_grafica == "Gráfica 1":
        st.header("📊 CANTIDAD TOTAL DE RESIDUOS POR DEPARTAMENTO")
        
        col1, col2 = st.columns(2)
        
        años = sorted(df["PERIODO"].unique())
        with col1:
            año_sel = st.selectbox("Selecciona el año (PERIODO)", años, key="g1_año")
        with col2:
            res_sel = st.selectbox("Selecciona el tipo de residuo", res_cols, key="g1_res")
        
        ocultar_lima = st.checkbox("Ocultar departamento de Lima", key="g1_lima")
        
        # Procesamiento de datos
        df_fil = df[df["PERIODO"] == año_sel]
        df_dep = df_fil.groupby("DEPARTAMENTO")[res_sel].sum().reset_index()
        df_dep = df_dep.sort_values("DEPARTAMENTO")
        
        if ocultar_lima:
            df_dep = df_dep[df_dep["DEPARTAMENTO"].str.upper() != "LIMA"]
        
        # Gráfica
        chart = (
            alt.Chart(df_dep)
            .mark_bar()
            .encode(
                x=alt.X("DEPARTAMENTO:N", sort=None),
                y=alt.Y(f"{res_sel}:Q"),
                tooltip=["DEPARTAMENTO", res_sel]
            )
        )
        st.altair_chart(chart, use_container_width=True)
        
        # Espacio para comentarios
        st.markdown("---")
        st.subheader("💬 Análisis y Comentarios")
        st.write("Aquí puedes agregar tus comentarios sobre esta gráfica...")
    
    # ==================== GRÁFICA 2 ====================
    elif tipo_grafica == "Gráfica 2":
        st.header("🥧 TOP 5 DISTRITOS CON MÁS RESIDUOS")
        
        col1, col2, col3 = st.columns(3)
        
        anios = sorted(df["PERIODO"].unique())
        departamentos = sorted(df["DEPARTAMENTO"].unique())
        
        with col1:
            anio_sel = st.selectbox("Selecciona el año (PERIODO)", anios, key="g2_año")
        with col2:
            res_sel = st.selectbox("Selecciona el tipo de residuo", res_cols, key="g2_res")
        with col3:
            dep_sel = st.selectbox("Selecciona el departamento", departamentos, key="g2_dep")
        
        # Procesamiento de datos
        df_fil = df[(df["PERIODO"] == anio_sel) & (df["DEPARTAMENTO"] == dep_sel)]
        df_top5 = df_fil.groupby("DISTRITO")[res_sel].sum().reset_index()
        df_top5 = df_top5.sort_values(res_sel, ascending=False).head(5)
        
        # Gráfica
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.pie(
            df_top5[res_sel],
            labels=df_top5["DISTRITO"],
            autopct="%1.1f%%",
            startangle=90
        )
        ax.axis("equal")
        st.pyplot(fig)
        
        # Espacio para comentarios
        st.markdown("---")
        st.subheader("💬 Análisis y Comentarios")
        st.write("Aquí puedes agregar tus comentarios sobre esta gráfica...")
    
    # ==================== GRÁFICA 3 ====================
    elif tipo_grafica == "Gráfica 3":
        st.header("📈 EVOLUCIÓN DE RESIDUOS POR DISTRITO")
        
        col1, col2 = st.columns(2)
        
        departamentos = sorted(df["DEPARTAMENTO"].unique())
        
        with col1:
            dep_sel = st.selectbox("Selecciona el departamento", departamentos, key="g3_dep")
        
        prov_df = df[df["DEPARTAMENTO"] == dep_sel]
        provincias = sorted(prov_df["PROVINCIA"].unique())
        
        with col2:
            prov_sel = st.selectbox("Selecciona la provincia", provincias, key="g3_prov")
        
        col3, col4 = st.columns(2)
        
        dist_df = prov_df[prov_df["PROVINCIA"] == prov_sel]
        distritos = sorted(dist_df["DISTRITO"].unique())
        
        with col3:
            dist_sel = st.selectbox("Selecciona el distrito", distritos, key="g3_dist")
        with col4:
            res_sel = st.selectbox("Selecciona el tipo de residuo", res_cols, key="g3_res")
        
        # Procesamiento de datos
        df_fil = df[
            (df["DEPARTAMENTO"] == dep_sel) &
            (df["PROVINCIA"] == prov_sel) &
            (df["DISTRITO"] == dist_sel)
        ].sort_values("PERIODO")
        
        chart_data = df_fil.set_index("PERIODO")[[res_sel]]
        
        # Gráfica
        st.line_chart(chart_data)
        
        # Espacio para comentarios
        st.markdown("---")
        st.subheader("💬 Análisis y Comentarios")
        st.write("Aquí puedes agregar tus comentarios sobre esta gráfica...")
    
    # ==================== GRÁFICA 4 ====================
    elif tipo_grafica == "Gráfica 4":
        st.header("🏆 DISTRITOS MÁS LIMPIOS (MENOR RESIDUO PER CÁPITA)")
        
        col1, col2, col3 = st.columns(3)
        
        departamentos = sorted(df["DEPARTAMENTO"].unique())
        anios = sorted(df["PERIODO"].unique())
        
        with col1:
            dep_sel = st.selectbox("Selecciona el departamento", departamentos, key="g4_dep")
        with col2:
            res_sel = st.selectbox("Selecciona el tipo de residuo", res_cols, key="g4_res")
        with col3:
            anio_sel = st.selectbox("Selecciona el año (PERIODO)", anios, key="g4_año")
        
        # Procesamiento de datos
        df_fil = df[
            (df["DEPARTAMENTO"] == dep_sel) &
            (df["PERIODO"] == anio_sel)
        ].copy()
        
        df_fil["RESIDUO_PERCAPITA"] = df_fil[res_sel] / df_fil["POB_TOTAL"]
        df_top = df_fil[["DISTRITO", "RESIDUO_PERCAPITA"]].sort_values("RESIDUO_PERCAPITA").head(5)
        
        # Gráfica
        chart = (
            alt.Chart(df_top)
            .mark_bar()
            .encode(
                x=alt.X("DISTRITO:N", sort=None),
                y=alt.Y("RESIDUO_PERCAPITA:Q"),
                tooltip=["DISTRITO", "RESIDUO_PERCAPITA"]
            )
        )
        st.altair_chart(chart, use_container_width=True)
        
        # Espacio para comentarios
        st.markdown("---")
        st.subheader("💬 Análisis y Comentarios")
        st.write("Aquí puedes agregar tus comentarios sobre esta gráfica...")

# ==================== PÁGINA DE NOSOTROS ====================
elif opcion == "NOSOTROS":
    st.title("👥 SOBRE NOSOTROS")
    st.markdown("---")
    
    st.markdown("""
    ## Equipo del Proyecto
    
    Este proyecto fue desarrollado por:
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 👤 INTEGRANTE 1
        **Nombre:** EMMY ABIGAYL DEL ROSARIO LOPEZ CUEVA
        
        **Rol:** JEFA
        
        """)
    
    with col2:
        st.markdown("""
        ### 👤 INTEGRANTE 2
        **Nombre:** WILMER SEBASTIAN HERRERA NEIRA
        
        **Rol:** ESPECTADOR       

        """)

    st.markdown("---")
    st.markdown("""
    ### 📝 Sobre el Proyecto
    
    Este dashboard fue desarrollado como parte de un proyecto de análisis de residuos sólidos,
    con el objetivo de proporcionar información clara y visual sobre la gestión de residuos
    en diferentes regiones del país.
    
    **Tecnologías utilizadas:**
    - Python 3.x
    - Streamlit
    - Pandas
    - Altair
    - Matplotlib
    """)

# Footer
st.sidebar.markdown("---")
st.sidebar.info("VIVA EL PERU, VIVA EGINHARDO, VIVA EL FORNAIT")
