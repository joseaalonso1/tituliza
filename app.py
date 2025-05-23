# Streamlit App para Simulador de Titulizaciones (CRR Art. 259)
# ---------------------------------------------------------------
# Basado íntegramente en el desarrollo realizado en simulador_titu.ipynb
# Se mantienen: inputs, lógica de cálculo, y estructura por bloques.

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

st.set_page_config(page_title="Simulador CRR Titulización", layout="centered")
st.title("Simulador de Titulizaciones – CRR Art. 259")

# -------------------
# Funciones base del modelo
# -------------------
def calcular_kirb(rwa, ead):
    return (rwa / ead) * 0.08 if ead > 0 else 0

def calcular_kssa(K, A, D, p):
    a = -1 / (p * K)
    u = D - K
    l = max(A, K)
    if u == l:
        return 1.0
    try:
        return max(0.0, min((np.exp(a * u) - np.exp(a * l)) / (a * (u - l)), 1.5))
    except OverflowError:
        return 1.0

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
# Entradas base
# -------------------
st.sidebar.header("Inputs generales")
rwa_pool = st.sidebar.number_input("RWA total", value=100.0)
ead_pool = st.sidebar.number_input("EAD total", value=100.0)
K_irb_manual = st.sidebar.number_input("K_IRB (manual)", min_value=0.01, max_value=1.0, value=0.10)
A_global = st.sidebar.slider("Punto A", 0.0, 0.9, 0.2, step=0.01)
D_global = st.sidebar.slider("Punto D", A_global + 0.01, 1.0, 0.8, step=0.01)
p_valor = st.sidebar.slider("Parámetro p", 0.1, 1.0, 0.5, step=0.01)

# -------------------
# Tabs seccionadas (estructura original)
# -------------------
tabs = st.tabs(["Puntos A-D", "K_SSA vs K_IRB", "K_IRB calculado", "RW y RWA"])

# Puntos A-D
with tabs[0]:
    st.subheader("Visualización del tramo [A-D] sobre el eje")
    fig, ax = plt.subplots()
    ax.hlines(1, 0, 1, colors='gray', linestyles='--')
    ax.vlines([A_global, D_global], 0, 1, colors='red', linestyles='-', label='A, D')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.1)
    ax.set_title("Representación visual de A-D")
    st.pyplot(fig)

# K_SSA vs K_IRB
with tabs[1]:
    st.subheader("Cálculo de K_SSA vs K_IRB (5 madureces)")
    kirb_range = np.linspace(0.01, 0.30, 200)
    fig, ax = plt.subplots()
    for M in range(1, 6):
        kssa_values = [calcular_kssa(K, A_global, D_global, p_valor + 0.05 * M) for K in kirb_range]
        ax.plot(kirb_range, kssa_values, label=f"M_T = {M}")
    ax.set_xlabel("K_IRB")
    ax.set_ylabel("K_SSA")
    ax.set_title("K_SSA vs K_IRB para diferentes M_T")
    ax.legend()
    st.pyplot(fig)

# K_IRB calculado
with tabs[2]:
    st.subheader("Cálculo automático de K_IRB")
    kirb_calculado = calcular_kirb(rwa_pool, ead_pool)
    st.metric(label="K_IRB calculado (RWA / EAD × 0.08)", value=f"{kirb_calculado:.4f}")

# RW y RWA
with tabs[3]:
    st.subheader("Evaluación de RWA y tipo de tramo")
    kssa_calculado = calcular_kssa(K_irb_manual, A_global, D_global, p_valor)
    tipo_tramo, rw_aplicado = calcular_rw(K_irb_manual, kssa_calculado, A_global, D_global)
    st.markdown(f"**K_SSA resultante:** {kssa_calculado:.4f}")
    st.markdown(f"**Tipo de tramo:** {tipo_tramo}")
    st.markdown(f"**RW aplicado (mínimo 15%):** {rw_aplicado:.2f}%")
    st.markdown(f"**RWA para exposición de 100:** {rw_aplicado:.2f}")
    st.info("Este análisis aplica el Artículo 259 del CRR para titulizaciones bajo SEC-IRBA")
