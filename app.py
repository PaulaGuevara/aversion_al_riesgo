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

# Cargar archivos generados por el BLOQUE FINAL del usuario
df_crra  = load_csv("resultados_CRRA.csv")
df_ftp   = load_csv("resultados_FTP.csv")
df_garch = load_csv("resultados_GARCH.csv")
df_full  = load_csv("resultados_completos_tablero.csv")

# Otros archivos opcionales
df_tests        = load_csv("garch_supuestos.csv")
df_timeseries   = load_csv("garch_timeseries.csv")
df_hist_vs_dyn  = load_csv("vol_hist_vs_garch.csv")


# Limpiar nombres
def clean_name(x):
    if isinstance(x, str):
        return x.replace("Datos históricos de ", "").split("(")[0].strip()
    return x

for df in [df_crra, df_ftp, df_garch, df_full, df_tests, df_timeseries, df_hist_vs_dyn]:
    if df is not None and "Activo" in df.columns:
        df["Activo"] = df["Activo"].apply(clean_name)

# Activos a excluir del análisis de riesgo
excluir_macro = ["TRM", "TPM", "IBR", "DTB3"]

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
    Este tablero presenta un análisis del coeficiente de aversión al riesgo γ en el mercado colombiano,
    siguiendo la metodología planteada por Chávez, Milanesi y Pesce (2021).

    Se estiman tres medidas del coeficiente γ:

    **CRRA — Constant Relative Risk Aversion**  
    Modelo clásico donde γ controla la concavidad de la función de utilidad.

    **FTP — Flexible Three-Parameter Utility**  
    Función de utilidad más general que incorpora parámetros adicionales para capturar preferencias
    no lineales frente al riesgo.

    **GARCH(1,1)**  
    Se usa volatilidad condicional σₜ estimada mediante un proceso GARCH con distribución t-student
    en lugar de volatilidad histórica.

    Los resultados permiten evaluar el nivel de aversión al riesgo implícito en los precios de las acciones colombianas.
    """)

    st.info("Usa el menú lateral para explorar las demás secciones del tablero.")

# ============================================================
# 2. AVERSIÓN AL RIESGO
# ============================================================

elif page == "Aversión al riesgo (CRRA / FTP / GARCH)":

    st.title("Coeficientes de Aversión al Riesgo por Activo")

    if df_full is None:
        st.error("No se encontró resultados_completos_tablero.csv")
        st.stop()

    df = df_full.copy()
    df = df[~df["Activo"].isin(excluir_macro)]

    st.subheader("Tabla Completa")
    st.dataframe(df.round(4), use_container_width=True)

    df_long = df.melt(
        id_vars="Activo",
        value_vars=["gamma_CRRA", "gamma_FTP", "gamma_GARCH"],
        var_name="Método",
        value_name="Gamma"
    )

    st.subheader("Gamma por Método")
    fig = px.bar(
        df_long,
        x="Activo",
        y="Gamma",
        color="Método",
        barmode="group",
        template=plotly_template,
        title="Comparación de γ por activo",
        height=600
    )
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# 3. VOLATILIDAD DINÁMICA σₜ
# ============================================================

elif page == "Volatilidad dinámica (σₜ)":

    st.title("Volatilidad Dinámica Estimada con GARCH(1,1)")

    if df_timeseries is None:
        st.error("No se encontró garch_timeseries.csv")
        st.stop()

    df = df_timeseries.copy()
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    activos = df["Activo"].unique()

    activos_sel = st.multiselect("Selecciona acciones:", activos, default=list(activos))

    df_plot = df[df["Activo"].isin(activos_sel)]

    fig = px.line(
        df_plot,
        x="Fecha",
        y="sigma_t",
        color="Activo",
        template=plotly_template,
        title="Volatilidad dinámica (σₜ)"
    )
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# 4. VOLATILIDAD HISTÓRICA VS DINÁMICA
# ============================================================

elif page == "Volatilidad histórica vs dinámica":

    st.title("Volatilidad Histórica vs Volatilidad Dinámica (GARCH)")

    if df_hist_vs_dyn is None:
        st.error("No se encontró vol_hist_vs_garch.csv")
        st.stop()

    df_hist_vs_dyn["Fecha"] = pd.to_datetime(df_hist_vs_dyn["Fecha"])

    activos = df_hist_vs_dyn["Activo"].unique()
    activo_sel = st.selectbox("Selecciona una acción:", activos)

    df_sel = df_hist_vs_dyn[df_hist_vs_dyn["Activo"] == activo_sel]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_sel["Fecha"], y=df_sel["vol_hist"],
        mode="lines", name="Volatilidad Histórica"
    ))
    fig.add_trace(go.Scatter(
        x=df_sel["Fecha"], y=df_sel["sigma_t"],
        mode="lines", name="Volatilidad GARCH (σₜ)"
    ))
    fig.update_layout(
        template=plotly_template,
        title=f"Volatilidad Histórica vs GARCH – {activo_sel}",
        height=600
    )
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# 5. DIAGNÓSTICOS GARCH
# ============================================================

elif page == "Diagnósticos GARCH":

    st.title("Pruebas de Diagnóstico GARCH")

    if df_tests is None:
        st.error("No se encontró garch_supuestos.csv")
        st.stop()

    df = df_tests.copy()
    df = df.round(4)

    st.subheader("Tabla de Resultados")
    st.dataframe(df, use_container_width=True)

    st.markdown("""
    **Interpretación sugerida:**

    - **ADF (p < 0.05)** → la serie de retornos es estacionaria.  
    - **ARCH-LM (p < 0.05)** → hay heterocedasticidad → aplicar GARCH es apropiado.  
    - **Ljung-Box residuos (p > 0.05)** → no hay autocorrelación en residuos.  
    - **Ljung-Box residuos² (p > 0.05)** → no hay autocorrelación en la varianza.  
    - **Jarque-Bera (p < 0.05)** → residuos no normales (común en finanzas).  
    - **alpha + beta < 1** → el proceso GARCH es estacionario.  
    """)

