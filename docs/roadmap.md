# Roadmap da migração

Repositórios de origem: <https://github.com/jasp-stats> (um repositório R por módulo; a lógica
de cálculo fica em `R/`). Guia de desenvolvimento de módulos:
<https://johnnydoorn.github.io/module-development-guide/>.

Status: ✅ migrado · 🟡 parcial · ⬜ não iniciado

## Fase 1: Controle de qualidade (jaspQualityControl)

| Análise | Python | Status |
|---|---|---|
| Capacidade de processo (normal) | `backend/quality/capability.py` | 🟡 sem gráficos e sem distribuições não normais |
| Capacidade (não normal: Weibull, lognormal, Box-Cox) | | ⬜ |
| Carta I-MR | `backend/quality/control_charts.py` | ✅ |
| Carta Xbarra-R | `backend/quality/control_charts.py` | ✅ |
| Carta Xbarra-S | | ⬜ |
| Cartas por atributos (p, np, c, u, Laney) | | ⬜ |
| Cartas ponderadas no tempo (EWMA, CUSUM) | | ⬜ |
| Regras de Nelson / Western Electric (1 a 8) | `nelson_rules` | 🟡 regras 1 a 3 |
| MSA: Gauge R&R (cruzado / aninhado) | | ⬜ |
| MSA: linearidade e viés, estudo tipo 1 | | ⬜ |
| MSA: concordância por atributos | | ⬜ |
| DOE: fatorial, superfície de resposta | | ⬜ |

## Fase 2: Estatística básica

| Módulo JASP | Análises | Status |
|---|---|---|
| jaspDescriptives | descritivas | 🟡 `backend/descriptives.py` |
| jaspTTests | t uma amostra, pareado, independente | ⬜ |
| jaspAnova | ANOVA, ANCOVA, medidas repetidas | ⬜ |
| jaspRegression | linear, logística, correlação | ⬜ |
| jaspFrequencies | qui-quadrado, binomial, multinomial | ⬜ |

## Fase 3: Lacunas em relação ao Minitab

Definidas em [comparacao-minitab.md](comparacao-minitab.md).
