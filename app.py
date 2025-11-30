# app.py 
# Combina: app, KPIs, Graphics, Informacion, Map_loader y estilos en un solo archivo.
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
import json
import os

# ---------------------------------------------------------------------
# Configuración inicial
# ---------------------------------------------------------------------
st.set_page_config(    #configuración antes de que se renderice el contenido
    page_title="Dashboard de Residuos", # titulo de la pestaña
    page_icon="📊", # icono de la pestaña
    layout="wide" #diseño horizontal de la página, para que el contenido se extienda a todo el ancho completo.
)

# ---------------------------------------------------------------------
# CSS 
# ---------------------------------------------------------------------
_STYLES = """
.stApp {   
    background-color: #000000;
    color: white;
}

/* Fondo del sidebar */
[data-testid="stSidebar"] {
    background-color: #1a1d23a1;
    color: white; /* texto normal en blanco */
}

"""

st.markdown(f"<style>{_STYLES}</style>", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Rutas por defecto 
# ---------------------------------------------------------------------
CSV_PATH = os.path.join("Data", "dataset.csv") #creamos la ruta del archivo de forma segura
GEOJSON_PATH = os.path.join("Data", "departamentos_peru.geojson")

# ---------------------------------------------------------------------
# CARGA DE DATOS (una sola vez)
# ---------------------------------------------------------------------
@st.cache_data  #guarda en cache el resultado de esta función para recalcularla cada vez que se actualice la página
def load_data(csv_path=CSV_PATH): #toma como parametro la ruta del archivo
    df = pd.read_csv(csv_path, sep=";", encoding="utf-8-sig") # lee el archivo, con su delimitador y asegura que se lea los caracteres especiales.
    # Normalizar columnas y valores
    df.columns = df.columns.str.strip().str.upper() 
    # strip: elimina los espacios al inicio y final de la columna
    # upper: convertimos todo a mayusculas para evitar errores
    if "DEPARTAMENTO" in df.columns:
        df["DEPARTAMENTO"] = df["DEPARTAMENTO"].astype(str).str.upper().str.strip() 
    if "PERIODO" in df.columns:
        df["PERIODO"] = pd.to_numeric(df["PERIODO"], errors="coerce")
    return df

    # int64 : valores enteros convertibles
    # float64: NaN o valores no convertibles

df = load_data()

# ---------------------------------------------------------------------
# KPIs (Indicadores clave) : Resumen instanteno de métricas clave 
# ---------------------------------------------------------------------
def calcular_kpis(df_local):
    """
    Calcula todos los KPIs del dashboard.
    """
    # KPI 1: Toneladas totales
    total_residuos = df_local["QRESIDUOS_DOM"].sum()

    # KPI 2: Departamento con más residuos
    res_por_depa = df_local.groupby("DEPARTAMENTO")["QRESIDUOS_DOM"].sum()
    depa_max = res_por_depa.idxmax() if not res_por_depa.empty else "Sin datos"
    depa_max_valor = res_por_depa.max() if not res_por_depa.empty else 0.0

    # KPI 3: Residuo más abundante
    columnas_residuos = [
        col for col in df_local.columns
        if col.startswith("QRESIDUOS_") and col != "QRESIDUOS_DOM"
    ]
    suma_residuos = df_local[columnas_residuos].sum() if columnas_residuos else pd.Series()
    residuo_mas_abundante = suma_residuos.idxmax() if not suma_residuos.empty else "Sin datos"
    valor_residuo_mas_abundante = suma_residuos.max() if not suma_residuos.empty else 0.0

    # KPI 4: Población total
    poblacion_total = df_local["POB_TOTAL"].sum() if "POB_TOTAL" in df_local.columns else 0.0

    return {
        "total_residuos": total_residuos,
        "depa_max": depa_max,
        "depa_max_valor": depa_max_valor,
        "residuo_mas_abundante": residuo_mas_abundante,
        "valor_residuo_mas_abundante": valor_residuo_mas_abundante,
        "poblacion_total": poblacion_total
    }

def mostrar_kpis(df_local):
    """
    Muestra los KPIs en la interfaz de Streamlit.
    """
    st.subheader("📊 Indicadores Generales")  # subtitulo para dar contexto
    kpis = calcular_kpis(df_local)   #guarda el diccionario de la función anterior en esta variable

    col1, col2, col3, col4 = st.columns(4) # 4 columnas para mostrar en paralelo

    with col1:
        st.metric(   # muestra un indicador con valor destacado
            label="Toneladas Totales de Residuos",
            value=f"{kpis['total_residuos']:,.2f} T"
        )

    with col2:
        st.metric(
            label="Departamento con más residuos",
            value=kpis['depa_max'],
            delta=f"{kpis['depa_max_valor']:,.2f} T"  # valor secundario
        )

    with col3:
        nombre_residuo = kpis['residuo_mas_abundante'].replace("QRESIDUOS_", "").replace("_", " ").title() if kpis['residuo_mas_abundante'] != "Sin datos" else "Sin datos"
        st.metric(
            label="Residuo más abundante",
            value=nombre_residuo,
            delta=f"{kpis['valor_residuo_mas_abundante']:,.2f} T"
        )

    with col4:
        st.metric(
            label="Población cubierta",
            value=f"{kpis['poblacion_total']:,.0f}",
            delta="personas"
        )

# ---------------------------------------------------------------------
# Graphics
# ---------------------------------------------------------------------
def grafica_residuos_por_departamento(df_local, periodo=None, tipo_residuo="QRESIDUOS_DOM", ocultar_lima=False):
    if periodo is not None:
        df_filtrado = df_local[df_local["PERIODO"] == periodo].copy()
    else:
        df_filtrado = df_local.copy()

    df_depto = df_filtrado.groupby("DEPARTAMENTO")[tipo_residuo].sum().reset_index()
    if ocultar_lima:
        df_depto = df_depto[df_depto["DEPARTAMENTO"].str.upper() != "LIMA"]
    df_depto = df_depto.sort_values(by=tipo_residuo, ascending=False)
    nombre_residuo = tipo_residuo.replace("QRESIDUOS_", "").replace("_", " ").title()

    fig = px.bar(
        df_depto,
        x="DEPARTAMENTO",
        y=tipo_residuo,
        title=f"Residuos de {nombre_residuo} por Departamento" + (f" - {periodo}" if periodo else " (Total)"),
        labels={"DEPARTAMENTO": "Departamento", tipo_residuo: f"Toneladas de {nombre_residuo}"},
        color=tipo_residuo,
        color_continuous_scale="Reds"
    )
    fig.update_layout(xaxis_tickangle=-45, height=500, showlegend=False, xaxis_title="Departamento", yaxis_title=f"Toneladas de {nombre_residuo}")
    return fig

def grafica_evolucion_temporal(df_local, departamento=None, provincia=None, distrito=None, tipo_residuo="QRESIDUOS_DOM"):
    df_filtrado = df_local.copy()
    if departamento:
        df_filtrado = df_filtrado[df_filtrado["DEPARTAMENTO"] == departamento]
    if provincia:
        df_filtrado = df_filtrado[df_filtrado["PROVINCIA"] == provincia]
    if distrito:
        df_filtrado = df_filtrado[df_filtrado["DISTRITO"] == distrito]

    df_tiempo = df_filtrado.groupby("PERIODO")[tipo_residuo].sum().reset_index()
    df_tiempo = df_tiempo.sort_values("PERIODO")
    nombre_residuo = tipo_residuo.replace("QRESIDUOS_", "").replace("_", " ").title()

    titulo = f"Evolución Temporal de {nombre_residuo}"
    if distrito:
        titulo += f" - {distrito}"
    elif provincia:
        titulo += f" - {provincia}"
    elif departamento:
        titulo += f" - {departamento}"
    else:
        titulo += " - Nacional"

    fig = px.line(df_tiempo, x="PERIODO", y=tipo_residuo, title=titulo, labels={"PERIODO": "Año", tipo_residuo: f"Toneladas de {nombre_residuo}"}, markers=True)
    fig.update_traces(line_color="#E74C3C", line_width=3, marker=dict(size=8))
    fig.update_layout(height=500, xaxis_title="Año", yaxis_title=f"Toneladas de {nombre_residuo}", hovermode='x unified')
    return fig

def grafica_top_departamentos(df_local, top_n=10):
    df_depto = df_local.groupby("DEPARTAMENTO")["QRESIDUOS_DOM"].sum().reset_index()
    df_top = df_depto.nlargest(top_n, "QRESIDUOS_DOM")
    fig = px.bar(df_top, x="QRESIDUOS_DOM", y="DEPARTAMENTO", orientation='h', title=f"Top {top_n} Departamentos con Más Residuos", labels={"DEPARTAMENTO": "Departamento", "QRESIDUOS_DOM": "Toneladas de Residuos"}, color="QRESIDUOS_DOM", color_continuous_scale="YlOrRd")
    fig.update_layout(height=500, showlegend=False)
    return fig

def grafica_tipos_residuos(df_local, departamento, anio, tipo_residuo, top_n=5):
    """
    Devuelve un gráfico de pastel de los distritos que más residuos producen
    para un departamento, año y tipo de residuo específico.
    """
    # Filtrar el DataFrame
    df_fil = df_local[
        (df_local["PERIODO"] == anio) &
        (df_local["DEPARTAMENTO"] == departamento)
    ]

    # Top distritos por residuo
    df_top = df_fil.groupby("DISTRITO")[tipo_residuo].sum().reset_index()
    df_top = df_top.sort_values(tipo_residuo, ascending=False).head(top_n)

    # Crear gráfico Plotly
    fig = px.pie(
        df_top,
        values=tipo_residuo,
        names="DISTRITO",
        title=f"Top {top_n} Distritos con más {tipo_residuo.replace('QRESIDUOS_', '').replace('_', ' ').title()} - {departamento} ({anio})",
        hole=0.4
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=500)

    return fig

def grafica_distritos_limpios(
    df_local, 
    departamento, 
    periodo, 
    tipo_residuo="QRESIDUOS_DOM", 
    top_n=10
):
    # Filtrar por departamento y periodo
    df_filtrado = df_local[
        (df_local["DEPARTAMENTO"] == departamento) & 
        (df_local["PERIODO"] == periodo)
    ].copy()
    
    # Calcular residuo per cápita
    df_filtrado["RESIDUO_PERCAPITA"] = df_filtrado.apply(
        lambda row: row[tipo_residuo] / row["POB_TOTAL"] 
        if row.get("POB_TOTAL", 0) and row["POB_TOTAL"] > 0 else 0, 
        axis=1
    )
    
    # Eliminar filas con población <= 0
    df_filtrado = df_filtrado[df_filtrado["POB_TOTAL"] > 0]
    
    # Seleccionar top distritos más limpios
    df_top = df_filtrado[
        ["DISTRITO", "RESIDUO_PERCAPITA", tipo_residuo, "POB_TOTAL"]
    ].sort_values("RESIDUO_PERCAPITA").head(top_n)
    
    # Formatear nombre del residuo
    nombre_residuo = tipo_residuo.replace("QRESIDUOS_", "").replace("_", " ").title()
    
    # Crear gráfico de barras
    fig = px.bar(
        df_top,
        x="DISTRITO",
        y="RESIDUO_PERCAPITA",
        title=f"🏆 Top {top_n} Distritos Más Limpios - {nombre_residuo}<br>{departamento} ({periodo})",
        labels={
            "DISTRITO": "Distrito",
            "RESIDUO_PERCAPITA": "Toneladas per cápita"
        },
        color="RESIDUO_PERCAPITA",
        color_continuous_scale="Greens_r",
        hover_data={
            "RESIDUO_PERCAPITA": ":.6f",
            tipo_residuo: ":.2f",
            "POB_TOTAL": ":,"
        }
    )
    
    # Ajustes de diseño
    fig.update_layout(
        xaxis_tickangle=-45,
        height=500,
        showlegend=False,
        xaxis_title="Distrito",
        yaxis_title="Toneladas per cápita (menor = más limpio)"
    )
    
    # Personalizar tooltip (hover)
    fig.update_traces(
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Per cápita: %{y:.6f} t/hab<br>"
            f"Total {nombre_residuo}: %{{customdata[0]:.2f}} t<br>"
            "Población: %{customdata[1]:,}<br>"
            "<extra></extra>"
        )
    )
    
    return fig


