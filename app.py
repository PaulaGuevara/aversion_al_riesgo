import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Aversión al Riesgo - Colombia",
    layout="wide"
)

# ==========================
#   CARGAR DATOS
# ==========================

@st.cache_data
def cargar_datos():
    df = pd.read_csv("data/resultados_completos_tablero.csv")
    df_crra = pd.read_csv("data/resultados_CRRA.csv")
    df_ftp  = pd.read_csv("data/resultados_FTP.csv")
    df_garch = pd.read_csv("data/resultados_GARCH.csv")
    return df, df_crra, df_ftp, df_garch

df, df_crra, df_ftp, df_garch = cargar_datos()

st.title("📊 Aversión al Riesgo en el Mercado Colombiano (2020–2025)")
st.markdown("Este tablero presenta los resultados del estudio de aversión al riesgo utilizando **CRRA**, **FTP** y **GARCH** replicando el enfoque de Chávez, Milanesi & Pesce (2021).")

# ==========================
#   KPIs
# ==========================

col1, col2, col3, col4 = st.columns(4)

col1.metric("γ CRRA Promedio", f"{df['gamma_CRRA'].mean():.3f}")
col2.metric("γ FTP Promedio", f"{df['gamma_FTP'].mean():.3f}")
col3.metric("γ GARCH Promedio", f"{df['gamma_GARCH'].mean():.3f}")
col4.metric("Activos Analizados", df.shape[0])

st.markdown("---")

# ==========================
#   GRÁFICO PRINCIPAL
# ==========================

st.subheader("Comparación de Aversión al Riesgo por Activo y Método")

fig = px.bar(
    df,
    x="Activo",
    y=["gamma_CRRA", "gamma_FTP", "gamma_GARCH"],
    barmode="group",
    title="γ por método (CRRA, FTP, GARCH)",
    labels={"value": "γ", "variable": "Método"},
    height=500
)

st.plotly_chart(fig, use_container_width=True)

# ==========================
#   TABLA COMPLETA
# ==========================

st.subheader("Tabla Completa de Resultados")
st.dataframe(df, use_container_width=True)

# ==========================
#   ANÁLISIS POR ACTIVO
# ==========================

st.markdown("---")
st.subheader("Análisis por Activo")

activo = st.selectbox("Selecciona un activo:", df["Activo"])

df_activo = df[df["Activo"] == activo]

colA, colB, colC = st.columns(3)
colA.metric("γ CRRA", f"{df_activo['gamma_CRRA'].values[0]:.4f}")
colB.metric("γ FTP", f"{df_activo['gamma_FTP'].values[0]:.4f}")
colC.metric("γ GARCH", f"{df_activo['gamma_GARCH'].values[0]:.4f}")

st.write("### Datos del activo seleccionado")
st.table(df_activo)
