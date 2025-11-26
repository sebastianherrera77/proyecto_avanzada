import streamlit as st
import pandas as pd
import altair as alt
import matplotlib.pyplot as plt

# ============================
# CARGA DE DATOS
# ============================
@st.cache_data
def load_data():
    return pd.read_csv("dataser.csv", sep=";")

df = load_data()

st.set_page_config(page_title="Dashboard de Residuos", layout="wide")

st.title("📊 Dashboard de Residuos en Perú")


# ============================
# GRAFICA 1: Total por Departamento
# ============================
def grafica1(df):
    st.subheader("1️⃣ Cantidad total de residuos por departamento")

    res_cols = [c for c in df.columns if "RESIDUO" in c.upper() or "ENVOLT" in c.upper()]
    años = sorted(df["PERIODO"].unique())

    año_sel = st.selectbox("Selecciona el año", años, key="g1_año")
    res_sel = st.selectbox("Selecciona el residuo", res_cols, key="g1_res")

    df_fil = df[df["PERIODO"] == año_sel]

    df_dep = df_fil.groupby("DEPARTAMENTO")[res_sel].sum().reset_index()
    df_dep = df_dep.sort_values("DEPARTAMENTO")

    ocultar_lima = st.checkbox("Ocultar Lima", key="g1_lima")
    if ocultar_lima:
        df_dep = df_dep[df_dep["DEPARTAMENTO"].str.upper() != "LIMA"]

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



# ============================
# GRAFICA 2: Top 5 Distritos (Pie Chart)
# ============================
def grafica2(df):
    st.subheader("2️⃣ 5 Distritos con más residuo (por departamento)")

    res_cols = [c for c in df.columns if "RESIDUO" in c.upper() or "ENVOLT" in c.upper()]

    anios = sorted(df["PERIODO"].unique())
    departamentos = sorted(df["DEPARTAMENTO"].unique())

    anio_sel = st.selectbox("Año", anios, key="g2_año")
    res_sel = st.selectbox("Residuo", res_cols, key="g2_res")
    dep_sel = st.selectbox("Departamento", departamentos, key="g2_dep")

    df_fil = df[(df["PERIODO"] == anio_sel) & (df["DEPARTAMENTO"] == dep_sel)]

    df_top5 = df_fil.groupby("DISTRITO")[res_sel].sum().reset_index()
    df_top5 = df_top5.sort_values(res_sel, ascending=False).head(5)

    fig, ax = plt.subplots()
    ax.pie(
        df_top5[res_sel],
        labels=df_top5["DISTRITO"],
        autopct="%1.1f%%",
        startangle=90
    )
    ax.axis("equal")

    st.pyplot(fig)



# ============================
# GRAFICA 3: Evolución temporal por distrito
# ============================
def grafica3(df):
    st.subheader("3️⃣ Evolución de residuos por distrito")

    res_cols = [c for c in df.columns if "RESIDUO" in c.upper() or "ENVOLT" in c.upper()]

    departamentos = sorted(df["DEPARTAMENTO"].unique())
    dep_sel = st.selectbox("Departamento", departamentos, key="g3_dep")

    prov_df = df[df["DEPARTAMENTO"] == dep_sel]
    provincias = sorted(prov_df["PROVINCIA"].unique())
    prov_sel = st.selectbox("Provincia", provincias, key="g3_prov")

    dist_df = prov_df[prov_df["PROVINCIA"] == prov_sel]
    distritos = sorted(dist_df["DISTRITO"].unique())
    dist_sel = st.selectbox("Distrito", distritos, key="g3_dist")

    res_sel = st.selectbox("Residuo", res_cols, key="g3_res")

    df_fil = df[
        (df["DEPARTAMENTO"] == dep_sel) &
        (df["PROVINCIA"] == prov_sel) &
        (df["DISTRITO"] == dist_sel)
    ].sort_values("PERIODO")

    chart_data = df_fil.set_index("PERIODO")[[res_sel]]

    st.line_chart(chart_data)



# ============================
# GRAFICA 4: Distritos más limpios
# ============================
def grafica4(df):
    st.subheader("4️⃣ Distritos más limpios (menor residuo per cápita)")

    res_cols = [c for c in df.columns if "RESIDUO" in c.upper() or "ENVOLT" in c.upper()]

    departamentos = sorted(df["DEPARTAMENTO"].unique())
    anios = sorted(df["PERIODO"].unique())

    dep_sel = st.selectbox("Departamento", departamentos, key="g4_dep")
    res_sel = st.selectbox("Residuo", res_cols, key="g4_res")
    anio_sel = st.selectbox("Año", anios, key="g4_año")

    df_fil = df[
        (df["DEPARTAMENTO"] == dep_sel) &
        (df["PERIODO"] == anio_sel)
    ].copy()

    df_fil["RESIDUO_PERCAPITA"] = df_fil[res_sel] / df_fil["POB_TOTAL"]

    df_top = df_fil[["DISTRITO", "RESIDUO_PERCAPITA"]].sort_values("RESIDUO_PERCAPITA").head(5)

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



# ============================
# MENÚ LATERAL
# ============================
st.sidebar.title("📌 Navegación")

opcion = st.sidebar.radio(
    "Selecciona una visualización:",
    ("Total por departamento", "Top 5 distritos", "Evolución temporal", "Distritos más limpios")
)

if opcion == "Total por departamento":
    grafica1(df)
elif opcion == "Top 5 distritos":
    grafica2(df)
elif opcion == "Evolución temporal":
    grafica3(df)
elif opcion == "Distritos más limpios":
    grafica4(df)