def mostrar_graficas(df_local):
    st.subheader("📊 Gráficas Interactivas")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Por Departamento", "📅 Evolución Temporal", "🏆 Top Departamentos", "🔍 Tipos de Residuo", "🌟 Distritos Más Limpios"])

    with tab1:
        st.markdown("### Cantidad Total de Residuos por Departamento")
        columnas_residuos = ["QRESIDUOS_DOM"] + [col for col in df_local.columns if col.startswith("QRESIDUOS_") and col != "QRESIDUOS_DOM"]
        nombres_legibles = {col: col.replace("QRESIDUOS_", "").replace("_", " ").title() for col in columnas_residuos}

        col1, col2 = st.columns(2)
        with col1:
            periodos = sorted(df_local["PERIODO"].unique())
            periodo_sel = st.selectbox("📅 Selecciona el año (PERIODO)", periodos, key="g1_periodo")
        with col2:
            tipo_residuo_legible = st.selectbox("🗑️ Selecciona el tipo de residuo", options=list(nombres_legibles.values()), key="g1_tipo")
            tipo_residuo = [k for k, v in nombres_legibles.items() if v == tipo_residuo_legible][0]

        ocultar_lima = st.checkbox("🚫 Ocultar departamento de Lima", value=False, key="g1_lima", help="Lima puede tener valores muy altos que dificultan ver otros departamentos")
        fig = grafica_residuos_por_departamento(df_local, periodo=periodo_sel, tipo_residuo=tipo_residuo, ocultar_lima=ocultar_lima)
        st.plotly_chart(fig, use_container_width=True)
        st.info("📌 Esta gráfica muestra el total de residuos por departamento. Puedes filtrar por año y tipo de residuo.")
        st.markdown("---")
        st.subheader("💬 Análisis y Comentarios")
        st.write("""
         Al analizar la cantidad un residuo en especifico de cada departamento pensamos que
         la diferencia no seria tan abrumante, pues nos equivocamos, la cantidad de habitantes de Lima 
         es tan grande que esto provoca que haya muchisimos mas residuos. Como podemos visualizar 
         se muestra que siempre Lima es el que lidera todos los graficos posibles y por haber, eso si... 
         notamos que los departamentos costeros son aquellos que también tienen valores muy altos a comparación 
         de los de la sierra y selva peruana, muchos aumentan alarmantemente con respecto a sus años 
         anteriores y eso nos genera una preocupación. Esta tabla tiene como finalidad el que el estado Peruano 
         pueda los lugares que mas necesitan atención para controlar la cantidad de residuos. Como mencionamos antes 
         el departamento de Lima tiene cifras muy superiores al resto, por ende, decidimos darle al usuario la opción
         de mostrar o no este departamento con el fin de que la grafica muestre mejor la comparativa por 
         departamento.
            """)

    with tab2:
        st.markdown("### Evolución Temporal de Residuos")
        columnas_residuos = ["QRESIDUOS_DOM"] + [col for col in df_local.columns if col.startswith("QRESIDUOS_") and col != "QRESIDUOS_DOM"]
        nombres_legibles = {col: col.replace("QRESIDUOS_", "").replace("_", " ").title() for col in columnas_residuos}

        col1, col2 = st.columns(2)
        with col1:
            departamentos = ["Todos"] + sorted(df_local["DEPARTAMENTO"].unique().tolist())
            dep_sel = st.selectbox("🏛️ Selecciona el departamento", departamentos, key="g2_dep")
        if dep_sel != "Todos":
            prov_df = df_local[df_local["DEPARTAMENTO"] == dep_sel]
            provincias = ["Todas"] + sorted(prov_df["PROVINCIA"].unique().tolist())
        else:
            provincias = ["Todas"]
        with col2:
            prov_sel = st.selectbox("🏙️ Selecciona la provincia", provincias, key="g2_prov", disabled=(dep_sel == "Todos"))

        if dep_sel != "Todos" and prov_sel != "Todas":
            dist_df = df_local[(df_local["DEPARTAMENTO"] == dep_sel) & (df_local["PROVINCIA"] == prov_sel)]
            distritos = ["Todos"] + sorted(dist_df["DISTRITO"].unique().tolist())
        else:
            distritos = ["Todos"]

        col3, col4 = st.columns(2)
        with col3:
            dist_sel = st.selectbox("🏘️ Selecciona el distrito", distritos, key="g2_dist", disabled=(prov_sel == "Todas" or dep_sel == "Todos"))
        with col4:
            tipo_residuo_legible = st.selectbox("🗑️ Selecciona el tipo de residuo", options=list(nombres_legibles.values()), key="g2_tipo")
            tipo_residuo = [k for k, v in nombres_legibles.items() if v == tipo_residuo_legible][0]

        dep_param = None if dep_sel == "Todos" else dep_sel
        prov_param = None if prov_sel == "Todas" else prov_sel
        dist_param = None if dist_sel == "Todos" else dist_sel

        fig = grafica_evolucion_temporal(df_local, departamento=dep_param, provincia=prov_param, distrito=dist_param, tipo_residuo=tipo_residuo)
        st.plotly_chart(fig, use_container_width=True)
        st.info("📌 Esta gráfica muestra cómo ha evolucionado la cantidad de residuos a lo largo del tiempo. Puedes filtrar por ubicación específica.")
        st.markdown("---")
        st.subheader("💬 Análisis y Comentarios")
        st.write(""" Un método muy práctico para saber si un distrito es saludable o no es ver como ha ido 
            evolucionando a lo largo de los años que se estudió. No podemos predecir al 100% si a futuro 
            ese distrito mejorará muchisimo o empereorá pero si nos dan una idea al analizar como fue la 
            cantidad de recursos en esos 4 años de estudio. Por esto al analizar distrito por distrito notamos que
            distritos limeños, en especifico los de la provincia de Lima mayormente tienden a aumentar 
            la cantidad de residuos en la mayoria de tipos de residuos. Por el contrario hay distritos un poco 
            más alejados que tienden a hacer todo lo contrario, reducen la producción de residuos. Esto podemos usarlo
            a futuro para empezar a predecir con mas precisión si tendrán evolución positiva o negativa.
            """)

    with tab3:
        top_n = st.slider("Selecciona cuántos departamentos mostrar:", 5, 20, 10)
        st.plotly_chart(grafica_top_departamentos(df_local, top_n), use_container_width=True)
        st.info(f"📌 Esta gráfica muestra los {top_n} departamentos con mayor cantidad de residuos.")

    with tab4:
        # Selecciones fuera de la función
        col1, col2, col3 = st.columns(3)
        with col1:
            departamentos = sorted(df_local["DEPARTAMENTO"].unique())
            dep_sel = st.selectbox("🏛️ Selecciona el departamento", departamentos, key="tab4_dep")
        with col2:
            periodos = sorted(df_local["PERIODO"].unique())
            anio_sel = st.selectbox("📅 Selecciona el año", periodos, key="tab4_anio")
        with col3:
            res_cols = [col for col in df_local.columns if col.startswith("QRESIDUOS_")]
            tipo_residuo_legible = st.selectbox("🗑️ Selecciona el tipo de residuo", options=res_cols, key="tab4_res")
            tipo_residuo = tipo_residuo_legible  # ya es el nombre real de la columna
    
        fig = grafica_tipos_residuos(df_local, departamento=dep_sel, anio=anio_sel, tipo_residuo=tipo_residuo)
        st.plotly_chart(fig, use_container_width=True)
        st.info("📌 Esta gráfica muestra la distribución de los diferentes tipos de residuos.")
        st.markdown("---")
        st.subheader("💬 Análisis y Comentarios")
        st.write("""Esta gráfica muestra los distritos que más residuos producen según el residuo que 
            queremos analizar, estos datos de distritos con mas residuos coinciden con los distritos con 
            más población, ¿Más que obvio no? , si bien es cierto esto deberia ser lo esperado no significa 
            que sea lo correcto, el territoria muchas veces es pequeño a comparación del resto de distritos,
            esto hace que la calidad de vida de los habitantes pueda ser mala o perjudicial
            """)

    with tab5:
        st.markdown("### 🌟 Distritos Más Limpios (Menor Residuo Per Cápita)")
        columnas_residuos = ["QRESIDUOS_DOM"] + [col for col in df_local.columns if col.startswith("QRESIDUOS_") and col != "QRESIDUOS_DOM"]
        nombres_legibles = {col: col.replace("QRESIDUOS_", "").replace("_", " ").title() for col in columnas_residuos}

        col1, col2, col3 = st.columns(3)
        with col1:
            departamentos = sorted(df_local["DEPARTAMENTO"].unique().tolist())
            dep_sel = st.selectbox("🏛️ Selecciona el departamento", departamentos, key="g5_dep")
        with col2:
            periodos = sorted(df_local["PERIODO"].unique())
            periodo_sel = st.selectbox("📅 Selecciona el año", periodos, key="g5_periodo")
        with col3:
            tipo_residuo_legible = st.selectbox("🗑️ Selecciona el tipo de residuo", options=list(nombres_legibles.values()), key="g5_tipo")
            tipo_residuo = [k for k, v in nombres_legibles.items() if v == tipo_residuo_legible][0]

        top_n = st.slider("¿Cuántos distritos mostrar?", min_value=5, max_value=20, value=10, key="g5_top")
        fig = grafica_distritos_limpios(df_local, departamento=dep_sel, periodo=periodo_sel, tipo_residuo=tipo_residuo, top_n=top_n)
        st.plotly_chart(fig, use_container_width=True)
        st.success("✨ Esta gráfica muestra los distritos con MENOR generación de residuos per cápita (toneladas por habitante). ¡Valores más bajos indican distritos más limpios!")
        st.markdown("---")
        st.subheader("💬 Análisis y Comentarios")
        st.write("""Por ultimo quisimos poner un apartado cuyo propósito sea el de mencionar aquellos
            distritos más limpios, es decir con menos cantidad de residuos expulsados en un año especifico.
            Esta idea surgio con el fin de buscar distritos que puedan ofrecer mejor calidad de vida. Es notorio 
            que distritos urbanizados como los de Lima metropolitana tiendan a ser muy contaminados y estos
            traigan problemas a los habitantes. El estado a su vez podria usar esta gráfica para seguir
            conservando estos distritos y seguir mejorandolos. Esta grafica demuestra que la centralización y urbanización
            lo que hizo fue traer consigo más residuos que buscan, en su mayoria, contaminar las ciudades.
            """)

