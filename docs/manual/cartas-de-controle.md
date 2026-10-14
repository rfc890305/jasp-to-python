# Cartas de controle

**Funções:** `backend.quality.imr_chart(values)`, `backend.quality.xbar_r_chart(values, subgroup_size)`
**Origem JASP:** `jaspQualityControl/R/variablesChartsIndividuals.R`, `variablesChartsSubgroups.R`

## Quando usar no Six Sigma

- **Medir:** verificar se o processo está estável antes de calcular capacidade.
- **Controlar:** monitorar o processo melhorado e reagir a causas especiais.

## Qual carta escolher

| Dados | Carta |
|---|---|
| Medições individuais | I-MR |
| Subgrupos de 2 a 10 | Xbarra-R |
| Subgrupos maiores que 10 | Xbarra-S (⬜ a migrar) |
| Contagens (defeituosos ou defeitos) | [Cartas por atributos](cartas-por-atributos.md) |

## Limites

- I-MR: LC = x̄; LSC/LIC = x̄ ± 3·MR̄/1,128. Amplitude móvel: LSC = 3,267·MR̄, LIC = 0.
- Xbarra-R: LSC/LIC = x̿ ± A2·R̄. Amplitude: LSC = D4·R̄, LIC = D3·R̄.

## Regras de Nelson implementadas

1. Um ponto além de 3σ da linha central.
2. Nove pontos consecutivos do mesmo lado da linha central.
3. Seis pontos consecutivos crescentes ou decrescentes.

O resultado traz `violations` com os índices (base 0) dos pontos que dispararam cada regra.
