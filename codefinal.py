import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import altair as alt

df = pd.read_csv("dataser.csv", sep=";")

st.sidebar.title("Menú de Gráficas")

opcion = st.sidebar.radio(
    "Selecciona una visualización:",
    [
        "1. Total de residuos por departamento",
        "2. Top 5 distritos más contaminados",
        "3. Evolución de residuos por distrito",
        "4. Distritos más limpios (per cápita)"
    ]
)

if opcion == "1. Total de residuos por departamento":

    st.title("CANTIDAD TOTAL DE RESIDUOS POR DEPARTAMENTO")

    res_cols = [c for c in df.columns if "RESIDUO" in c.upper() or "ENVOLT" in c.upper()]
    años = sorted(df["PERIODO"].unique())

    año_sel = st.selectbox("Selecciona el año (PERIODO)", años)
    res_sel = st.selectbox("Selecciona el tipo de residuo", res_cols)

    df_fil = df[df["PERIODO"] == año_sel]

    df_dep = df_fil.groupby("DEPARTAMENTO")[res_sel].sum().reset_index()
    df_dep = df_dep.sort_values("DEPARTAMENTO")

    ocultar_lima = st.checkbox("Ocultar departamento de Lima")

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

elif opcion == "2. Top 5 distritos más contaminados":

    st.title("Top 5 Distritos con más residuo por departamento")

    res_cols = [c for c in df.columns if "RESIDUO" in c.upper() or "ENVOLT" in c.upper()]
    anios = sorted(df["PERIODO"].unique())
    departamentos = sorted(df["DEPARTAMENTO"].unique())

    anio_sel = st.selectbox("Selecciona el año (PERIODO)", anios)
    res_sel = st.selectbox("Selecciona el tipo de residuo", res_cols)
    dep_sel = st.selectbox("Selecciona el departamento", departamentos)

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

elif opcion == "3. Evolución de residuos por distrito":

    st.title("Evolución de residuos por distrito")

    res_cols = [c for c in df.columns if "RESIDUO" in c.upper() or "ENVOLT" in c.upper()]

    departamentos = sorted(df["DEPARTAMENTO"].unique())
    dep_sel = st.selectbox("Selecciona el departamento", departamentos)

    prov_df = df[df["DEPARTAMENTO"] == dep_sel]
    provincias = sorted(prov_df["PROVINCIA"].unique())
    prov_sel = st.selectbox("Selecciona la provincia", provincias)

    dist_df = prov_df[prov_df["PROVINCIA"] == prov_sel]
    distritos = sorted(dist_df["DISTRITO"].unique())
    dist_sel = st.selectbox("Selecciona el distrito", distritos)

    res_sel = st.selectbox("Selecciona el tipo de residuo", res_cols)

    df_fil = df[
        (df["DEPARTAMENTO"] == dep_sel) &
        (df["PROVINCIA"] == prov_sel) &
        (df["DISTRITO"] == dist_sel)
    ].sort_values("PERIODO")

    chart_data = df_fil.set_index("PERIODO")[[res_sel]]

    st.line_chart(chart_data)

elif opcion == "4. Distritos más limpios (per cápita)":

    st.title("DISTRITOS MÁS LIMPIOS (MENOR RESIDUO PER CÁPITA)")

    res_cols = [c for c in df.columns if "RESIDUO" in c.upper() or "ENVOLT" in c.upper()]
    departamentos = sorted(df["DEPARTAMENTO"].unique())
    anios = sorted(df["PERIODO"].unique())

    dep_sel = st.selectbox("Selecciona el departamento", departamentos)
    res_sel = st.selectbox("Selecciona el tipo de residuo", res_cols)
    anio_sel = st.selectbox("Selecciona el año (PERIODO)", anios)

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
