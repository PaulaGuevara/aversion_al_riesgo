import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# ============================================================
# CONFIGURACIÓN GENERAL DEL TABLERO
# ============================================================

st.set_page_config(
    page_title="Aversión al Riesgo – Colombia",
    layout="wide"
)

# Paleta azul profesional
color_palette = ["#004A98", "#1B76D1", "#6BA5FF", "#AFCBFF"]

plotly_template = "plotly_white"

# ============================================================
# FUNCIÓN PARA CARGAR DATOS
# ============================================================

def load_csv(path):
    full = os.path.join("data", path)
    if os.path.exists(full):
        return pd.read_csv(full)
    st.warning(f"No se encontró el archivo {path}")
    return None

# Archivos principales
df_crra  = load_csv("resultados_CRRA.csv")
df_ftp   = load_csv("resultados_FTP.csv")
df_garch = load_csv("resultados_GARCH.csv")
df_full  = load_csv("resultados_completos_tablero.csv")

# Otros archivos opcionales
df_tests        = load_csv("garch_supuestos.csv")
df_timeseries   = load_csv("garch_timeseries.csv")
df_hist_vs_dyn  = load_csv("vol_hist_vs_garch.csv")

# ============================================================
# LIMPIEZA DE NOMBRES
# ============================================================

def clean_name(x):
    if isinstance(x, str):
        return x.replace("Datos históricos de ", "").split("(")[0].strip()
    return x

for df in [df_crra, df_ftp, df_garch, df_full, df_tests, df_timeseries, df_hist_vs_dyn]:
    if df is not None and "Activo" in df.columns:
        df["Activo"] = df["Activo"].apply(clean_name)

# Eliminar TRM de todos los análisis
excluir_macro = ["TRM", "TPM", "IBR", "DTB3"]

# ============================================================
# MENÚ
# ============================================================

page = st.sidebar.radio(
    "Navegación",
    [
        "Contexto",
        "Aversión al riesgo",
        "Volatilidad dinámica (σₜ)",
        "Volatilidad histórica vs dinámica",
        "Diagnósticos GARCH"
    ]
)

# ============================================================
# LOGO
# ============================================================

st.markdown("""
    <div style="position:absolute; top:15px; right:25px;">
        <img src="https://usantotomas.edu.co/hs-fs/hubfs/social-suggested-images/usantotomas.edu.cohs-fshubfsLogo%20Santoto%20-%20SP%20Bogota%20Horizontal%20blanco-2.png"
        width="200">
    </div>
""", unsafe_allow_html=True)

# ============================================================
# 1. CONTEXTO
# ============================================================

