import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="Aversión al Riesgo – Mercado Colombiano",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# FUNCIÓN DE CARGA Y LIMPIEZA DE DATOS
# ============================================================

@st.cache_data
def cargar_datos():

    df = pd.read_csv("data/resultados_completos_tablero.csv")

    # Renombrar columnas a formato más limpio
    df = df.rename(columns={
        "Activo": "Activo",
        "gamma_CRRA": "gamma_CRRA",
        "gamma_FTP": "gamma_FTP",
        "gamma_GARCH": "gamma_GARCH",
        "vol_hist": "Vol_Hist",
        "sigma_garch": "Vol_GARCH"
    })

    # Limpieza de nombres de activos
    df["Activo"] = df["Activo"].str.replace("Datos históricos de ", "", regex=False)
    df["Activo"] = df["Activo"].str.replace(" (.*)", "", regex=True)

    # Excluir TPM, IBR y DTB3 de las gráficas comparativas
    df_filtrado = df[~df["Activo"].isin(["TPM", "IBR", "DTB3"])]

    return df, df_filtrado

df_original, df = cargar_datos()

# ============================================================
# SIDEBAR – NAVEGACIÓN
# ============================================================

pagina = st.sidebar.radio(
    "Navegación",
    [
        "Resumen General",
        "Comparación de Aversión al Riesgo",
        "Volatilidad: Histórica vs GARCH",
        "Diagnósticos y Resultados",
        "Tabla Completa"
    ]
)

# ============================================================
# PÁGINA 1 — RESUMEN GENERAL
# ============================================================

if pagina == "Resumen General":

    st.title("Aversión al Riesgo Implícita en el Mercado Colombiano")

    st.subheader("Contexto del Estudio")

    st.markdown("""
El tablero presenta un análisis de aversión al riesgo para el mercado colombiano,
siguiendo la metodología del estudio de **Chávez, Milanesi y Pesce (2021)**, aplicado a datos
de acciones e indicadores financieros entre 2020 y 2025.

El objetivo es estimar el coeficiente de aversión al riesgo gamma (γ) bajo tres enfoques:

**1. CRRA — Coeficiente de Aversión Relativa al Riesgo Constante**  
Modelo clásico de utilidad donde gamma mide la curvatura de la función de utilidad.
Valores más altos implican mayor rechazo a la variabilidad en rendimientos.

**2. FTP — Función de Tres Parámetros**  
Extensión flexible del modelo CRRA que incorpora elasticidad y curvatura.
Permite capturar patrones no lineales en la aversión al riesgo.

**3. Modelo GARCH**  
Modelo econométrico que estima volatilidad condicional.  
Su volatilidad dinámica se utiliza como insumo para recalcular gamma
y evaluar cómo cambia la aversión al riesgo cuando la incertidumbre no es constante.

El análisis permite comparar cómo varía la percepción de riesgo según el método utilizado
y según las condiciones del mercado.
""")

    st.markdown("___")

    # KPI
    col1, col2, col3 = st.columns(3)
    col1.metric("Gamma promedio CRRA", f"{df['gamma_CRRA'].mean():.3f}")
    col2.metric("Gamma promedio FTP", f"{df['gamma_FTP'].mean():.3f}")
    col3.metric("Gamma promedio GARCH", f"{df['gamma_GARCH'].mean():.3f}")

    st.markdown("___")

    st.subheader("Distribución general de gamma por método")

    fig = px.box(
        df,
        y=["gamma_CRRA", "gamma_FTP", "gamma_GARCH"],
        labels={"variable": "Método", "value": "Gamma"},
        title="Distribución de Gamma por Método"
    )
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# PÁGINA 2 — COMPARACIÓN DE AVERSIÓN AL RIESGO
# ============================================================

elif pagina == "Comparación de Aversión al Riesgo":

    st.title("Comparación de Aversión al Riesgo por Activo")

    st.subheader("Gamma por método")

    fig = px.bar(
        df,
        x="Activo",
        y=["gamma_CRRA", "gamma_FTP", "gamma_GARCH"],
        barmode="group",
        title="Gamma por Activo y Método",
        labels={"value": "Gamma", "variable": "Método"},
        height=600
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("___")

    st.subheader("Relación entre Métodos")

    fig2 = px.scatter(
        df,
        x="gamma_CRRA",
        y="gamma_FTP",
        text="Activo",
        title="Relación entre Gamma CRRA y Gamma FTP",
        labels={"gamma_CRRA": "Gamma CRRA", "gamma_FTP": "Gamma FTP"}
    )
    fig2.update_traces(textposition="top center")
    st.plotly_chart(fig2, use_container_width=True)

# ============================================================
# PÁGINA 3 — VOLATILIDAD
# ============================================================

elif pagina == "Volatilidad: Histórica vs GARCH":

    st.title("Volatilidad Histórica y Volatilidad GARCH")

    st.subheader("Comparación de Volatilidad por Activo")

    fig = px.bar(
        df,
        x="Activo",
        y=["Vol_Hist", "Vol_GARCH"],
        barmode="group",
        labels={"value": "Volatilidad"},
        title="Volatilidad Histórica y GARCH por Activo",
        height=600
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("___")

    st.subheader("Relación entre volatilidad y aversión al riesgo")

    fig2 = px.scatter(
        df,
        x="Vol_GARCH",
        y="gamma_GARCH",
        text="Activo",
        labels={"Vol_GARCH": "Volatilidad GARCH", "gamma_GARCH": "Gamma GARCH"},
        title="Gamma GARCH vs Volatilidad Condicional"
    )
    fig2.update_traces(textposition="top center")
    st.plotly_chart(fig2, use_container_width=True)

# ============================================================
# PÁGINA 4 — DIAGNÓSTICOS
# ============================================================

elif pagina == "Diagnósticos y Resultados":

    st.title("Resultados y Diagnósticos")

    st.subheader("Estadísticas generales")

    st.dataframe(
        df[["Activo", "gamma_CRRA", "gamma_FTP", "gamma_GARCH", "Vol_Hist", "Vol_GARCH"]],
        use_container_width=True
    )

# ============================================================
# PÁGINA 5 — TABLA COMPLETA
# ============================================================

elif pagina == "Tabla Completa":

    st.title("Tabla Completa de Resultados")
    st.dataframe(df_original, use_container_width=True)
