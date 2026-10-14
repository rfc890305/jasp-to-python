"""Análise do sistema de medição (MSA): Gage R&R cruzado pelo método ANOVA.

Referência JASP: jaspQualityControl/R/msaGaugeRR.R (.gaugeANOVA, .ssPart,
.ssRepWithInteraction, .dfGaugeCrossed, .gaugeCrossedVarComps,
.gaugeCrossedVarCompsSingleOP, .gaugeNumberDistinctCategories).

Modelo de efeitos aleatórios, como o padrão do JASP e do Minitab: a interação
peça × operador é testada contra a repetibilidade e, se p ≥ ``alpha_interaction``,
é removida e incorporada ao erro (ANOVA sem interação).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def _anova_table(rows) -> pd.DataFrame:
    table = pd.DataFrame(rows, columns=["source", "df", "ss", "ms", "f", "p"])
    return table.set_index("source")


def _balanced(data: pd.DataFrame, part: str, operator: str) -> int:
    counts = data.groupby([part, operator], observed=True).size()
    n_parts, n_ops = data[part].nunique(), data[operator].nunique()
    if counts.size != n_parts * n_ops:
        raise ValueError("Estudo não cruzado: todo operador precisa medir todas as peças.")
    if counts.nunique() != 1 or counts.iloc[0] < 2:
        raise ValueError("Estudo desbalanceado: cada peça × operador precisa do mesmo número (≥ 2) de medições.")
    return int(counts.iloc[0])


def gauge_rr_crossed(
    data: pd.DataFrame,
    part: str,
    operator: str | None,
    measurement: str,
    tolerance: float | None = None,
    study_var_multiplier: float = 6.0,
    alpha_interaction: float = 0.05,
) -> dict:
    """Gage R&R cruzado (ANOVA) em formato longo: uma linha por medição.

    ``operator=None`` (ou um só operador) faz o estudo tipo 3, sem reprodutibilidade.

    Retorna:
    - ``anova``: ANOVA de dois fatores com interação (ou de um fator no tipo 3);
    - ``anova_reduced``: ANOVA sem interação, quando ela foi removida (senão ``None``);
    - ``interaction_removed``: se a interação foi incorporada ao erro;
    - ``variance_components``: variância e % de contribuição por fonte;
    - ``gauge_evaluation``: desvio padrão, variação do estudo (σ × multiplicador),
      % da variação do estudo e, com ``tolerance``, % da tolerância;
    - ``ndc``: número de categorias distintas = int(1,41 × σpeça / σmedidor).
    """
    cols = [part, measurement] + ([operator] if operator else [])
    df = data[cols].dropna().copy()
    df[measurement] = df[measurement].astype(float)
    if operator is None:
        operator = "__operador__"
        df[operator] = "único"
    single = df[operator].nunique() == 1

    r = _balanced(df, part, operator)
    p, o = df[part].nunique(), df[operator].nunique()
    y = df[measurement]
    grand = y.mean()

    ss_total = float(((y - grand) ** 2).sum())
    ss_part = float(o * r * ((df.groupby(part, observed=True)[measurement].mean() - grand) ** 2).sum())
    cell_mean = df.groupby([part, operator], observed=True)[measurement].transform("mean")
    ss_rep = float(((y - cell_mean) ** 2).sum())

    df_part, df_rep, df_total = p - 1, p * o * (r - 1), p * o * r - 1
    ms_part, ms_rep = ss_part / df_part, ss_rep / df_rep

    if single:
        f_part = ms_part / ms_rep
        anova = _anova_table([
            (part, df_part, ss_part, ms_part, f_part, stats.f.sf(f_part, df_part, df_rep)),
            ("Repetibilidade", df_rep, ss_rep, ms_rep, np.nan, np.nan),
            ("Total", df_total, ss_total, np.nan, np.nan, np.nan),
        ])
        var_rep = ms_rep
        var_part = max(0.0, (ms_part - ms_rep) / r)
        components = {
            "R&R total": var_rep,
            "Repetibilidade": var_rep,
            "Peça a peça": var_part,
        }
        anova_reduced, removed = None, False
    else:
        ss_op = float(p * r * ((df.groupby(operator, observed=True)[measurement].mean() - grand) ** 2).sum())
        ss_int = ss_total - ss_part - ss_op - ss_rep
        df_op, df_int = o - 1, (p - 1) * (o - 1)
        ms_op, ms_int = ss_op / df_op, ss_int / df_int
        f_part, f_op, f_int = ms_part / ms_int, ms_op / ms_int, ms_int / ms_rep
        p_int = stats.f.sf(f_int, df_int, df_rep)
        anova = _anova_table([
            (part, df_part, ss_part, ms_part, f_part, stats.f.sf(f_part, df_part, df_int)),
            (operator, df_op, ss_op, ms_op, f_op, stats.f.sf(f_op, df_op, df_int)),
            (f"{part} × {operator}", df_int, ss_int, ms_int, f_int, p_int),
            ("Repetibilidade", df_rep, ss_rep, ms_rep, np.nan, np.nan),
            ("Total", df_total, ss_total, np.nan, np.nan, np.nan),
        ])
        removed = not p_int < alpha_interaction
        if removed:
            ss_err = ss_total - ss_part - ss_op
            df_err = df_total - df_part - df_op
            ms_err = ss_err / df_err
            anova_reduced = _anova_table([
                (part, df_part, ss_part, ms_part, ms_part / ms_err,
                 stats.f.sf(ms_part / ms_err, df_part, df_err)),
                (operator, df_op, ss_op, ms_op, ms_op / ms_err,
                 stats.f.sf(ms_op / ms_err, df_op, df_err)),
                ("Repetibilidade", df_err, ss_err, ms_err, np.nan, np.nan),
                ("Total", df_total, ss_total, np.nan, np.nan, np.nan),
            ])
            var_rep = ms_err
            var_op = max(0.0, (ms_op - ms_err) / (p * r))
            var_int = None
            var_part = max(0.0, (ms_part - ms_err) / (o * r))
        else:
            anova_reduced = None
            var_rep = ms_rep
            var_op = max(0.0, (ms_op - ms_int) / (p * r))
            var_int = max(0.0, (ms_int - ms_rep) / r)
            var_part = max(0.0, (ms_part - ms_int) / (o * r))

        reprod = var_op + (var_int or 0.0)
        components = {
            "R&R total": var_rep + reprod,
            "Repetibilidade": var_rep,
            "Reprodutibilidade": reprod,
            operator: var_op,
        }
        if var_int is not None:
            components[f"{part} × {operator}"] = var_int
        components["Peça a peça"] = var_part

    total_var = components["R&R total"] + components["Peça a peça"]
    components["Variação total"] = total_var

    variance = pd.DataFrame({"variance": pd.Series(components)})
    variance["pct_contribution"] = variance["variance"] / total_var * 100

    evaluation = pd.DataFrame({"sd": np.sqrt(variance["variance"])})
    evaluation["study_var"] = evaluation["sd"] * study_var_multiplier
    evaluation["pct_study_var"] = evaluation["study_var"] / evaluation.loc["Variação total", "study_var"] * 100
    if tolerance:
        evaluation["pct_tolerance"] = evaluation["study_var"] / tolerance * 100

    sd_gauge = evaluation.loc["R&R total", "sd"]
    sd_part = evaluation.loc["Peça a peça", "sd"]
    ndc = max(1, int(1.41 * sd_part / sd_gauge)) if sd_gauge > 0 else None

    return {
        "anova": anova,
        "anova_reduced": anova_reduced,
        "interaction_removed": removed,
        "variance_components": variance,
        "gauge_evaluation": evaluation,
        "ndc": ndc,
    }


def gauge_rr_verdict(pct_study_var: float) -> str:
    """Classificação AIAG da %variação do estudo do R&R total."""
    if pct_study_var < 10:
        return "aceitável"
    if pct_study_var <= 30:
        return "marginal (aceitável conforme aplicação e custo)"
    return "inaceitável"
