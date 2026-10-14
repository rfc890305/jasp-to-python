"""Gera data/teste_cartas_controle.csv: 30 lotes com causas especiais plantadas.

Uma linha por lote (subgrupo). Colunas:

- Diametro_mm: uma medida por lote, para a carta I-MR (aba Variáveis).
- Sub1..Sub5: cinco medidas por lote, para a carta Xbarra-R (n = 5).
- Inspecionados, Defeituosos, Defeitos: amostras de ~150 a 250 peças, para p, np, c e u.
- Inspecionados_grande, Defeituosos_grande, Defeitos_grande: amostras de ~8.000 a 12.000
  peças com variação extra entre lotes (sobredispersão), para comparar p x p' e u x u' de Laney.

Execução: ``python scripts/gerar_dados_teste_cartas.py`` (semente fixa, resultado reprodutível).
"""

from pathlib import Path

import numpy as np
import pandas as pd

LOTES = 30
rng = np.random.default_rng(2026)
lote = np.arange(1, LOTES + 1)

# Variáveis: alvo 10,00 mm, σ = 0,02 mm.
diametro = 10.0 + rng.normal(0, 0.02, LOTES)
diametro[7] = 10.09                                    # lote 8: ponto além de 3σ (regra 1)
diametro[12:21] = 10.03 + rng.normal(0, 0.008, 9)       # lotes 13-21: 9 acima da média (regra 2)
diametro[23:29] = np.linspace(9.97, 10.04, 6)           # lotes 24-29: 6 em alta (regra 3)

subgrupos = 10.0 + rng.normal(0, 0.02, (LOTES, 5))
subgrupos[9] += 0.05                                    # lote 10: média deslocada (regra 1 no Xbarra)
subgrupos[17] = 10.0 + np.array([-0.07, 0.0, 0.01, 0.06, -0.01])  # lote 18: amplitude alta (carta R)

# Atributos com amostras comuns: p ≈ 5 %, u ≈ 0,06 defeito/peça.
insp = rng.integers(150, 251, LOTES)
defeituosos = rng.binomial(insp, 0.05)
defeituosos[11] = int(round(insp[11] * 0.15))          # lote 12: pico de defeituosos
defeitos = rng.poisson(0.06 * insp)
defeitos[19] = int(round(insp[19] * 0.18))             # lote 20: pico de defeitos

# Atributos com amostras grandes e sobredispersão (taxa real varia de lote para lote).
insp_g = rng.integers(8000, 12001, LOTES)
p_lote = np.clip(rng.normal(0.03, 0.004, LOTES), 0.005, None)
defeituosos_g = rng.binomial(insp_g, p_lote)
defeituosos_g[4] = int(round(insp_g[4] * 0.05))         # lote 5: causa especial real
u_lote = np.clip(rng.normal(0.04, 0.005, LOTES), 0.005, None)
defeitos_g = rng.poisson(u_lote * insp_g)
defeitos_g[26] = int(round(insp_g[26] * 0.065))         # lote 27: causa especial real

df = pd.DataFrame({
    "Lote": lote,
    "Diametro_mm": diametro.round(4),
    **{f"Sub{j + 1}": subgrupos[:, j].round(4) for j in range(5)},
    "Inspecionados": insp,
    "Defeituosos": defeituosos,
    "Defeitos": defeitos,
    "Inspecionados_grande": insp_g,
    "Defeituosos_grande": defeituosos_g,
    "Defeitos_grande": defeitos_g,
})

out = Path(__file__).resolve().parent.parent / "data" / "teste_cartas_controle.csv"
df.to_csv(out, index=False)
print(f"{out} ({len(df)} linhas)")
