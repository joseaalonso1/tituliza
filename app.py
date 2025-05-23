# Streamlit App para Simulador de Titulizaciones (CRR Art. 259)
# ---------------------------------------------------------------
# Despliegue interactivo de la calculadora de K_IRB, K_SSA y RWA
# Requiere: streamlit, numpy

import streamlit as st
import numpy as np

st.set_page_config(page_title="Simulador CRR Titulización", layout="centered")
st.title("Simulador de Titulizaciones – CRR Art. 259")
st.markdown("""
Este simulador permite calcular:
- **K_IRB** conforme a RWA/EAD (Art. 259.2)
- **K_SSA** con la fórmula supervisora (Art. 259.3)
- **RW** según el tipo de tramo (1, 2 o 3) incluyendo el mínimo del 15%
""")

# Entradas del usuario
st.sidebar.header("Entradas")
rwa_pool = st.sidebar.number_input("RWA del portafolio (millones)", min_value=0.0, value=100.0)
ead_pool = st.sidebar.number_input("EAD del portafolio (millones)", min_value=0.01, value=100.0)
K = st.sidebar.number_input("K_IRB manual (opcional)", min_value=0.0, max_value=1.0, value=0.10)
A = st.sidebar.number_input("Punto de Attachment (A)", min_value=0.0, max_value=1.0, value=0.05)
D = st.sidebar.number_input("Punto de Detachment (D)", min_value=0.0, max_value=1.0, value=0.30)
p = st.sidebar.number_input("Parámetro p", min_value=0.01, max_value=1.0, value=0.5)

# Funciones

def calcular_kirb(rwa, ead):
    return (rwa / ead) * 0.08

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

# Cálculos
kirb_calc = calcular_kirb(rwa_pool, ead_pool)
kssa_calc = calcular_kssa(K, A, D, p)
tipo, rw_final = calcular_rw(K, kssa_calc, A, D)

# Resultados
st.subheader("Resultados")
st.markdown(f"**K_IRB calculado:** {kirb_calc:.4f}  ")
st.markdown(f"**K_SSA calculado:** {kssa_calc:.4f}  ")
st.markdown(f"**Tipo de tramo (CRR Art. 259):** {tipo}")
st.markdown(f"**Risk Weight aplicado (RW):** {rw_final:.2f}%")
st.markdown(f"**RWA resultante por cada 100 de exposición:** {rw_final:.2f}")

st.info("Versión simplificada del CRR. Asegúrese de validar con su equipo de riesgo para producción.")