# ---------------------------------------------------------------------
# Informacion (unificado)
# ---------------------------------------------------------------------
def mostrar_descripcion_proyecto():
    st.markdown("""
    ### 📋 Acerca del Dashboard

    Este dashboard ha sido diseñado para analizar, visualizar y comprender la
    generación de residuos sólidos domiciliarios en los distintos departamentos
    del Perú. Su propósito es brindar una herramienta clara, accesible y
    dinámica para la toma de decisiones y el estudio de patrones ambientales.

    #### 🎯 Funcionalidades principales:

    - **Indicadores Clave (KPIs)**: Resumen instantáneo de métricas relevantes.
    - **Mapa Interactivo**: Visualización geoespacial por departamento y periodo.
    - **Gráficas Analíticas**: Tendencias, comparaciones y distribución de residuos.
    - **Filtros dinámicos**: Permiten explorar los datos desde diferentes perspectivas.

    #### 📊 Fuente de datos:

    La información proviene de registros oficiales relacionados con la gestión
    de residuos sólidos domiciliarios en el Perú. Estos datos permiten realizar
    análisis históricos, comparativos y territoriales confiables.

    #### 🔍 Cómo navegar el dashboard:

    1. Utiliza el menú lateral para acceder a cada sección.
    2. En **Inicio**, encontrarás KPIs globales y el mapa interactivo.
    3. En **Gráficas**, podrás explorar análisis visuales detallados por variable.
    4. Ajusta los filtros de periodo para estudiar cómo cambian los residuos con el tiempo.

    #### 🛠️ Tecnologías utilizadas:

    - **Python**: Lenguaje principal del proyecto.
    - **Streamlit**: Desarrollo del entorno visual e interactivo.
    - **Pandas**: Manejo, limpieza y procesamiento de datos.
    - **Plotly**: Gráficos interactivos en alta calidad.
    - **Folium**: Creación de mapas temáticos y geográficos.
    """)

