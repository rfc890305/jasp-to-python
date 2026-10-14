# Planejamento de experimentos (DOE)

**Funções:**
- Criação: `backend.quality.factorial_design(n_factors, runs=None, generators=None, center_points=0,
  replicates=1, randomize=False, seed=None)`, `central_composite_design(n_factors, alpha="rotatable", ...)`,
  `box_behnken_design(n_factors, ...)`
- Análise: `backend.quality.analyze_design(data, response, factors, model="interactions", max_order=2,
  coding="auto")`

**Origem JASP:** `jaspQualityControl/R/doeFactorial.R`, `doeResponseSurfaceMethodology.R` e `doeAnalysis.R`
**Equivalente Minitab:** Estat › DOE › Fatorial (Criar / Analisar) e Superfície de Resposta (Criar / Analisar)

## Quando usar no Six Sigma

- **Analisar:** confirmar quais Xs suspeitos (do Ishikawa, do FMEA, da regressão em dados históricos)
  realmente afetam o Y. Um fatorial fracionado de triagem testa muitos fatores com poucas corridas.
- **Melhorar:** com os poucos Xs vitais, um fatorial completo estima as interações e, se houver
  curvatura, uma superfície de resposta (CCD ou Box-Behnken) encontra o ajuste ótimo.
- **Controlar:** os níveis ótimos viram parâmetros padronizados do processo, com tolerância operacional.

Sequência típica: triagem (2^(k−p), resolução III ou IV) → fatorial completo ou resolução V nos fatores
vitais, com pontos centrais para testar curvatura → superfície de resposta → corrida de confirmação.

## Criação do planejamento

| Planejamento | Uso | Função |
|---|---|---|
| Fatorial completo 2^k | até 4–5 fatores, todas as interações | `factorial_design(k)` |
| Fracionado 2^(k−p) | triagem de 5 a 8 fatores | `factorial_design(k, runs=16)` |
| Composto central (CCD) | superfície de resposta, 5 níveis por fator | `central_composite_design(k)` |
| Box-Behnken | superfície de resposta sem pontos extremos (3 níveis) | `box_behnken_design(k)` |

- Fatores ficam em unidades codificadas (−1, 0, +1). Converta para unidades reais com
  `real = centro + codificado × meia-amplitude`.
- Os geradores padrão das frações seguem Montgomery (Tabela 8.14), os mesmos do Minitab. O resultado
  traz `design.attrs["resolution"]` e a relação de definição.

| Resolução | O que fica confundido | Uso |
|---|---|---|
| III | efeitos principais com interações de 2 fatores | triagem grosseira |
| IV | interações de 2 fatores entre si | triagem segura dos efeitos principais |
| V | interações de 2 com as de 3 fatores | estima efeitos principais e interações de 2 |

- **Aleatorize** (`randomize=True`) para proteger contra variáveis de ruído que mudam com o tempo;
  a coluna `RunOrder` é a ordem de execução, `StdOrder` a ordem padrão.
- **Pontos centrais** dão graus de liberdade para o erro sem replicar o fatorial todo e permitem
  testar curvatura.
- **CCD:** α rotacionável = (2^k)^¼ (padrão) ou face centrada (`alpha="face"`) quando os níveis axiais
  não podem sair da faixa do cubo.

## Análise

`analyze_design` ajusta por mínimos quadrados com os fatores codificados em −1/+1 (pelo mínimo e
máximo de cada coluna, como o JASP; `coding="none"` se os dados já estão codificados, ou um dicionário
`{fator: (baixo, alto)}`, necessário num CCD em unidades reais para que os pontos axiais não virem ±1).

| Modelo (`model`) | Termos |
|---|---|
| `"linear"` | efeitos principais |
| `"interactions"` | efeitos principais e interações até `max_order` (padrão 2) |
| `"quadratic"` | lineares, quadrados e interações de 2 fatores (superfície de resposta) |

Saídas:

- `coefficients`: efeito (= 2 × coeficiente, a mudança média do Y de −1 para +1), coeficiente,
  erro padrão, t e p;
- `anova`: SQ de cada termo (tipo III), modelo, erro e total;
- `summary`: S, R², R² ajustado e R² de predição (PRESS);
- `pareto`: efeitos padronizados e valor crítico. Sem graus de liberdade para o erro (fatorial sem
  réplica e sem pontos centrais) usa o pseudo erro padrão de Lenth, como o Minitab;
- `equation`: equação em unidades codificadas;
- `stationary_point` (modelo quadrático): ponto estacionário codificado, resposta prevista e natureza
  (máximo, mínimo ou sela, pelos autovalores).

## Interpretação

1. **Pareto:** termos além da linha crítica são significativos (α = 0,05). Respeite a hierarquia:
   se a interação AB é significativa, mantenha A e B no modelo.
2. **Interação significativa:** o efeito de um fator depende do nível do outro; não escolha níveis
   olhando só os efeitos principais.
3. **R² ajustado × R² predito:** diferença grande indica termos demais (sobreajuste); remova os não
   significativos e reajuste.
4. **Resíduos:** use `fitted` e `residuals` para verificar normalidade e variância constante.
5. **Ponto estacionário fora da região (|x| > 1 ou além de α):** o ótimo está fora do experimento;
   faça uma nova rodada na direção de maior subida. Ponto de sela pede análise de cristas.
6. Sempre confirme o ajuste ótimo com corridas de confirmação antes de padronizar.

## Validação

`tests/test_doe.py` reproduz os resultados dos testes do JASP conferidos com o Minitab (fatorial 2²,
fatorial 2⁵ com interações de 2ª ordem e CCD com 3 fatores). Diferença conhecida: no CCD o JASP mostra
como "Total" a soma das SQ tipo III; aqui o Total é a SQ total real dos dados (o R² coincide).

## Exemplo

```python
import pandas as pd
from backend.quality import analyze_design, factorial_design

plano = factorial_design(3, center_points=3, randomize=True, seed=7)   # 11 corridas para executar

df = pd.read_csv("data/exemplo_doe.csv")
r = analyze_design(df, "Rendimento", ["Temperatura", "Tempo", "Pressao"])
print(r["coefficients"].round(3))
print(r["pareto"]["effects"])   # Temperatura, Tempo e Temperatura×Tempo significativos
```

No app, aba **DOE**: gere o planejamento (CSV para download) e analise os resultados.
