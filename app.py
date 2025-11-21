import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="Aversión al Riesgo en el Mercado Colombiano",
    layout="wide"
)

plotly_template = "plotly_white"

# ============================================================
# FUNCIÓN PARA CARGAR DATOS
# ============================================================

def load_csv(path):
    full_path = os.path.join("data", path)
    if os.path.exists(full_path):
        df = pd.read_csv(full_path)
        return df
    st.warning(f"No se encontró {path}.")
    return None


# Carga de datos
df_crra = load_csv("gamma_crra.csv")
df_ftp = load_csv("gamma_ftp.csv")
df_garch = load_csv("gamma_garch.csv")
df_tests = load_csv("garch_supuestos.csv")
df_timeseries = load_csv("garch_timeseries.csv")
df_hist_vs_dyn = load_csv("vol_hist_vs_garch.csv")

# Limpiar nombres
def clean_name(x):
    if isinstance(x, str):
        return x.replace("Datos históricos de ", "").split("(")[0].strip()
    return x

for df in [df_crra, df_ftp, df_garch, df_tests, df_timeseries, df_hist_vs_dyn]:
    if df is not None and "Activo" in df.columns:
        df["Activo"] = df["Activo"].apply(clean_name)

# Activos a excluir del análisis de riesgo
excluir = ["TRM", "TPM", "IBR", "DTB3"]

# ============================================================
# MENÚ LATERAL
# ============================================================

page = st.sidebar.radio(
    "Navegación",
    [
        "Contexto",
        "Aversión al riesgo (CRRA / FTP / GARCH)",
        "Volatilidad dinámica (σₜ)",
        "Volatilidad histórica vs dinámica",
        "Diagnósticos GARCH"
    ]
)

# ============================================================
# 1. CONTEXTO
# ============================================================

if page == "Contexto":

    st.title("Aversión al Riesgo en el Mercado Colombiano — 2020–2025")

    st.markdown("""
    Este tablero presenta los resultados de un estudio sobre aversión al riesgo implícita en el mercado colombiano,
    siguiendo la metodología de **Chávez, Milanesi & Pesce (2021)**.

    El objetivo es estimar el coeficiente de aversión al riesgo γ utilizando tres metodologías:

    **1. CRRA — Constant Relative Risk Aversion**  
    Modelo clásico donde la utilidad depende del retorno y γ mide la concavidad de la función.

    **2. FTP — Flexible Three-Parameter Utility**  
    Modelo más flexible que introduce dos parámetros adicionales para capturar comportamientos no lineales.

    **3. GARCH(1,1) — Volatilidad Condicional**  
    En lugar de usar volatilidad histórica, se utiliza la volatilidad dinámica σₜ generada por un proceso GARCH(1,1)
    con distribución t-student.

    Estos modelos permiten evaluar si los inversionistas presentan aversión leve, moderada o elevada al riesgo.
    """)

    st.info("Seleccione otra sección usando el menú lateral.")

# ============================================================
# 2. AVERSIÓN AL RIESGO (CRRA / FTP / GARCH)
# ============================================================

elif page == "Aversión al riesgo (CRRA / FTP / GARCH)":

    st.title("Coeficientes de Aversión al Riesgo por Activo")

    if df_crra is None or df_ftp is None or df_garch is None:
        st.error("Faltan archivos CSV de gamma.")
        st.stop()

    # Merge de datos
    df = df_crra.merge(df_ftp, on="Activo", how="outer")
    df = df.merge(df_garch, on="Activo", how="outer")

    df = df[~df["Activo"].isin(excluir)]

    st.subheader("Tabla General")
    st.dataframe(df.round(4), use_container_width=True)

    # Gráfico de barras
    df_long = df.melt(id_vars="Activo",
                      value_vars=["gamma_CRRA", "gamma_FTP", "gamma_GARCH"],
                      var_name="Método", value_name="Gamma")

    st.subheader("Gamma por método")
    fig = px.bar(df_long,
                 x="Activo",
                 y="Gamma",
                 color="Método",
                 barmode="group",
                 template=plotly_template,
                 title="Comparación de γ por activo",
                 height=600)
    st.plotly_chart(fig, use_container_width=True)


# ============================================================
# 3. VOLATILIDAD DINÁMICA (σₜ)
# ============================================================

elif page == "Volatilidad dinámica (σₜ)":

    st.title("Volatilidad Dinámica Estimada mediante GARCH(1,1)")

    if df_timeseries is None:
        st.error("No se encontró garch_timeseries.csv.")
        st.stop()

    df_timeseries["Fecha"] = pd.to_datetime(df_timeseries["Fecha"])
    activos = df_timeseries["Activo"].unique()

    st.sidebar.subheader("Filtro de activos")
    activos_sel = st.sidebar.multiselect("Selecciona acciones:", activos, default=list(activos))

    df_plot = df_timeseries[df_timeseries["Activo"].isin(activos_sel)]

    fig = px.line(df_plot,
                  x="Fecha",
                  y="sigma_t",
                  color="Activo",
                  template=plotly_template,
                  title="Volatilidad dinámica (σₜ)")
    st.plotly_chart(fig, use_container_width=True)


# ============================================================
# 4. VOLATILIDAD HISTÓRICA VS DINÁMICA
# ============================================================

elif page == "Volatilidad histórica vs dinámica":

    st.title("Volatilidad Histórica vs Volatilidad Dinámica (GARCH)")

    if df_hist_vs_dyn is None:
        st.error("No se encontró vol_hist_vs_garch.csv.")
        st.stop()

    df_hist_vs_dyn["Fecha"] = pd.to_datetime(df_hist_vs_dyn["Fecha"])
    activos = df_hist_vs_dyn["Activo"].unique()

    activo_sel = st.selectbox("Selecciona una acción:", activos)

    df_sel = df_hist_vs_dyn[df_hist_vs_dyn["Activo"] == activo_sel]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_sel["Fecha"], y=df_sel["vol_hist"],
        mode="lines", name="Volatilidad histórica"
    ))
    fig.add_trace(go.Scatter(
        x=df_sel["Fecha"], y=df_sel["sigma_t"],
        mode="lines", name="Volatilidad GARCH (σₜ)"
    ))
    fig.update_layout(template=plotly_template,
                      title=f"Histórica vs Dinámica – {activo_sel}",
                      height=600)
    st.plotly_chart(fig, use_container_width=True)


# ============================================================
# 5. DIAGNÓSTICOS GARCH
# ============================================================

elif page == "Diagnósticos GARCH":

    st.title("Pruebas de Diagnóstico — Modelos GARCH(1,1)")

    if df_tests is None:
        st.error("No se encontró garch_supuestos.csv.")
        st.stop()

    st.subheader("Resultados de las pruebas (redondeados)")

    st.dataframe(df_tests.round(4), use_container_width=True)

    st.markdown("""
    **Interpretación:**  
    - **ADF p < 0.05** → retornos estacionarios  
    - **ARCH-LM p < 0.05** → heterocedasticidad → GARCH es apropiado  
    - **Ljung-Box p > 0.05** → residuos no autocorrelacionados  
    - **Jarque-Bera p < 0.05** → residuos no normales (común en mercados)  
    - **alpha + beta < 1** → el proceso GARCH es estacionario  
    """)

