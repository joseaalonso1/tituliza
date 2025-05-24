import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

st.set_page_config(page_title="Simulador CRR Titulización", layout="wide")
st.title("Simulador de Titulizaciones – CRR Art. 259")

st.markdown("""
### ℹ️ Instrucciones de uso y flujo lógico

Este simulador reproduce los cálculos de titulizaciones conforme al **Artículo 259 del CRR**. El flujo recomendado es:

1. Calcular **K_IRB** a partir de RWA y EAD.
2. Definir **A y D** y ver dónde cae **K_IRB** (tramo).
3. Calcular **K_SSA** usando la fórmula supervisora.
4. Calcular el **RW y RWA** final según el tramo:

**Tramos:**
- Tramo 1: K_IRB ≤ A ⇒ RW = 1250%
- Tramo 2: A < K_IRB < D ⇒ RW = 2.5 × K_SSA
- Tramo 3: K_IRB ≥ D ⇒ RW = 12.5 × K_SSA  
⚠️ El RW mínimo es siempre **15%**

**📘 Glosario:**
- **A**, **D**: Attachment y Detachment points
- **K_IRB**: (RWA / EAD) × 8%
- **K_SSA**: Supervisory Formula result
- **RW**: Risk Weight
- **RWA**: Activo Ponderado por Riesgo
- **N**: Número efectivo de exposiciones
- **LGD**: Pérdida dado incumplimiento
- **M_T**: Madurez del tramo (1 a 5 años)
- **p**: Parámetro del CRR (depende de clasificación)
""")

# -------------------
# Funciones generales
# -------------------
def calcular_kirb(rwa, ead):
    return (rwa / ead) * 0.08 if ead > 0 else 0

def calcular_rw(K, KSSA, A, D):
    if K <= A:
        tipo = 1
        rw = 1250.0
    elif K >= D:
        tipo = 3
        rw = 12.5 * KSSA
    else:
        tipo = 2
        rw = 2.5 * KSSA
    return tipo, max(rw, 15.0)

# -------------------
# Tabs por módulo
# -------------------
tabs = st.tabs([
    "1. Calculadora K_IRB",
    "2. Tramos A-D",
    "3. K_SSA vs K_IRB",
    "4. RWAs según CRR 259"
])

# --- Calculadora K_IRB
with tabs[0]:
    st.header("1. Calculadora de K_IRB")
    rwa = st.number_input("RWA total:", min_value=0.0, value=100.0, step=0.1)
    ead = st.number_input("EAD total:", min_value=0.01, value=100.0, step=0.1)
    K = calcular_kirb(rwa, ead)
    st.markdown(f"**K_IRB = {K:.4f}** (equivale a {K*100:.2f}% del EAD)")

# --- Tramos A-D
with tabs[1]:
    st.header("2. Visualización de la posición de K_IRB frente a A y D")
    A = st.number_input("Punto A:", min_value=0.0, max_value=0.9, step=0.01, value=0.10)
    D = st.number_input("Punto D:", min_value=A+0.01, max_value=1.0, step=0.01, value=0.30)
    K = st.number_input("K_IRB:", min_value=0.0, max_value=1.0, step=0.01, value=0.15)

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
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.25), ncol=3)
    ax.set_title("Visualización método CRR – Art. 259")
    ax.grid(True)
    st.pyplot(fig)

# --- K_SSA vs K_IRB
with tabs[2]:
    st.header("3. K_SSA vs K_IRB usando fórmula CRR")
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
        ax.set_title(f"K_SSA vs K_IRB – {tipo}, {senior}, granular: {granular}")
        ax.set_xlabel("K_IRB")
        ax.set_ylabel("K_SSA")
        ax.grid(True)
        ax.legend()
        st.pyplot(fig)
        st.markdown(f"**Parámetros:** A={A_p}, B={B_p}, C={C_p}, D={D_p}, E={E_p}, LGD={LGD}, N={N}")
    else:
        st.warning("Clasificación no válida.")

# --- RWAs según CRR 259
with tabs[3]:
    st.header("4. Cálculo final de RW y RWA (CRR Art. 259)")
    kirb = st.number_input("K_IRB:", 0.0, 1.0, 0.10, 0.01)
    kssa = st.number_input("K_SSA:", 0.0, 1.0, 0.25, 0.01)
    A = st.number_input("A:", 0.0, 0.9, 0.05, 0.01)
    D = st.number_input("D:", A+0.01, 1.0, 0.30, 0.01)
    tipo, rw = calcular_rw(kirb, kssa, A, D)
    st.markdown(f"**Tipo de tramo:** {tipo}")
    st.markdown(f"**RW calculado:** {rw:.2f}%")
    st.markdown(f"**RWA sobre exposición de 100:** {rw:.2f}")

