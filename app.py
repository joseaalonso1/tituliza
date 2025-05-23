# Streamlit App para Simulador de Titulizaciones (CRR Art. 259)
# ---------------------------------------------------------------
# Este simulador reproduce los cálculos de titulizaciones conforme al Artículo 259 del CRR (Capital Requirements Regulation).
# Cada sección representa una herramienta específica de cálculo o visualización:
#
# SECCIÓN 1: Visualiza gráficamente dónde se ubica el K_IRB respecto a los puntos de Attachment (A) y Detachment (D).
# SECCIÓN 2: Calcula K_SSA usando la Supervisory Formula Approach (KSSFA) para distintas madureces y clasificaciones del portafolio.
# SECCIÓN 3: Calculadora sencilla para obtener K_IRB a partir del total de RWA y EAD de la cartera subyacente.
# SECCIÓN 4: Calculadora final de Risk Weights y RWA aplicables según el tramo identificado (tramos 1, 2, 3).
#
# GLOSARIO DE VARIABLES:
# - A: Punto de attachment (comienzo del tramo de pérdida).
# - D: Punto de detachment (final del tramo de pérdida).
# - K_IRB: Carga de capital de la cartera subyacente (Expected + Unexpected Losses).
# - K_SSA: Capital requerido según Supervisory Formula Approach.
# - RWA: Risk Weighted Assets (activo ponderado por riesgo).
# - N: Número efectivo de exposiciones.
# - LGD: Pérdida dado el incumplimiento (loss given default).
# - p: Parámetro de supervisión calculado con base en A, B, C, D, E según tipo de cartera.

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

st.set_page_config(page_title="Simulador CRR Titulización", layout="wide")
st.title("Simulador de Titulizaciones – CRR Art. 259")

# -------------------
# Funciones generales
# -------------------
def calcular_kirb(rwa, ead):
    return (rwa / ead) * 0.08 if ead > 0 else 0

def calcular_rw(K, KSSA, A, D):
    if K <= A:
        tipo = 1
        rw = 12.5 * KSSA
    elif K >= D:
        tipo = 3
        rw = 12.5
    else:
        tipo = 2
        rw = 12.5 * KSSA * (D - K) / (D - A) + 12.5 * (K - A) / (D - A)
    return tipo, max(rw, 15.0)

# -------------------
# Tabs independientes por módulo
# -------------------
tabs = st.tabs([
    "1. Tramos A-D",
    "2. K_SSA vs K_IRB",
    "3. Calculadora K_IRB",
    "4. RWAs según CRR 259"
])

# --- Tramos A-D
with tabs[0]:
    st.header("Visualización de la posición de K_IRB vs A y D")
    A = st.number_input("Punto A:", min_value=0.0, max_value=0.9, step=0.01, value=0.10, key="A1")
    D = st.number_input("Punto D:", min_value=A+0.01, max_value=1.0, step=0.01, value=0.30, key="D1")
    K = st.number_input("K_IRB:", min_value=0.0, max_value=1.0, step=0.01, value=0.15, key="K1")

    fig, ax = plt.subplots(figsize=(10, 2))
    ax.hlines(y=0.5, xmin=0, xmax=1, color='gray', linewidth=3)
    if K >= D:
        ax.axhspan(0.4, 0.6, facecolor='red', alpha=0.3)
    elif K <= A:
        ax.axhspan(0.4, 0.6, facecolor='green', alpha=0.3)
    else:
        ax.axhspan(0.4, 0.6, facecolor='orange', alpha=0.3)

    ax.hlines(y=0.5, xmin=A, xmax=D, color='blue', linewidth=6, label='Tramo A–D')
    ax.plot([K], [0.5], 'o', color='black', label=f'K_IRB = {K:.2f}')
    ax.set_xlim(-0.05, 1.05)
    ax.set_yticks([])
    ax.set_title("Visualización del método según posición de K_IRB")
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.25), ncol=3)
    ax.grid(True)
    st.pyplot(fig)