def mostrar_estadisticas_dataset(df_local):
    st.markdown("### 📈 Estadísticas del Dataset")
    st.metric("Total de registros", f"{len(df_local):,}")
    st.metric("Departamentos analizados", df_local["DEPARTAMENTO"].nunique())
    st.metric("Periodos disponibles", df_local["PERIODO"].nunique())
    periodo_min = int(df_local["PERIODO"].min())
    periodo_max = int(df_local["PERIODO"].max())
    st.metric("Rango de años", f"{periodo_min} — {periodo_max}")

def mostrar_info_desarrolladores():
    st.markdown("### 👥 Equipo de Desarrollo")
    st.info("""
    **Desarrolladores:**
    - Wilmer Herrera Neira  
    - Abigail Lopez Cueva
    """)

def mostrar_metodologia():
    with st.expander("📚 Metodología del Análisis"):
        st.markdown("""
        #### Proceso de análisis:

        1. **Recopilación de datos**  
           Obtención de registros oficiales relacionados con la gestión de residuos.

        2. **Limpieza y preparación**  
           Normalización de nombres, validación de valores y organización del dataset.

        3. **Análisis exploratorio (EDA)**  
           Identificación de patrones, valores extremos, tendencias y distribución territorial.

        4. **Visualización**  
           Creación de gráficos, mapas temáticos y dashboards interactivos para facilitar
           la interpretación de información.

        #### Indicadores implementados:

        - Total de residuos generados por periodo.
        - Departamento con mayor producción de residuos.
        - Tipo de residuo predominante.
        - Población total representada en los registros.
        """)