if page == "Contexto":

    st.title("Aversión al Riesgo en el Mercado Colombiano (2020–2025)")
    st.subheader("Autoras: Paula Ximena Guevara G – Natalia Zárate Yara")

    st.markdown("""
    Este tablero presenta los resultados del análisis de **aversión al riesgo implícita** en el mercado colombiano,
    replicando la metodología de **Chávez, Milanesi y Pesce (2021)**.

    Se estiman coeficientes γ usando:
    
    **CRRA – Constant Relative Risk Aversion**  
    Mide la concavidad de la utilidad bajo riesgo.

    **FTP – Flexible Three-Parameter Utility**  
    Modelo más flexible que captura preferencias no lineales.

    **GARCH(1,1)**  
    Usa la volatilidad condicional σₜ en lugar de volatilidad histórica.
    """)

    # ============================
    # KPIs
    # ============================

    c1, c2, c3 = st.columns(3)

    if df_full is not None:
        df_filtered = df_full[~df_full["Activo"].isin(excluir_macro)]

        gamma_crra_mean  = df_filtered["gamma_CRRA"].mean()
        gamma_ftp_mean   = df_filtered["gamma_FTP"].mean()
        gamma_garch_mean = df_filtered["gamma_GARCH"].mean()

        c1.metric("Gamma CRRA promedio", f"{gamma_crra_mean:.3f}")
        c2.metric("Gamma FTP promedio", f"{gamma_ftp_mean:.3f}")
        c3.metric("Gamma GARCH promedio", f"{gamma_garch_mean:.3f}")

    # ============================
    # Gráfico inicial
    # ============================

    st.subheader("Comparación general de γ por método")

    df_long = df_filtered.melt(
        id_vars="Activo",
        value_vars=["gamma_CRRA", "gamma_FTP", "gamma_GARCH"],
        var_name="Método",
        value_name="Gamma"
    )

    fig = px.bar(
        df_long,
        x="Activo",
        y="Gamma",
        color="Método",
        color_discrete_sequence=color_palette,
        barmode="group",
        template=plotly_template,
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# 2. AVERSIÓN AL RIESGO COMPLETA
# ============================================================

elif page == "Aversión al riesgo":

    st.title("Aversión al Riesgo – CRRA, FTP y GARCH")

    if df_full is None:
        st.error("No se encontró resultados_completos_tablero.csv")
        st.stop()

    df = df_full[~df_full["Activo"].isin(excluir_macro)].copy()

    st.subheader("Tabla de resultados")
    st.dataframe(df.round(4), use_container_width=True)
    st.caption("Tabla con los coeficientes γ estimados bajo las metodologías CRRA, FTP y GARCH.")

    df_long = df.melt(id_vars="Activo",
                      value_vars=["gamma_CRRA","gamma_FTP","gamma_GARCH"],
                      var_name="Método", value_name="Gamma")

    fig = px.bar(
        df_long,
        x="Activo",
        y="Gamma",
        color="Método",
        color_discrete_sequence=color_palette,
        template=plotly_template,
        barmode="group"
    )
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# 3. VOLATILIDAD DINÁMICA σₜ
# ============================================================

elif page == "Volatilidad dinámica (σₜ)":

    st.title("Volatilidad Dinámica – Modelo GARCH(1,1)")

    if df_timeseries is None:
        st.error("No se encontró garch_timeseries.csv")
        st.stop()

    df = df_timeseries.copy()
    df["Fecha"] = pd.to_datetime(df["Fecha"])

    df = df[~df["Activo"].isin(excluir_macro)]

    activos = df["Activo"].unique()

    activos_sel = st.multiselect("Seleccione acciones:", activos, default=list(activos))

    df_plot = df[df["Activo"].isin(activos_sel)]

    fig = px.line(
        df_plot,
        x="Fecha",
        y="sigma_t",
        color="Activo",
        template=plotly_template,
        color_discrete_sequence=color_palette,
    )
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# 4. VOLATILIDAD HISTÓRICA VS GARCH
# ============================================================

elif page == "Volatilidad histórica vs dinámica":

    st.title("Volatilidad Histórica vs Volatilidad GARCH")

    if df_hist_vs_dyn is None:
        st.error("Archivo vol_hist_vs_garch.csv no encontrado.")
        st.stop()

    df = df_hist_vs_dyn.copy()
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    df = df[~df["Activo"].isin(excluir_macro)]

    activos = df["Activo"].unique()
    activo_sel = st.selectbox("Seleccione una acción:", activos)

    df_sel = df[df["Activo"] == activo_sel]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_sel["Fecha"], y=df_sel["vol_hist"],
        mode="lines", name="Volatilidad Histórica",
        line=dict(color=color_palette[0])
    ))
    fig.add_trace(go.Scatter(
        x=df_sel["Fecha"], y=df_sel["sigma_t"],
        mode="lines", name="Volatilidad GARCH",
        line=dict(color=color_palette[1])
    ))
    fig.update_layout(
        template=plotly_template,
        height=600
    )
    st.plotly_chart(fig, use_container_width=True)

    st.caption("Comparación entre la volatilidad histórica y la volatilidad condicional estimada por GARCH.")

# ============================================================
# 5. DIAGNÓSTICOS GARCH
# ============================================================

elif page == "Diagnósticos GARCH":

    st.title("Diagnósticos del Modelo GARCH(1,1)")

    if df_tests is None:
        st.error("No se encontró garch_supuestos.csv")
        st.stop()

    df = df_tests.copy()
    df = df.round(4)

    st.subheader("Resultados de pruebas")
    st.dataframe(df, use_container_width=True)
    st.caption("Resultados de pruebas ADF, ARCH-LM, Ljung-Box y Jarque-Bera para validar los supuestos del modelo GARCH.")