# --- K_SSA vs K_IRB con máximos
with tabs[1]:
    st.header("Gráfico dinámico K_SSA vs K_IRB según clasificación")
    tipo = st.selectbox("Tipo", ["Retail", "Non-retail"], key="tipo")
    senior = st.selectbox("Senioridad", ["Senior", "Non-senior"], key="senior")
    N = st.number_input("N (exposiciones)", min_value=1, value=30, step=1, key="N")
    LGD = st.number_input("LGD promedio", min_value=0.0, max_value=1.0, value=0.45, step=0.01, key="LGD")
    A = st.number_input("A:", 0.0, 0.9, 0.10, step=0.01, key="A2")
    D = st.number_input("D:", A+0.01, 1.0, 0.30, step=0.01, key="D2")

    granular = "granular" if tipo == "Retail" or N >= 25 else "no_granular"
    crr_params = {
        ('Retail', 'Senior', 'granular'): (0.0, 0.0, -7.48, 0.71, 0.24),
        ('Retail', 'Non-senior', 'granular'): (0.0, 0.0, -5.78, 0.55, 0.27),
        ('Non-retail', 'Senior', 'granular'): (0.0, 3.56, -1.85, 0.55, 0.07),
        ('Non-retail', 'Non-senior', 'granular'): (0.11, 2.61, -2.91, 0.68, 0.07),
        ('Non-retail', 'Senior', 'no_granular'): (0.11, 2.27, -1.73, 0.55, 0.07),
        ('Non-retail', 'Non-senior', 'no_granular'): (0.22, 2.35, -2.46, 0.48, 0.07),
    }
    key = (tipo, senior, granular)

    if key in crr_params:
        A_p, B_p, C_p, D_p, E_p = crr_params[key]
        kirb_vals = np.linspace(0.01, 0.30, 200)
        fig, ax = plt.subplots()
        for M in range(1, 6):
            p = np.maximum(0.3, A_p + B_p / N + C_p * kirb_vals + D_p * LGD + E_p * M)
            a = -1 / (p * kirb_vals)
            u = D - kirb_vals
            l = np.maximum(A, kirb_vals)
            kssa = np.where(u == l, 1.0, (np.exp(a * u) - np.exp(a * l)) / (a * (u - l)))
            kssa = np.clip(kssa, 0, 1.5)
            ax.plot(kirb_vals, kssa, label=f"M_T = {M}")
        ax.set_title(f"K_SSA vs K_IRB – Tipo: {tipo}, Senior: {senior}, Granular: {granular}")
        ax.set_xlabel("K_IRB")
        ax.set_ylabel("K_SSA")
        ax.grid(True)
        ax.legend()
        st.pyplot(fig)
        st.markdown(f"**Parámetros:** A={A_p}, B={B_p}, C={C_p}, D={D_p}, E={E_p}, LGD={LGD}, N={N}")
    else:
        st.warning("Clasificación no válida para parámetros del CRR.")

# --- Calculadora de K_IRB
with tabs[2]:
    st.header("Calculadora sencilla de K_IRB (CRR Art. 259)")
    rwa = st.number_input("RWA total:", min_value=0.0, value=100.0, step=0.1, key="rwa")
    ead = st.number_input("EAD total:", min_value=0.01, value=100.0, step=0.1, key="ead")
    K = calcular_kirb(rwa, ead)
    st.markdown(f"**K_IRB = {K:.4f}** (equivale a {K*100:.2f}% del EAD)")

# --- Calculadora de RWAs
with tabs[3]:
    st.header("Calculadora final de RWA según CRR Art. 259")
    kirb = st.number_input("K_IRB:", 0.0, 1.0, 0.10, 0.01, key="kirb")
    kssa = st.number_input("K_SSA:", 0.0, 1.0, 0.25, 0.01, key="kssa")
    A = st.number_input("A:", 0.0, 0.9, 0.05, 0.01, key="A4")
    D = st.number_input("D:", A+0.01, 1.0, 0.30, 0.01, key="D4")
    tipo, rw = calcular_rw(kirb, kssa, A, D)
    st.markdown(f"**Tipo de tramo:** {tipo}")
    st.markdown(f"**RW calculado:** {rw:.2f}%")
    st.markdown(f"**RWA sobre exposición de 100:** {rw:.2f}")