def mostrar_glosario():
    with st.expander("📖 Glosario de Términos"):
        st.markdown("""
        - **Residuos domiciliarios**: Residuos generados en hogares y viviendas.
        - **Tonelada (T)**: Unidad de peso equivalente a 1000 kg.
        - **Periodo**: Año del registro de generación de residuos.
        - **Departamento**: División geográfica principal del Perú.
        - **GPC (Generación Per Cápita)**: Cantidad de residuos generados por habitante por día.
        """)

def mostrar_informacion(df_local):
    col1, col2 = st.columns([2, 1])
    with col1:
        mostrar_descripcion_proyecto()
    with col2:
        mostrar_estadisticas_dataset(df_local)
        st.markdown("---")
        mostrar_info_desarrolladores()

def mostrar_informacion_completa(df_local):
    mostrar_informacion(df_local)
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        mostrar_metodologia()
    with col2:
        mostrar_glosario()

# ---------------------------------------------------------------------
# Map loader 
# ---------------------------------------------------------------------
def generar_mapa(df_local, periodo, geojson_path=GEOJSON_PATH):
    """
    Genera un mapa folium a partir del dataframe ya cargado y el geojson.
    """
    # normalizar nombres y columnas (por si)
    df_copy = df_local.copy()
    df_copy.columns = df_copy.columns.str.strip().str.upper()
    if "DEPARTAMENTO" in df_copy.columns:
        df_copy["DEPARTAMENTO"] = df_copy["DEPARTAMENTO"].astype(str).str.upper().str.strip()
    columnas_residuos = [c for c in df_copy.columns if c.startswith("QRESIDUOS_") and c != "QRESIDUOS_DOM"]

    # Agrupar por departamento y periodo
    df_grouped = df_copy.groupby(["DEPARTAMENTO", "PERIODO"], as_index=False)[["QRESIDUOS_DOM"] + columnas_residuos].sum()

    # Filtrar por periodo
    df_periodo = df_grouped[df_grouped["PERIODO"] == periodo].copy()

    total_residuos_dict = df_periodo.set_index("DEPARTAMENTO")["QRESIDUOS_DOM"].to_dict()

    residuo_top_dict = {}
    for _, row in df_periodo.iterrows():
        depa = row["DEPARTAMENTO"]
        sub = row[columnas_residuos]
        if sub.sum() == 0 or sub.isna().all():
            residuo_top_dict[depa] = ("Sin datos", 0.0)
        else:
            top_col = sub.idxmax()
            top_val = sub.max()
            nombre_legible = top_col.replace("QRESIDUOS_", "").replace("_", " ").title()
            residuo_top_dict[depa] = (nombre_legible, float(top_val))

    # Cargar GeoJSON
    try:
        with open(geojson_path, "r", encoding="utf-8") as f:
            geojson_data = json.load(f)
    except FileNotFoundError:
        st.error(f"No se encontró el archivo GeoJSON en: {geojson_path}")
        return folium.Map(location=[-9.19, -75.015], zoom_start=5)

    # Inyectar propiedades
    for feature in geojson_data.get("features", []):
        props = feature.get("properties", {})
        nombre = props.get("NOMBDEP") or props.get("NAME") or props.get("dpto") or ""
        nombre_norm = str(nombre).upper().strip()

        total = total_residuos_dict.get(nombre_norm, 0.0)
        top_name, top_val = residuo_top_dict.get(nombre_norm, ("Sin datos", 0.0))
        total_fmt = f"{total:,.2f}"
        top_val_fmt = f"{top_val:,.2f}"

        props["total_residuos"] = total_fmt
        props["residuo_top"] = f"{top_name} ({top_val_fmt} t)"
        feature["properties"] = props

    # Crear mapa
    m = folium.Map(location=[-9.19, -75.015], zoom_start=5)

    folium.Choropleth(
        geo_data=geojson_data,
        data=df_periodo,
        columns=["DEPARTAMENTO", "QRESIDUOS_DOM"],
        key_on="feature.properties.NOMBDEP",
        fill_color="YlOrRd",
        fill_opacity=0.8,
        line_opacity=0.3,
        nan_fill_color="white",
        legend_name=f"Residuos domiciliarios (toneladas) - {periodo}"
    ).add_to(m)

    tooltip = folium.GeoJsonTooltip(
        fields=["NOMBDEP", "total_residuos", "residuo_top"],
        aliases=["Departamento:", "Total residuos (t):", "Residuo más abundante:"],
        localize=True,
        labels=True,
        sticky=True,
        style=("background-color: white; "
               "border: 1px solid gray; "
               "border-radius: 3px; "
               "box-shadow: 3px 3px 6px rgba(0,0,0,0.2);")
    )

    folium.GeoJson(
        geojson_data,
        name="Departamentos",
        style_function=lambda feature: {"fillColor": "transparent", "color": "black", "weight": 0.8},
        tooltip=tooltip,
        highlight_function=lambda x: {"weight": 3, "color": "blue"}
    ).add_to(m)

    return m

