# Simulador de Titulizaciones conforme al CRR (SEC-IRBA y SEC-SA)
# ---------------------------------------------------------------
# Este script calcula K_IRB, K_SSA, y RWA bajo el marco regulatorio europeo.
# Referencias: Artículo 259 del Reglamento CRR (EU) No 575/2013
# Autor: joseaalonso1

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
import ipywidgets as widgets
from IPython.display import display, Markdown

# -----------------------------
# 1. Cálculo de K_IRB (Art. 259.2)
# -----------------------------
def calcular_kirb(rwa_pool, ead_pool):
    """Calcula K_IRB como RWA / EAD * 8%"""
    if ead_pool <= 0:
        return 0
    return (rwa_pool / ead_pool) * 0.08

# -----------------------------
# 2. Cálculo de K_SSA (Supervisory Formula, Art. 259.3)
# -----------------------------
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

# -----------------------------
# 3. Cálculo de Risk Weight (RW) según tramo (Art. 259.3)
# -----------------------------
def calcular_rw(K, KSSA, A, D):
    if K <= A:
        tipo = 1
        rw = 12.5 * KSSA
    elif K >= D:
        tipo = 3
        rw = 12.5  # 1250%
    else:
        tipo = 2
        rw = 12.5 * KSSA * (D - K) / (D - A) + 12.5 * (K - A) / (D - A)
    return tipo, max(rw, 15.0)  # RW mínimo del 15%

# -----------------------------
# 4. Interfaz básica para simulación
# -----------------------------
kirb_input = widgets.FloatText(value=0.10, description="K_IRB:")
kssa_input = widgets.FloatText(value=0.25, description="K_SSA:")
a_input = widgets.FloatText(value=0.05, description="A:")
d_input = widgets.FloatText(value=0.30, description="D:")
rwa_input = widgets.FloatText(value=100, description="RWA pool:")
ead_input = widgets.FloatText(value=100, description="EAD pool:")
p_input = widgets.FloatText(value=0.5, description="p:")

# Botón y salida
boton = widgets.Button(description="Calcular todo")

# Acción del botón
def ejecutar(b):
    kirb = calcular_kirb(rwa_input.value, ead_input.value)
    kssa = calcular_kssa(kirb_input.value, a_input.value, d_input.value, p_input.value)
    tipo, rw = calcular_rw(kirb_input.value, kssa_input.value, a_input.value, d_input.value)
    display(Markdown(f"""
    ### Resultados:
    - K_IRB calculado: **{kirb:.4f}**
    - K_SSA calculado: **{kssa:.4f}**
    - Tipo de tramo: **{tipo}**
    - RW final aplicado: **{rw:.2f}%**
    """))

boton.on_click(ejecutar)

# Mostrar interfaz
ui = widgets.VBox([
    widgets.HBox([rwa_input, ead_input]),
    widgets.HBox([kirb_input, kssa_input]),
    widgets.HBox([a_input, d_input, p_input]),
    boton
])
display(Markdown("## Simulador completo de titulizaciones (CRR Art. 259)"), ui)
