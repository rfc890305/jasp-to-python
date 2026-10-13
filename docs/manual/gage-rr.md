# Análise do sistema de medição: Gage R&R cruzado

**Função:** `backend.quality.gauge_rr_crossed(data, part, operator, measurement, tolerance=None,
study_var_multiplier=6, alpha_interaction=0.05)`
**Origem JASP:** `jaspQualityControl/R/msaGaugeRR.R` (menu *Type 2 and 3 Gauge r&R Study*)
**Equivalente Minitab:** Estat › Ferramentas da Qualidade › Estudo de Medição › R&R do Medidor (Cruzado), método ANOVA

## Quando usar no Six Sigma

- **Medir:** antes de qualquer análise de capacidade ou de causa raiz. Se o sistema de medição
  responde por boa parte da variação, os dados não distinguem peças boas de ruins e todas as fases
  seguintes ficam comprometidas.
- **Controlar:** revalidar o sistema quando muda o instrumento, o método ou os inspetores.

## Como planejar o estudo

- 10 peças que cubram toda a faixa do processo (não só peças boas), 2 ou 3 operadores que usam o
  instrumento no dia a dia, 2 ou 3 repetições por peça e operador.
- Estudo **cruzado**: todos os operadores medem todas as peças, em ordem aleatória e às cegas.
- Dados em formato longo: uma linha por medição com colunas de peça, operador e valor.
- Sem operador (`operator=None`) a função faz o **estudo tipo 3** (medição automática): só repetibilidade.
- Se a peça é destruída no ensaio, o estudo é aninhado (ainda não migrado, veja o [roadmap](../roadmap.md)).

## Cálculo

1. ANOVA de dois fatores com interação (peça, operador, peça × operador, repetibilidade). Peça e
   operador são testados contra a interação (modelo de efeitos aleatórios).
2. Se a interação não é significativa (p ≥ 0,05), ela é removida e somada ao erro, como no JASP e no Minitab.
3. Componentes de variância:
   - Repetibilidade (equipamento, EV): QM do erro;
   - Operador: (QM operador − QM interação) / (p·r);
   - Interação: (QM interação − QM erro) / r;
   - Reprodutibilidade (avaliador, AV) = operador + interação;
   - R&R total = repetibilidade + reprodutibilidade;
   - Peça a peça: (QM peça − QM interação) / (o·r);
   - Variação total = R&R + peça a peça. Componentes negativos viram 0.
4. Variação do estudo = 6·σ de cada fonte; %Var. estudo = relação com a variação total;
   %Tolerância = 6σ / (LSE − LIE).
5. Número de categorias distintas: ndc = int(1,41 × σpeça / σR&R).

## Critérios de aceitação (AIAG MSA)

| %Var. estudo (ou %Tolerância) do R&R | Decisão |
|---|---|
| < 10% | Aceitável |
| 10% a 30% | Marginal: aceitável conforme a importância da aplicação e o custo |
| > 30% | Inaceitável: melhorar o sistema de medição |

Além disso, ndc ≥ 5. Use %Tolerância quando o objetivo é classificar peças (inspeção) e
%Var. estudo quando é controlar ou melhorar o processo. `gauge_rr_verdict()` aplica a tabela.

## Interpretação

- **Repetibilidade alta**: problema do instrumento (resolução, fixação, manutenção, desgaste).
- **Reprodutibilidade alta**: problema de método ou treinamento; compare as médias por operador.
- **Interação significativa**: algum operador mede certas peças de forma diferente (peças difíceis de
  posicionar, leitura de escala em faixas específicas).
- **ndc < 5**: o instrumento não tem resolução para separar as peças; carta de controle e capacidade
  feitas com ele serão enganosas.

## Validação

Os testes (`tests/test_msa.py`) reproduzem os valores dos testes do JASP para os mesmos dados,
inclusive o caso com interação significativa e o estudo tipo 3.

## Exemplo

```python
import pandas as pd
from backend.quality import gauge_rr_crossed

df = pd.read_csv("data/exemplo_gage_rr.csv")
r = gauge_rr_crossed(df, part="Peca", operator="Operador", measurement="Medida", tolerance=0.6)
print(r["gauge_evaluation"].round(2))
print("ndc =", r["ndc"])   # R&R ≈ 14,7% da variação do estudo (marginal), ndc = 9
```

No app, aba **Gage R&R (MSA)**.
