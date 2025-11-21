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
    layout="wide",
    initial_sidebar_state="expanded"
)

# Tema gris con azul - Paleta profesional
color_palette = ["#1E3A8A", "#3B82F6", "#60A5FA", "#93C5FD", "#BFDBFE", 
                 "#1E40AF", "#2563EB", "#3B82F6", "#60A5FA", "#93C5FD"]
bg_color = "#F3F4F6"
text_color = "#1F2937"

# Aplicar estilos CSS personalizados
st.markdown("""
    <style>
    /* Fondo general */
    .main {
        background-color: #F3F4F6;
    }
    
    /* Títulos */
    h1, h2, h3 {
        color: #1E3A8A;
    }
    
    /* Sidebar con fondo azul oscuro */
    [data-testid="stSidebar"] {
        background-color: #1E3A8A;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        background-color: #1E3A8A;
    }
    
    /* Texto en sidebar */
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Métricas */
    [data-testid="stMetricValue"] {
        color: #1E3A8A;
        font-weight: bold;
    }
    
    /* Tablas */
    .dataframe {
        background-color: white;
    }
    
    /* Botones y selectores */
    .stButton>button {
        background-color: #3B82F6;
        color: white;
    }
    
    .stButton>button:hover {
        background-color: #1E3A8A;
    }
    </style>
""", unsafe_allow_html=True)

plotly_template = "simple_white"

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
# SIDEBAR - LOGO Y NAVEGACIÓN
# ============================================================

with st.sidebar:
    # Logo en la barra lateral
    st.image(
        "https://usantotomas.edu.co/hs-fs/hubfs/social-suggested-images/usantotomas.edu.cohs-fshubfsLogo%20Santoto%20-%20SP%20Bogota%20Horizontal%20blanco-2.png",
        use_container_width=True
    )
    
    st.markdown("---")
    
    # Menú de navegación
    page = st.radio(
        "**Navegación**",
        [
            "Contexto",
            "Aversión al riesgo",
            "Volatilidad dinámica",
            "Volatilidad histórica vs dinámica",
            "Diagnósticos GARCH"
        ]
    )
    
    st.markdown("---")
    st.markdown("**Responsables:**")
    st.markdown("Paula Ximena Guevara G.")
    st.markdown("Natalia Zárate Yara")
    st.markdown("---")
    st.caption("Universidad Santo Tomás")
    st.caption("Facultad de Estadística")
    st.caption("2025")

# ============================================================
# 1. CONTEXTO
# ============================================================

