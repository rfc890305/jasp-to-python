"""Cartas de controle para variáveis (I-MR e Xbarra-R) e regras de Nelson.

Referências JASP: jaspQualityControl/R/variablesChartsIndividuals.R e
variablesChartsSubgroups.R
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .constants import constants_for


def nelson_rules(values, center: float, sigma: float) -> dict[str, list[int]]:
    """Índices (base 0) dos pontos que violam as regras 1, 2 e 3 de Nelson.

    1: um ponto além de 3 sigmas do centro.
    2: nove pontos consecutivos do mesmo lado da linha central.
    3: seis pontos consecutivos crescentes ou decrescentes.
    """
    x = np.asarray(values, dtype=float)
    rule1 = [int(i) for i in np.where(np.abs(x - center) > 3 * sigma)[0]]

    rule2, run, side = [], 0, 0
    for i, v in enumerate(x):
        s = int(np.sign(v - center))
        run = run + 1 if s != 0 and s == side else (1 if s != 0 else 0)
        side = s
        if run >= 9:
            rule2.append(i)

    rule3, run, direction = [], 1, 0
    for i in range(1, x.size):
        d = int(np.sign(x[i] - x[i - 1]))
        run = run + 1 if d != 0 and d == direction else (2 if d != 0 else 1)
        direction = d
        if run >= 6:
            rule3.append(i)

    return {"rule1": rule1, "rule2": rule2, "rule3": rule3}


def imr_chart(values) -> dict:
    """Carta de valores individuais e amplitude móvel (I-MR)."""
    x = pd.Series(values, dtype=float).dropna().to_numpy()
    if x.size < 2:
        raise ValueError("São necessárias ao menos 2 observações.")
    d2, _, d3, d4 = constants_for(2)

    mr = np.abs(np.diff(x))
    mr_bar = float(np.mean(mr))
    center = float(np.mean(x))
    sigma = mr_bar / d2

    individuals = pd.DataFrame({
        "value": x,
        "center": center,
        "ucl": center + 3 * sigma,
        "lcl": center - 3 * sigma,
    })
    moving_range = pd.DataFrame({
        "value": np.concatenate([[np.nan], mr]),
        "center": mr_bar,
        "ucl": d4 * mr_bar,
        "lcl": d3 * mr_bar,
    })
    return {
        "sigma": sigma,
        "individuals": individuals,
        "moving_range": moving_range,
        "violations": nelson_rules(x, center, sigma),
    }


def xbar_r_chart(values, subgroup_size: int) -> dict:
    """Carta Xbarra-R para subgrupos consecutivos de tamanho fixo."""
    x = pd.Series(values, dtype=float).dropna().to_numpy()
    k = x.size // subgroup_size
    if k < 2:
        raise ValueError("São necessários ao menos 2 subgrupos completos.")
    d2, a2, d3, d4 = constants_for(subgroup_size)

    groups = x[: k * subgroup_size].reshape(k, subgroup_size)
    means = groups.mean(axis=1)
    ranges = groups.max(axis=1) - groups.min(axis=1)
    grand_mean = float(means.mean())
    r_bar = float(ranges.mean())

    xbar = pd.DataFrame({
        "value": means,
        "center": grand_mean,
        "ucl": grand_mean + a2 * r_bar,
        "lcl": grand_mean - a2 * r_bar,
    })
    r = pd.DataFrame({
        "value": ranges,
        "center": r_bar,
        "ucl": d4 * r_bar,
        "lcl": d3 * r_bar,
    })
    sigma_xbar = (a2 * r_bar) / 3
    return {
        "sigma": r_bar / d2,
        "xbar": xbar,
        "range": r,
        "violations": nelson_rules(means, grand_mean, sigma_xbar),
    }
