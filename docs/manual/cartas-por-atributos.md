# Cartas de controle por atributos

**Funções:** `backend.quality.p_chart(defectives, sizes)`, `np_chart(defectives, sizes)`, `c_chart(defects)`,
`u_chart(defects, sizes)`, `laney_p_chart(defectives, sizes)`, `laney_u_chart(defects, sizes)`
**Origem JASP:** `jaspQualityControl/R/attributesCharts.R` (menu *Control Charts for Attributes*)
**Equivalente Minitab:** Estat › Cartas de Controle › Cartas de Atributos (P, NP, C, U, P' e U' de Laney)

## Quando usar no Six Sigma

- **Definir / Medir:** quando o CTQ é passa/não passa (defeituoso) ou uma contagem de defeitos,
  a carta mostra a linha de base da taxa de defeitos e se o processo está estável antes de calcular a
  capacidade por atributos (DPU, DPMO, nível sigma).
- **Controlar:** no plano de controle, acompanha a taxa de defeitos depois da melhoria e dispara a
  reação quando surge uma causa especial.

Atributos carregam menos informação que medições: precisam de amostras maiores e detectam mudanças
mais tarde. Se o CTQ puder ser medido numa escala contínua, prefira as [cartas por variáveis](cartas-de-controle.md).

## Qual carta escolher

| O que se conta | Tamanho da amostra | Carta |
|---|---|---|
| Itens defeituosos (cada item é bom ou ruim) | Variável | **p** (proporção) |
| Itens defeituosos | Constante | **np** (número) ou p |
| Defeitos (um item pode ter vários) | Área de oportunidade constante | **c** |
| Defeitos | Área de oportunidade variável | **u** (defeitos por unidade) |
| Qualquer das acima com amostras muito grandes (milhares) e limites estreitos demais | — | **p' / u' de Laney** |

## Limites (3σ)

| Carta | Linha central | LSC / LIC |
|---|---|---|
| p | p̄ = Σd / Σn | p̄ ± 3·√(p̄(1−p̄)/nᵢ) |
| np | nᵢ·p̄ | nᵢ·p̄ ± 3·√(nᵢ·p̄(1−p̄)) |
| c | c̄ | c̄ ± 3·√c̄ |
| u | ū = Σc / Σn | ū ± 3·√(ū/nᵢ) |
| p' de Laney | p̄ | p̄ ± 3·σᵢ·σz, com σz = MR̄(zᵢ)/1,128 e zᵢ = (pᵢ − p̄)/σᵢ |
| u' de Laney | ū | ū ± 3·σᵢ·σz, com σᵢ = √(ū/nᵢ) |

O LIC negativo é truncado em 0 (e o LSC da carta p em 1). Com tamanhos de amostra diferentes os
limites variam por subgrupo, por isso o gráfico mostra limites em degrau.

**Laney:** com amostras enormes, a variação entre subgrupos supera a prevista pela binomial ou pela
Poisson (sobredispersão) e quase todo ponto parece fora de controle. σz mede esse excesso: σz ≈ 1 indica
que a carta p/u tradicional serve; σz > 1 indica sobredispersão e a carta de Laney é a correta.
Diferença em relação ao JASP: aqui zᵢ usa o σᵢ de cada subgrupo (como o Minitab e o artigo de Laney,
2002); o JASP usa o tamanho do primeiro subgrupo para todos. Com tamanhos iguais os resultados coincidem.

## Saída

Cada função devolve `chart` (DataFrame com `value`, `center`, `ucl`, `lcl`), `center` e `violations`:

- `rule1`: pontos fora dos limites do próprio subgrupo;
- `rule2`: nove pontos seguidos do mesmo lado da linha central;
- `rule3`: seis pontos seguidos subindo ou descendo.

As cartas de Laney também devolvem `sigma_z`.

## Interpretação

1. Investigue cada ponto acima do LSC: o que mudou naquele lote (material, turno, máquina)?
2. Ponto abaixo do LIC numa carta de defeitos é boa notícia **ou** falha de inspeção: confirme o sistema
   de medição (veja [Gage R&R](gage-rr.md) e a análise de concordância por atributos).
3. Só remova pontos com causa especial identificada e corrigida; recalcule os limites depois.
4. Com o processo estável, a linha central é a capacidade atual: p̄ × 10⁶ = PPM defeituoso; ū dá o DPU.

## Exemplo

```python
import pandas as pd
from backend.quality import p_chart, u_chart

df = pd.read_csv("data/exemplo_atributos.csv")
r = p_chart(df["Defeituosos"], df["Inspecionados"])
print(r["center"], r["violations"]["rule1"])   # p̄ ≈ 0,063; lote 18 (índice 17) acima do LSC
u = u_chart(df["Defeitos"], df["Inspecionados"])
```

No app, aba **Atributos (p, np, c, u)**: escolha a carta, a coluna de contagem e a de tamanho da amostra.
