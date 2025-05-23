# Streamlit App para Simulador de Titulizaciones (CRR Art. 259)
# ---------------------------------------------------------------
# Cuatro secciones separadas:
# 1. Visualización de puntos A-D
# 2. K_SSA vs K_IRB
# 3. Cálculo de K_IRB
# 4. Cálculo de RWA (tipos 1-2-3)

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Simulador CRR Titulización", layout="centered")
st.title("Simulador de Titulizaciones – CRR Art. 259")

# --- Funciones auxiliares ---
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

# --- Secciones de la app ---
tabs = st.tabs(["Puntos A-D", "K_SSA vs K_IRB", "K_IRB", "RWAs"])

# 1. Puntos A-D
with tabs[0]:
    st.subheader("Visualización de puntos A-D")
    A = st.slider("Punto A", 0.0, 0.9, 0.2)
    D = st.slider("Punto D", A+0.01, 1.0, 0.8)
    fig, ax = plt.subplots()
    ax.hlines(1, 0, 1, color='gray', linestyle='--')
    ax.vlines([A, D], 0, 1, color='red', linestyle='-', label='Puntos A y D')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.1)
    ax.set_title("Ubicación de puntos A-D sobre tramo")
    st.pyplot(fig)

# 2. K_SSA vs K_IRB
with tabs[1]:
    st.subheader("Gráfico K_SSA vs K_IRB")
    A = st.number_input("A", 0.0, 1.0, 0.05)
    D = st.number_input("D", A+0.01, 1.0, 0.30)
    p = st.number_input("Parámetro p", 0.01, 1.0, 0.5)
    kirb_range = np.linspace(0.01, 0.30, 100)
    fig, ax = plt.subplots()
    for M in range(1, 6):
        kssa_vals = [calcular_kssa(K, A, D, p + 0.05 * M) for K in kirb_range]
        ax.plot(kirb_range, kssa_vals, label=f"M_T = {M}")
    ax.set_xlabel("K_IRB")
    ax.set_ylabel("K_SSA")
    ax.set_title("K_SSA vs K_IRB por madurez")
    ax.legend()
    st.pyplot(fig)

# 3. K_IRB
with tabs[2]:
    st.subheader("Cálculo de K_IRB")
    rwa = st.number_input("RWA del pool", 0.0, 10000.0, 100.0)
    ead = st.number_input("EAD del pool", 0.01, 10000.0, 100.0)
    kirb = calcular_kirb(rwa, ead)
    st.markdown(f"**K_IRB =** {kirb:.4f}")

# 4. RWA por tipo (CRR Art. 259)
with tabs[3]:
    st.subheader("Evaluación del RW y RWA")
    K = st.number_input("K_IRB (manual)", 0.0, 1.0, 0.10)
    KSSA = st.number_input("K_SSA", 0.0, 1.0, 0.25)
    A = st.number_input("A", 0.0, 1.0, 0.05)
    D = st.number_input("D", A+0.01, 1.0, 0.30)
    tipo, rw = calcular_rw(K, KSSA, A, D)
    st.markdown(f"**Tipo de tramo:** {tipo}")
    st.markdown(f"**RW aplicado:** {rw:.2f}%")
    st.markdown(f"**RWA por cada 100 de exposición:** {rw:.2f}")
