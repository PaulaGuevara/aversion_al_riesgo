import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# =====================================================================
# CONFIGURACIÓN GENERAL
# =====================================================================

st.set_page_config(
    page_title="Aversión al Riesgo – Mercado Colombiano",
    layout="wide"
)

# =====================================================================
# CARGA DE DATOS ROBUSTA
# =====================================================================

@st.cache_data
def cargar_datos():

    df = pd.read_csv("data/resultados_completos_tablero.csv")

    # normalizar nombres de columnas
    cols = {c.lower(): c for c in df.columns}

    # renombrar (detecta automáticamente la columna con este significado)
    def col(posibles):
        for p in posibles:
            if p.lower() in cols:
                return cols[p.lower()]
        return None

    df = df.rename(columns={
        col(["activo"]): "Activo",
        col(["gamma_crra", "crra"]): "gamma_CRRA",
        col(["gamma_ftp", "ftp"]): "gamma_FTP",
        col(["gamma_garch", "garch"]): "gamma_GARCH",
        col(["vol_hist", "volatilidad", "vol"]): "Vol_Hist",
        col(["sigma_garch", "sigma_last", "vol_garch"]): "Vol_GARCH"
    })

    # limpiar nombres de acciones
    df["Activo"] = df["Activo"].str.replace("Datos históricos de ", "", regex=False)
    df["Activo"] = df["Activo"].str.replace(r" \(.+\)", "", regex=True)

    # excluir series macro
    df_filtrado = df[~df["Activo"].isin(["TPM", "IBR", "DTB3"])]

    return df, df_filtrado

df_original, df = cargar_datos()

# =====================================================================
# SIDEBAR – NAVEGACIÓN
# =====================================================================

pagina = st.sidebar.radio(
    "Navegación",
    [
        "Resumen General",
        "Aversión al Riesgo por Acción",
        "Volatilidad por Acción",
        "Tabla Completa"
    ]
)

# =====================================================================
# PÁGINA 1 — RESUMEN GENERAL
# =====================================================================

if pagina == "Resumen General":

    st.title("Aversión al Riesgo Implícita en el Mercado Colombiano")

    st.subheader("Contexto General")
    st.markdown("""
El análisis sigue la metodología del estudio de Chávez, Milanesi y Pesce (2021),
estimando la aversión al riesgo implícita en activos financieros mediante:

**CRRA (Constant Relative Risk Aversion)**  
Función de utilidad estándar donde gamma mide la curvatura y, por tanto,
la intensidad de rechazo al riesgo.

**FTP (Función de Tres Parámetros)**  
Extensión más flexible que incorpora elasticidad y curvatura, permitiendo
representar preferencias no lineales ante el riesgo.

**Modelos GARCH**  
Modelos de volatilidad condicional que permiten estimar gamma usando
una volatilidad que varía en el tiempo, reflejando mejor la incertidumbre
observada en los mercados.

El estudio compara cómo cada enfoque captura la aversión al riesgo
en acciones colombianas entre 2020 y 2025.
""")

    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    col1.metric("Gamma promedio CRRA", f"{df['gamma_CRRA'].mean():.3f}")
    col2.metric("Gamma promedio FTP", f"{df['gamma_FTP'].mean():.3f}")
    col3.metric("Gamma promedio GARCH", f"{df['gamma_GARCH'].mean():.3f}")

    st.markdown("---")

    st.subheader("Distribución de Gamma por Método")

    metodo = st.selectbox(
        "Seleccione método:",
        ["CRRA", "FTP", "GARCH"]
    )

    col_map = {
        "CRRA": "gamma_CRRA",
        "FTP": "gamma_FTP",
        "GARCH": "gamma_GARCH"
    }

    fig = px.box(
        df,
        y=col_map[metodo],
        title=f"Distribución de gamma ({metodo})",
        labels={col_map[metodo]: "Gamma"}
    )
    st.plotly_chart(fig, use_container_width=True)

# =====================================================================
# PÁGINA 2 — AVERSIÓN POR ACCIÓN
# =====================================================================

elif pagina == "Aversión al Riesgo por Acción":

    st.title("Aversión al Riesgo por Acción")

    accion = st.selectbox("Seleccione una acción:", df["Activo"].unique())

    subset = df[df["Activo"] == accion]

    st.subheader("Comparación de gamma por método")

    fig = px.bar(
        subset,
        x="Activo",
        y=["gamma_CRRA", "gamma_FTP", "gamma_GARCH"],
        barmode="group",
        labels={"value": "Gamma", "variable": "Método"},
        title=f"Aversión al riesgo estimada para {accion}"
    )
    st.plotly_chart(fig, use_container_width=True)

# =====================================================================
# PÁGINA 3 — VOLATILIDAD
# =====================================================================

elif pagina == "Volatilidad por Acción":

    st.title("Volatilidad por Acción")

    accion = st.selectbox("Seleccione una acción:", df["Activo"].unique(), key="vol")

    subset = df[df["Activo"] == accion]

    st.subheader("Volatilidad histórica vs. GARCH")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=["Histórica"],
        y=[subset["Vol_Hist"].values[0]],
        name="Volatilidad Histórica"
    ))
    fig.add_trace(go.Bar(
        x=["GARCH"],
        y=[subset["Vol_GARCH"].values[0]],
        name="Volatilidad GARCH"
    ))
    fig.update_layout(title=f"Volatilidad del activo: {accion}", barmode="group")
    st.plotly_chart(fig, use_container_width=True)

# =====================================================================
# PÁGINA 4 — TABLA COMPLETA
# =====================================================================

elif pagina == "Tabla Completa":

    st.title("Tabla Completa de Resultados")
    st.dataframe(df_original, use_container_width=True)