if page == "Contexto":

    st.title("Aversión al Riesgo en el Mercado Colombiano (2020–2025)")

    st.markdown("""
    <div style='background-color: white; padding: 20px; border-radius: 10px; border-left: 5px solid #1E3A8A;'>
    <p style='color: #1F2937; font-size: 16px;'>
    Este tablero presenta los resultados del análisis de <b>aversión al riesgo implícita</b> en el mercado colombiano,
    replicando la metodología de <b>Chávez, Milanesi y Pesce (2021)</b>.
    </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("##")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style='background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
        <h4 style='color: #1E3A8A;'>CRRA</h4>
        <p style='color: #4B5563;'><b>Constant Relative Risk Aversion</b></p>
        <p style='color: #6B7280;'>Mide la concavidad de la utilidad bajo riesgo con aversión relativa constante.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
        <h4 style='color: #1E3A8A;'>FTP</h4>
        <p style='color: #4B5563;'><b>Flexible Three-Parameter</b></p>
        <p style='color: #6B7280;'>Modelo más flexible que captura preferencias no lineales con tres parámetros.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style='background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
        <h4 style='color: #1E3A8A;'>GARCH(1,1)</h4>
        <p style='color: #4B5563;'><b>Volatilidad Condicional</b></p>
        <p style='color: #6B7280;'>Usa la volatilidad condicional σₜ en lugar de volatilidad histórica.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("##")
    
    # ============================
    # KPIs
    # ============================

    st.subheader("Indicadores Principales")

    c1, c2, c3 = st.columns(3)

    if df_full is not None:
        df_filtered = df_full[~df_full["Activo"].isin(excluir_macro)]

        gamma_crra_mean  = df_filtered["gamma_CRRA"].mean()
        gamma_ftp_mean   = df_filtered["gamma_FTP"].mean()
        gamma_garch_mean = df_filtered["gamma_GARCH"].mean()

        c1.metric("γ CRRA Promedio", f"{gamma_crra_mean:.4f}", help="Coeficiente promedio bajo CRRA")
        c2.metric("γ FTP Promedio", f"{gamma_ftp_mean:.4f}", help="Coeficiente promedio bajo FTP")
        c3.metric("γ GARCH Promedio", f"{gamma_garch_mean:.4f}", help="Coeficiente promedio bajo GARCH")

    st.markdown("##")
    
    # ============================
    # Gráfico inicial - BARRAS
    # ============================

    st.subheader("Comparación General de γ por Método")

    df_long = df_filtered.melt(
        id_vars="Activo",
        value_vars=["gamma_CRRA", "gamma_FTP", "gamma_GARCH"],
        var_name="Método",
        value_name="Gamma"
    )
    
    # Renombrar métodos
    df_long["Método"] = df_long["Método"].replace({
        "gamma_CRRA": "CRRA",
        "gamma_FTP": "FTP",
        "gamma_GARCH": "GARCH"
    })

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
    
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(showgrid=False, title='Activo'),
        yaxis=dict(showgrid=True, gridcolor='#E5E7EB', title='Coeficiente γ'),
        showlegend=True
    )

    st.plotly_chart(fig, use_container_width=True)
    
    st.caption("**Interpretación:** Este gráfico muestra los coeficientes de aversión al riesgo estimados para cada activo bajo las tres metodologías. FTP tiende a generar valores más altos que CRRA, indicando mayor sensibilidad a riesgos extremos.")

# ============================================================
# 2. AVERSIÓN AL RIESGO COMPLETA
# ============================================================

elif page == "Aversión al riesgo":

    st.title("Aversión al Riesgo – CRRA, FTP y GARCH")

    if df_full is None:
        st.error("No se encontró resultados_completos_tablero.csv")
        st.stop()

    df = df_full[~df_full["Activo"].isin(excluir_macro)].copy()

    st.subheader("Tabla de Resultados")
    
    # Tabla sin estilos de color
    st.dataframe(df.round(4), use_container_width=True)
    
    st.caption("**Tabla:** Coeficientes γ estimados bajo las metodologías CRRA, FTP y GARCH para cada activo financiero colombiano.")

    st.markdown("##")
    
    st.subheader("Comparación Visual")

    df_long = df.melt(
        id_vars="Activo",
        value_vars=["gamma_CRRA","gamma_FTP","gamma_GARCH"],
        var_name="Método", 
        value_name="Gamma"
    )
    
    # Renombrar métodos
    df_long["Método"] = df_long["Método"].replace({
        "gamma_CRRA": "CRRA",
        "gamma_FTP": "FTP",
        "gamma_GARCH": "GARCH"
    })

    # Gráfico de líneas
    fig = go.Figure()
    
    metodos = df_long["Método"].unique()
    colores_metodo = {
        "CRRA": color_palette[0],
        "FTP": color_palette[1],
        "GARCH": color_palette[2]
    }
    
    for metodo in metodos:
        df_metodo = df_long[df_long["Método"] == metodo]
        fig.add_trace(go.Scatter(
            x=df_metodo["Activo"],
            y=df_metodo["Gamma"],
            mode='lines+markers',
            name=metodo,
            line=dict(color=colores_metodo[metodo], width=3),
            marker=dict(size=8)
        ))
    
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(showgrid=False, title='Activo'),
        yaxis=dict(showgrid=True, gridcolor='#E5E7EB', title='Coeficiente γ'),
        height=600,
        hovermode='x unified',
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.caption("**Análisis:** Las líneas permiten comparar directamente los tres métodos. GARCH suele producir valores intermedios al considerar la volatilidad dinámica del mercado.")

# ============================================================
# 3. VOLATILIDAD DINÁMICA σₜ
# ============================================================

elif page == "Volatilidad dinámica":

    st.title("Volatilidad Dinámica – Modelo GARCH(1,1)")

    if df_timeseries is None:
        st.error("No se encontró garch_timeseries.csv")
        st.stop()

    df = df_timeseries.copy()
    df["Fecha"] = pd.to_datetime(df["Fecha"])

    df = df[~df["Activo"].isin(excluir_macro)]

    activos = sorted(df["Activo"].unique())

    st.markdown("""
    <div style='background-color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px;'>
    <p style='color: #4B5563; margin: 0;'>
    La <b>volatilidad condicional (σₜ)</b> captura la variabilidad cambiante del mercado a lo largo del tiempo,
    ajustándose dinámicamente a periodos de alta y baja incertidumbre.
    </p>
    </div>
    """, unsafe_allow_html=True)

    activos_sel = st.multiselect(
        "Seleccione acciones para comparar:",
        activos,
        default=activos,  # Todas las acciones por defecto
        help="Puede seleccionar múltiples acciones para comparar su volatilidad"
    )

    if len(activos_sel) == 0:
        st.warning("Por favor seleccione al menos una acción.")
        st.stop()

    df_plot = df[df["Activo"].isin(activos_sel)]

    # Gráfico de líneas con colores distintos
    fig = go.Figure()
    
    # Asignar colores a cada activo
    colores_activos = {}
    palette_extended = color_palette * ((len(activos_sel) // len(color_palette)) + 1)
    
    for i, activo in enumerate(sorted(activos_sel)):
        colores_activos[activo] = palette_extended[i]
        df_activo = df_plot[df_plot["Activo"] == activo]
        
        fig.add_trace(go.Scatter(
            x=df_activo["Fecha"],
            y=df_activo["sigma_t"],
            mode='lines',
            name=activo,
            line=dict(color=palette_extended[i], width=2.5)
        ))
    
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(showgrid=False, title='Fecha'),
        yaxis=dict(showgrid=True, gridcolor='#E5E7EB', title='Volatilidad Condicional (σₜ)'),
        height=600,
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99,
            bgcolor="rgba(255,255,255,0.8)"
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.caption("**Interpretación:** Los picos en la volatilidad condicional reflejan momentos de incertidumbre en el mercado (crisis, anuncios económicos, etc.). GARCH permite capturar estos cambios de manera más precisa que la volatilidad histórica.")

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

    st.markdown("""
    <div style='background-color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px;'>
    <p style='color: #4B5563; margin: 0;'>
    Compare la <b>volatilidad histórica</b> (constante en ventanas móviles) con la <b>volatilidad GARCH</b> 
    (que se adapta a la información más reciente del mercado).
    </p>
    </div>
    """, unsafe_allow_html=True)

    activos = sorted(df["Activo"].unique())
    activo_sel = st.selectbox(
        "Seleccione una acción:",
        activos,
        help="Elija un activo para visualizar la comparación"
    )

    df_sel = df[df["Activo"] == activo_sel]

    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df_sel["Fecha"], 
        y=df_sel["vol_hist"],
        mode="lines", 
        name="Volatilidad Histórica",
        line=dict(color=color_palette[0], width=2.5)
    ))
    
    fig.add_trace(go.Scatter(
        x=df_sel["Fecha"], 
        y=df_sel["sigma_t"],
        mode="lines", 
        name="Volatilidad GARCH (σₜ)",
        line=dict(color=color_palette[1], width=2.5)
    ))
    
    fig.update_layout(
        height=600,
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(showgrid=False, title='Fecha'),
        yaxis=dict(showgrid=True, gridcolor='#E5E7EB', title='Volatilidad'),
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255,255,255,0.8)"
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)

    st.caption("**Análisis:** La volatilidad GARCH reacciona más rápidamente a los cambios del mercado, mientras que la histórica es más suavizada. Los momentos donde GARCH supera significativamente a la histórica indican periodos de turbulencia no anticipada.")

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

    st.markdown("""
    <div style='background-color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px;'>
    <p style='color: #4B5563; margin: 0;'>
    Los siguientes tests validan que el modelo GARCH(1,1) sea apropiado para modelar 
    la volatilidad condicional de los retornos financieros.
    </p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Resultados de Pruebas Estadísticas")
    
    # Tabla sin colores
    st.dataframe(df, use_container_width=True)
    
    st.caption("**Tabla:** Resultados de las pruebas estadísticas para validar los supuestos del modelo GARCH.")

    st.markdown("##")
    
    # ============================
    # INTERPRETACIÓN DE CADA TEST
    # ============================
    
    st.subheader("Interpretación de los Diagnósticos")
    
    with st.expander("**1. Prueba ADF (Augmented Dickey-Fuller)**", expanded=True):
        st.markdown("""
        **Objetivo:** Verificar si la serie de rendimientos es estacionaria.
        
        - **Hipótesis nula (H₀):** La serie tiene raíz unitaria (no es estacionaria)
        - **Interpretación:**
            - **p-value < 0.05:** Rechazamos H₀ → La serie ES estacionaria (Supuesto cumplido)
            - **p-value > 0.05:** No rechazamos H₀ → La serie NO es estacionaria (Problema)
        
        **¿Por qué importa?** GARCH requiere que los rendimientos sean estacionarios para que el modelo sea válido.
        """)
    
    with st.expander("**2. Test ARCH-LM (Heteroscedasticidad Condicional)**"):
        st.markdown("""
        **Objetivo:** Detectar si quedan efectos ARCH en los residuales después de ajustar GARCH.
        
        - **Hipótesis nula (H₀):** No hay efectos ARCH en los residuales
        - **Interpretación:**
            - **p-value > 0.05:** No rechazamos H₀ → No hay heteroscedasticidad residual (Modelo adecuado)
            - **p-value < 0.05:** Rechazamos H₀ → Aún hay efectos ARCH (El modelo no captura toda la volatilidad)
        
        **¿Por qué importa?** Si el test rechaza, significa que GARCH(1,1) es insuficiente y necesitaríamos más rezagos.
        """)
    
    with st.expander("**3. Test Ljung-Box (Residuales)**"):
        st.markdown("""
        **Objetivo:** Verificar que no haya autocorrelación en los residuales estandarizados.
        
        - **Hipótesis nula (H₀):** No hay autocorrelación en los residuales
        - **Interpretación:**
            - **p-value > 0.05:** No rechazamos H₀ → Residuales son ruido blanco (Modelo bien especificado)
            - **p-value < 0.05:** Rechazamos H₀ → Hay autocorrelación (El modelo no captura toda la estructura)
        
        **¿Por qué importa?** Si hay autocorrelación, el modelo GARCH no está capturando toda la dinámica temporal.
        """)
    
    with st.expander("**4. Test Ljung-Box (Residuales²)**"):
        st.markdown("""
        **Objetivo:** Verificar que no haya autocorrelación en los residuales al cuadrado (proxy de volatilidad).
        
        - **Hipótesis nula (H₀):** No hay autocorrelación en los residuales²
        - **Interpretación:**
            - **p-value > 0.05:** No rechazamos H₀ → No hay estructura residual en la volatilidad (GARCH captura la volatilidad)
            - **p-value < 0.05:** Rechazamos H₀ → Aún hay estructura (Necesita ajustes)
        
        **¿Por qué importa?** Es crucial para validar que GARCH capturó correctamente los clusters de volatilidad.
        """)
    
    with st.expander("**5. Test Jarque-Bera (Normalidad)**"):
        st.markdown("""
        **Objetivo:** Evaluar si los residuales estandarizados siguen una distribución normal.
        
        - **Hipótesis nula (H₀):** Los residuales siguen una distribución normal
        - **Interpretación:**
            - **p-value > 0.05:** No rechazamos H₀ → Residuales son aproximadamente normales
            - **p-value < 0.05:** Rechazamos H₀ → Residuales tienen colas pesadas o asimetría
        
        **¿Por qué importa?** Si se rechaza, podríamos considerar GARCH con distribución t-Student en lugar de normal.
        
        **Nota:** Es común que este test rechace en datos financieros debido a eventos extremos (colas pesadas).
        """)
    
    with st.expander("**6. Condición α + β < 1**"):
        st.markdown("""
        **Objetivo:** Verificar la estacionariedad de la varianza condicional.
        
        - **Condición requerida:** α + β < 1
        - **Interpretación:**
            - **α + β < 1:** La volatilidad es estacionaria (El modelo es estable)
            - **α + β ≥ 1:** Volatilidad no estacionaria (Proceso explosivo o integrado)
        
        **¿Por qué importa?** Si α + β ≥ 1, los shocks de volatilidad persisten indefinidamente (no hay reversión a la media).
        
        **Valores típicos:**
        - α (ARCH): 0.05 - 0.15 (impacto de shocks recientes)
        - β (GARCH): 0.80 - 0.90 (persistencia de volatilidad pasada)
        - Suma: 0.85 - 0.98 (cercano a 1 indica alta persistencia)
        """)
    
    st.markdown("##")
    
    # ============================
    # CONCLUSIÓN
    # ============================
    
    st.info("""
    **Conclusión General:**
    
    La aversión al riesgo implícita en el mercado financiero colombiano entre 2020 y 2025 fue estimada mediante funciones de utilidad CRRA y FTP junto con medidas de volatilidad histórica y condicional GARCH(1,1). Los resultados muestran que la aversión al riesgo bajo CRRA es baja y estable, mientras que la función FTP genera valores más altos debido a su sensibilidad a colas pesadas. Aunque los modelos GARCH capturan adecuadamente la dinámica de la volatilidad, la volatilidad condicional no altera de manera significativa el coeficiente de aversión al riesgo estimado. En conjunto, el análisis evidencia que, pese a la alta persistencia de la volatilidad en Colombia, la aversión al riesgo basada en CRRA se mantiene rígida frente a los cambios en la incertidumbre, lo que resalta la importancia de explorar funciones de utilidad o metodologías más flexibles en estudios futuros.
    
    """)
