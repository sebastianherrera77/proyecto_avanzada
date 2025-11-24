import streamlit as st
import pandas as pd
import altair as alt

df = pd.read_csv("dataser.csv", sep=";")
st.title("**CANTIDAD TOTAL DE RESIDUOS POR DEPARTAMENTO**")
res_cols = [c for c in df.columns if "RESIDUO" in c.upper() or "ENVOLT" in c.upper()]
años = sorted(df["PERIODO"].unique())

año_sel = st.selectbox("Selecciona el año (PERIODO)", años)
res_sel = st.selectbox("Selecciona el tipo de residuo", res_cols)

df_fil = df[df["PERIODO"] == año_sel]

df_dep = df_fil.groupby("DEPARTAMENTO")[res_sel].sum().reset_index()
df_dep = df_dep.sort_values("DEPARTAMENTO")

st.dataframe(df_dep)

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

