# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io
import base64
from pathlib import Path

# Estadística
from scipy import stats
from statsmodels.tsa.stattools import adfuller
from statsmodels.stats.diagnostic import het_arch, acorr_ljungbox

# -----------------------------------------------------------
# Configuración visual
# -----------------------------------------------------------
st.set_page_config(
    page_title="Aversión al Riesgo – Colombia",
    layout="wide",
    initial_sidebar_state="expanded"
)

PRIMARY = "#2b8cbe"
ACCENT = "#f39c12"
BG = "#f7fbff"

# Small custom CSS for header coloring (optional)
st.markdown(
    f"""
    <style>
    .stApp {{
        background: {BG};
    }}
    .title {{
        color: {PRIMARY};
    }}
    .subtitle {{
        color: #0b3d91;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------
# UTIL: cargar CSV desde data/ y detectar columnas
# -----------------------------------------------------------
DATA_DIR = Path("data")

@st.cache_data
def try_load_csv(filename_list):
    """
    Intenta cargar el primer archivo existente de filename_list (relative to data/)
    Devuelve DataFrame o None
    """
    for fname in filename_list:
        p = DATA_DIR / fname
        if p.exists():
            try:
                df = pd.read_csv(p, low_memory=False)
                return df, fname
            except Exception:
                continue
    return None, None

# Archivos esperados (ajusta si tus nombres son distintos)
df_final, name_final = try_load_csv([
    "resultados_completos_tablero.csv",
    "tablero_final_completo.csv",
    "tablero_final.csv",
    "resultados_completos.csv"
])

df_crra, _ = try_load_csv(["resultados_CRRA.csv", "gamma_CRRA.csv"])
df_ftp, _  = try_load_csv(["resultados_FTP.csv", "gamma_FTP.csv"])
df_garch, _ = try_load_csv(["resultados_GARCH.csv", "gamma_GARCH.csv", "garch_results.csv"])
df_garch_tests, _ = try_load_csv(["garch_supuestos.csv", "garch_tests.csv"])
df_timeseries, name_ts = try_load_csv([
    "garch_timeseries.csv",
    "garch_series.csv",
    "sigma_timeseries.csv",
    "sigma_t.csv"
])
# Additionally check for a file with residuals/time series that might contain Fecha/Activo/sigma_t/retornos
df_sigma_long, _ = try_load_csv(["sigma_long.csv", "vol_series_long.csv"])

# PDF (paper) — developer instruction: include local path (will be transformed)
pdf_path = "/mnt/data/teoria (1).pdf"

# -----------------------------------------------------------
# Limpieza y normalización de columnas y nombres de activos
# -----------------------------------------------------------
def normalize_df_names(df):
    """
    Renombra columnas clave a los nombres usados en la app:
    - Activo
    - gamma_CRRA, gamma_FTP, gamma_GARCH
    - Vol_Hist, Vol_GARCH
    - Fecha, sigma_t, Retorno (para timeseries)
    """
    if df is None:
        return None

    cols = {c.lower().strip(): c for c in df.columns}

    def find_col(possible_keys):
        for k in possible_keys:
            if k.lower() in cols:
                return cols[k.lower()]
        return None

    mapping = {}
    # Activo
    c = find_col(["activo", "asset", "name"])
    if c: mapping[c] = "Activo"
    # gammas
    c = find_col(["gamma_crra", "gamma crra", "crra"])
    if c: mapping[c] = "gamma_CRRA"
    c = find_col(["gamma_ftp", "gamma ftp", "ftp"])
    if c: mapping[c] = "gamma_FTP"
    c = find_col(["gamma_garch", "gamma garch", "garch"])
    if c: mapping[c] = "gamma_GARCH"
    # vols
    c = find_col(["vol_hist", "volatilidad", "vol_hist"])
    if c: mapping[c] = "Vol_Hist"
    c = find_col(["vol_garch", "sigma_garch", "sigma_last", "vol_garch"])
    if c: mapping[c] = "Vol_GARCH"
    # Fecha / sigma_t / retorno (timeseries)
    c = find_col(["fecha", "date"])
    if c: mapping[c] = "Fecha"
    c = find_col(["sigma_t", "sigma", "volatilidad_condicional", "sigma_garch"])
    if c: mapping[c] = "sigma_t"
    c = find_col(["retorno", "rend", "rendimiento", "returns"])
    if c: mapping[c] = "Retorno"

    df = df.rename(columns=mapping)
    # Clean Activo names if present
    if "Activo" in df.columns:
        df["Activo"] = df["Activo"].astype(str).str.replace("Datos históricos de ", "", regex=False)
        df["Activo"] = df["Activo"].str.replace(r" \(.+\)", "", regex=True).str.strip()
    return df

df_final = normalize_df_names(df_final)
df_crra  = normalize_df_names(df_crra)
df_ftp   = normalize_df_names(df_ftp)
df_garch = normalize_df_names(df_garch)
df_garch_tests = normalize_df_names(df_garch_tests)
df_timeseries = normalize_df_names(df_timeseries)
df_sigma_long = normalize_df_names(df_sigma_long)

# If df_final is None, try to build from pieces
if df_final is None:
    pieces = []
    if df_crra is not None:
        pieces.append(df_crra)
    if df_ftp is not None:
        pieces.append(df_ftp)
    if df_garch is not None:
        pieces.append(df_garch)
    if pieces:
        # merge on Activo
        df_final = pieces[0]
        for p in pieces[1:]:
            if "Activo" in p.columns:
                df_final = df_final.merge(p, on="Activo", how="outer")
        df_final = normalize_df_names(df_final)

# Fallback empty
if df_final is None:
    df_final = pd.DataFrame(columns=[
        "Activo", "gamma_CRRA", "gamma_FTP", "gamma_GARCH",
        "Vol_Hist", "Vol_GARCH"
    ])

# Exclude macro series from risk visuals
EXCLUDE = {"TPM", "IBR", "DTB3"}

df_risk = df_final[~df_final["Activo"].isin(EXCLUDE)].copy()

# -----------------------------------------------------------
# UTIL: descargar DataFrame como CSV (botón)
# -----------------------------------------------------------
def get_table_download_link(df: pd.DataFrame, filename: str = "export.csv"):
    """Return a link to download the dataframe as CSV"""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Descargar {filename}</a>'
    return href

# -----------------------------------------------------------
# Sidebar: filtros y navegación
# -----------------------------------------------------------
st.sidebar.header("Filtros")
show_actions = st.sidebar.multiselect(
    "Seleccionar acciones (vacío = todas)", options=sorted(df_risk["Activo"].unique()), default=[]
)
if not show_actions:
    # default: all
    actions = sorted(df_risk["Activo"].unique())
else:
    actions = show_actions

st.sidebar.markdown("---")
st.sidebar.header("Navegación")
page = st.sidebar.radio("Ir a:", [
    "Resumen",
    "Aversión por acción",
    "Volatilidad dinámica",
    "Diagnósticos GARCH",
    "Heatmaps",
    "Descargas y recursos"
])

# -----------------------------------------------------------
# PAGE: RESUMEN
# -----------------------------------------------------------
if page == "Resumen":
    st.title("Aversión al Riesgo Implícita — Resumen")
    st.markdown("""
    **Contexto breve del artículo**: Chávez, Milanesi y Pesce (2021) estiman la aversión al riesgo implícita
    a partir de precios y volatilidades de activos financieros utilizando aproximaciones de utilidad (CRRA)
    y extensiones (FTP). El estudio demuestra que corregir por asimetría y curtosis modifica las estimaciones
    de aversión y que la volatilidad condicional (GARCH) es un insumo clave para capturar la incertidumbre dinámica.
    """)

    st.markdown("**Qué representa cada medida (breve):**")
    st.markdown("- **Gamma (γ):** coeficiente de aversión relativa al riesgo; mayor γ implica mayor rechazo a la variabilidad del rendimiento.")
    st.markdown("- **CRRA:** estimación clásica basada en media y varianza.")
    st.markdown("- **FTP:** ajuste que incorpora momentos superiores (skew, kurtosis).")
    st.markdown("- **GARCH:** modelo de volatilidad condicional; su σₜ alimenta las estimaciones dinámicas de γ.")

    st.markdown("---")
    # KPIs
    col1, col2, col3 = st.columns(3)
    col1.metric("Gamma (CRRA) promedio", f"{df_risk['gamma_CRRA'].dropna().mean():.3f}")
    col2.metric("Gamma (FTP) promedio", f"{df_risk['gamma_FTP'].dropna().mean():.3f}")
    col3.metric("Gamma (GARCH) promedio", f"{df_risk['gamma_GARCH'].dropna().mean():.3f}")

    # Bar chart: promedio por método (all selected actions)
    st.subheader("Gamma promedio por método (acciones seleccionadas)")
    tmp = pd.DataFrame({
        "Método": ["CRRA", "FTP", "GARCH"],
        "Gamma": [
            df_risk.loc[df_risk["Activo"].isin(actions), "gamma_CRRA"].mean(),
            df_risk.loc[df_risk["Activo"].isin(actions), "gamma_FTP"].mean(),
            df_risk.loc[df_risk["Activo"].isin(actions), "gamma_GARCH"].mean()
        ]
    })
    fig = px.bar(tmp, x="Método", y="Gamma", color="Método",
                 color_discrete_sequence=[PRIMARY, ACCENT, "#6a51a3"],
                 text_auto=".3f",
                 title="Gamma promedio por método")
    st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------
# PAGE: AVERSIÓN POR ACCIÓN
# -----------------------------------------------------------
elif page == "Aversión por acción":
    st.title("Aversión al Riesgo por Acción")
    st.markdown("Comparación de estimaciones de γ (CRRA, FTP y GARCH).")

    # Show all actions by default (filtered by sidebar)
    df_plot = df_risk[df_risk["Activo"].isin(actions)].copy()
    # Ensure numeric
    for c in ["gamma_CRRA", "gamma_FTP", "gamma_GARCH"]:
        if c in df_plot.columns:
            df_plot[c] = pd.to_numeric(df_plot[c], errors="coerce")

    # grouped bar by activo
    cols_present = [c for c in ["gamma_CRRA", "gamma_FTP", "gamma_GARCH"] if c in df_plot.columns]
    if not cols_present:
        st.warning("No se encontraron columnas de gamma en los CSV. Verifica los archivos en data/")
    else:
        fig = go.Figure()
        w = 0.2
        x = np.arange(len(df_plot))
        names = df_plot["Activo"].tolist()

        # Add a trace for each method present
        offsets = np.linspace(-w, w, len(cols_present))
        palette = {"gamma_CRRA": PRIMARY, "gamma_FTP": ACCENT, "gamma_GARCH": "#6a51a3"}
        for i, col in enumerate(cols_present):
            fig.add_trace(go.Bar(
                x=names,
                y=df_plot[col],
                name=col.replace("gamma_", "").upper(),
                marker_color=palette.get(col, None),
                offsetgroup=i
            ))

        fig.update_layout(barmode="group", xaxis_tickangle=-45, height=550,
                          title="Gamma por activo y método",
                          xaxis_title="Activo", yaxis_title="Gamma")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Tabla resumida (descargable)")
    display_cols = ["Activo"] + cols_present + [c for c in ["Vol_Hist", "Vol_GARCH"] if c in df_plot.columns]
    st.dataframe(df_plot[display_cols].reset_index(drop=True), use_container_width=True)
    st.markdown(get_table_download_link(df_plot[display_cols], "gamma_por_activo.csv"), unsafe_allow_html=True)

# -----------------------------------------------------------
# PAGE: VOLATILIDAD DINÁMICA (series temporales σ_t)
# -----------------------------------------------------------
elif page == "Volatilidad dinámica":
    st.title("Volatilidad dinámica (GARCH σₜ) y series temporales")

    if df_timeseries is None and df_sigma_long is None:
        st.info("No se encontró un archivo de series temporales de σₜ en data/. "
                "Si quieres ver gráficos temporales, exporta un CSV con columnas: Fecha, Activo, sigma_t, Retorno.")
        st.stop()

    # Priorizar df_timeseries (wide or long)
    if df_timeseries is not None:
        # if timeseries is wide (columns per asset), attempt to melt
        if "Fecha" in df_timeseries.columns and "sigma_t" in df_timeseries.columns and "Activo" in df_timeseries.columns:
            long = df_timeseries.copy()
        else:
            # try to melt if one column is Fecha and the rest are assets
            if "Fecha" in df_timeseries.columns:
                long = df_timeseries.melt(id_vars="Fecha", var_name="Activo", value_name="sigma_t")
            else:
                st.error(f"Archivo {name_ts} no tiene columna Fecha clara. Ajusta el CSV.")
                st.stop()
    else:
        long = df_sigma_long.copy()

    # Clean and parse Fecha
    long["Fecha"] = pd.to_datetime(long["Fecha"])
    long["sigma_t"] = pd.to_numeric(long["sigma_t"], errors="coerce")
    long["Activo"] = long["Activo"].astype(str).str.replace("Datos históricos de ", "", regex=False).str.replace(r" \(.+\)","",regex=True).str.strip()

    # filter by actions (default all)
    long_plot = long[long["Activo"].isin(actions)]

    # selector de activo para series
    act_for_series = st.multiselect("Seleccionar acciones para series (vacío= todas):", options=sorted(long_plot["Activo"].unique()), default=sorted(long_plot["Activo"].unique()))
    if act_for_series:
        long_plot = long_plot[long_plot["Activo"].isin(act_for_series)]

    # Plot interactive time series
    fig = px.line(long_plot, x="Fecha", y="sigma_t", color="Activo",
                  labels={"sigma_t": "σₜ (Volatilidad condicional)", "Fecha": "Fecha"},
                  title="Volatilidad condicional σₜ por activo (serie temporal)")
    st.plotly_chart(fig, use_container_width=True)

    # Optional: gamma(t) if Gamma estimates per date exist (column Gamma)
    if "Gamma" in long_plot.columns or "gamma" in [c.lower() for c in long_plot.columns]:
        gcol = "Gamma" if "Gamma" in long_plot.columns else [c for c in long_plot.columns if c.lower()=="gamma"][0]
        fig2 = px.line(long_plot, x="Fecha", y=gcol, color="Activo", title="Gamma(t) estimado")
        st.plotly_chart(fig2, use_container_width=True)

# -----------------------------------------------------------
# PAGE: DIAGNÓSTICOS GARCH
# -----------------------------------------------------------
elif page == "Diagnósticos GARCH":
    st.title("Diagnósticos de Modelos GARCH")

    # If precomputed tests exist, show them
    if df_garch_tests is not None and "Activo" in df_garch_tests.columns:
        df_tests = df_garch_tests.copy()
        # normalize column names
        df_tests = normalize_df_names(df_tests)
        df_tests = df_tests[~df_tests["Activo"].isin(EXCLUDE)]
        st.subheader("Resultados de tests (archivo garch_supuestos.csv detectado)")
        st.dataframe(df_tests, use_container_width=True)
        st.markdown(get_table_download_link(df_tests, "garch_tests_export.csv"), unsafe_allow_html=True)
    else:
        st.info("No se encontró un archivo con tests (garch_supuestos.csv). Se pueden calcular bajo demanda si se dispone de residuales y series GARCH en el entorno original.")

    st.markdown("---")
    st.subheader("Pruebas rápidas por activo (calculadas a partir de datos cargados)")

    # Attempt quick tests using df_final if residuals/sigma not available
    if "gamma_GARCH" in df_final.columns and df_timeseries is not None:
        # compute simple correlation tests as placeholders
        st.write("Se muestran pruebas básicas (ADF sobre series de retornos no implementadas aquí).")
    else:
        st.write("No hay suficientes datos en los CSV cargados para calcular tests automáticamente desde esta app.")

# -----------------------------------------------------------
# PAGE: HEATMAPS
# -----------------------------------------------------------
elif page == "Heatmaps":
    st.title("Heatmaps y Correlaciones")

    # Heatmap: correlation between gammas and volatilities
    corr_cols = [c for c in ["gamma_CRRA", "gamma_FTP", "gamma_GARCH", "Vol_Hist", "Vol_GARCH"] if c in df_risk.columns]
    if len(corr_cols) >= 2:
        corr = df_risk[corr_cols].corr()
        fig = px.imshow(corr, text_auto=True, color_continuous_scale="Viridis", title="Matriz de correlaciones")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay suficientes columnas para construir el heatmap de correlaciones.")

    # Heatmap of volatility over time (if long series available)
    if df_timeseries is not None or df_sigma_long is not None:
        long_src = long if 'long' in locals() else df_sigma_long.copy()
        # Pivot: rows Fecha (by month), columns Activo, values mean sigma_t
        long_src["Fecha"] = pd.to_datetime(long_src["Fecha"])
        long_src["Mes"] = long_src["Fecha"].dt.to_period("M").dt.to_timestamp()
        pivot = long_src.pivot_table(index="Mes", columns="Activo", values="sigma_t", aggfunc="mean")
        fig2 = px.imshow(pivot.T.loc[sorted(pivot.T.index)], aspect="auto", color_continuous_scale="Viridis",
                         title="Heatmap: Volatilidad condicional (promedio mensual)")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Para heatmaps temporales se requiere un CSV con series σₜ por Fecha y Activo.")

# -----------------------------------------------------------
# PAGE: DESCARGAS Y RECURSOS
# -----------------------------------------------------------
elif page == "Descargas y recursos":
    st.title("Descargas y recursos")

    st.subheader("Archivos disponibles en data/")
    for p in sorted(DATA_DIR.glob("*")):
        st.write(f"- {p.name}")

    st.markdown("---")
    st.subheader("Descargas rápidas")
    st.markdown(get_table_download_link(df_final, "resultados_completos_tablero.csv"), unsafe_allow_html=True)
    if df_garch_tests is not None:
        st.markdown(get_table_download_link(df_garch_tests, "garch_tests.csv"), unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Documento de referencia")
    # Developer instruction: provide local path as URL
    st.markdown(f"Artículo de referencia (PDF): [{Path(pdf_path).name}]({pdf_path})")

    st.markdown("---")
    st.write("Instrucciones para regenerar series σₜ y tests desde tu notebook:")
    st.markdown("""
    1. En tu notebook (Colab) ejecuta las funciones GARCH para cada activo y exporta:
       - Un CSV 'garch_timeseries.csv' con columnas: Fecha, Activo, sigma_t, Retorno
       - Un CSV 'garch_supuestos.csv' con columnas: Activo, ADF_p, ARCH_LM_p, Ljung_resid_p, Ljung_resid2_p, JarqueBera_p, alpha+beta
    2. Coloca esos CSV en la carpeta `data/` del repositorio y redeploy en Streamlit Cloud.
    """)

# End of app