# ---------------------------------------------------------------------
# APP - Navegación y ensamblado final
# ---------------------------------------------------------------------
# Sidebar
if os.path.exists("upch_logo.png"):
    st.sidebar.image("upch_logo.png", use_container_width=True)

st.sidebar.title("Menú de Navegación")
st.sidebar.markdown("---")


pagina = st.sidebar.radio("Selecciona una sección:", ["🏠 Inicio", "📈 Gráficas", "ℹ️ Información"], index=0)

st.sidebar.markdown("---")
st.sidebar.markdown("### Acerca del proyecto")
st.sidebar.info(
    "Dashboard interactivo para el análisis de residuos sólidos domiciliarios "
    "en el Perú. Incluye métricas, gráficos comparativos y un mapa dinámico "
    "para facilitar la exploración de los datos."
)

# Rutas y comprobaciones básicas
if df.empty:
    st.error("El dataset está vacío o no pudo cargarse. Revisa Data/dataset.csv")
else:
    if pagina == "🏠 Inicio":
        st.title("📊 SISTEMA DE ANÁLISIS DE RESIDUOS SÓLIDOS DOMICILIARIOS")
        st.markdown("---")

        # KPIs
        mostrar_kpis(df)
        st.markdown("---")

        # Mapa
        st.subheader("🗺️ Mapa de Residuos por Departamento")
        periodos = sorted(df["PERIODO"].unique())
        periodo_seleccionado = st.selectbox("Selecciona el periodo (año):", periodos, index=len(periodos)-1 if periodos else 0)
        with st.spinner("Cargando mapa..."):
            mapa = generar_mapa(df, periodo_seleccionado, geojson_path=GEOJSON_PATH)
            # Mostrar mapa 
            try:
                st.components.v1.html(mapa._repr_html_(), height=650)
            except Exception:
                # Fallback: mostrar enlace o mensaje
                st.warning("No se pudo renderizar el mapa dentro del contenedor. Asegúrate de tener folium y streamlit actualizados.")
                st.write("Mapa generado (intenta abrir en un navegador compatible).")

    elif pagina == "📈 Gráficas":
        st.title("📈 Análisis Gráfico de Residuos")
        st.markdown("---")
        mostrar_graficas(df)

    elif pagina == "ℹ️ Información":
        st.title("ℹ️ Información del Proyecto")
        st.markdown("---")
        mostrar_informacion_completa(df)
