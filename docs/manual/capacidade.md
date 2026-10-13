# Capacidade de processo

**Função:** `backend.quality.capability_analysis(values, lsl=None, usl=None, target=None, subgroup_size=1)`
**Origem JASP:** `jaspQualityControl/R/processCapabilityStudies.R`

## Quando usar no Six Sigma

- **Medir:** estabelecer a linha de base do processo (Ppk e PPM atuais, nível sigma).
- **Controlar:** comprovar o ganho depois das melhorias e monitorar a capacidade.

Pré-requisitos: processo estável (verifique com a [carta de controle](cartas-de-controle.md))
e dados aproximadamente normais.

## Índices

| Índice | Fórmula | Leitura |
|---|---|---|
| Cp | (USL − LSL) / 6σ_within | Potencial, se o processo estivesse centrado |
| Cpk | min(USL − μ, μ − LSL) / 3σ_within | Potencial considerando a centralização |
| Pp, Ppk | Idem com σ_overall | Desempenho real de longo prazo |
| Cpm | (USL − LSL) / 6√(σ² + (μ − alvo)²) | Penaliza distância do alvo (Taguchi) |

- σ_within: subgrupos de 1 usam amplitude móvel média / d2 (1,128); subgrupos maiores usam R̄ / d2(n).
- σ_overall: desvio padrão amostral (n − 1).
- Nível sigma = Z.bench (a partir do PPM total) + 1,5, pela convenção do deslocamento de 1,5σ.

Referência prática: Cpk ≥ 1,33 é o mínimo usual; Cpk ≥ 1,67 para características críticas;
um processo Six Sigma corresponde a Cp = 2 e Cpk = 1,5 (3,4 PPM).

## Exemplo

```python
import pandas as pd
from backend.quality import capability_analysis

df = pd.read_csv("data/exemplo_diametro.csv")
r = capability_analysis(df["diametro_mm"], lsl=9.85, usl=10.15, target=10.0)
print(r["Cpk"], r["Ppk"], r["ppm_overall"]["ppm_total"], r["sigma_level"])
# Cp 1,386 · Cpk 1,363 · Pp 1,287 · Ppk 1,266 · nível sigma ≈ 5,18
```
