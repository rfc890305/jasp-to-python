"""Análise de capacidade de processo (Cp, Cpk, Pp, Ppk, PPM).

Referência JASP: jaspQualityControl/R/processCapabilityStudies.R
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from .constants import constants_for


def _within_sigma(x: np.ndarray, subgroup_size: int) -> float:
    """Desvio padrão de curto prazo (dentro dos subgrupos).

    n = 1: amplitude móvel média / d2 (n=2), como no Minitab e no JASP.
    n > 1: amplitude média dos subgrupos / d2(n).
    """
    if subgroup_size == 1:
        mr = np.abs(np.diff(x))
        return float(np.mean(mr) / constants_for(2)[0])
    k = x.size // subgroup_size
    groups = x[: k * subgroup_size].reshape(k, subgroup_size)
    ranges = groups.max(axis=1) - groups.min(axis=1)
    return float(np.mean(ranges) / constants_for(subgroup_size)[0])


def _ppm(mean: float, sigma: float, lsl, usl) -> dict:
    below = stats.norm.cdf((lsl - mean) / sigma) * 1e6 if lsl is not None else 0.0
    above = stats.norm.sf((usl - mean) / sigma) * 1e6 if usl is not None else 0.0
    return {"ppm_below_lsl": float(below), "ppm_above_usl": float(above), "ppm_total": float(below + above)}


def _indices(mean: float, sigma: float, lsl, usl) -> dict:
    upper = (usl - mean) / (3 * sigma) if usl is not None else None
    lower = (mean - lsl) / (3 * sigma) if lsl is not None else None
    both = (usl - lsl) / (6 * sigma) if lsl is not None and usl is not None else None
    sides = [v for v in (upper, lower) if v is not None]
    return {"two_sided": both, "upper": upper, "lower": lower, "k": min(sides)}


def capability_analysis(values, lsl: float | None = None, usl: float | None = None,
                        target: float | None = None, subgroup_size: int = 1) -> dict:
    """Capacidade de um processo sob normalidade.

    Retorna índices potenciais (Cp, Cpk, a partir do sigma *within*) e de
    desempenho (Pp, Ppk, a partir do sigma *overall*), PPM esperado e o
    nível sigma de curto prazo (Z.bench + 1,5).
    """
    if lsl is None and usl is None:
        raise ValueError("Informe ao menos um limite de especificação (LSL ou USL).")
    if lsl is not None and usl is not None and lsl >= usl:
        raise ValueError("LSL deve ser menor que USL.")

    x = pd.Series(values, dtype=float).dropna().to_numpy()
    if x.size < 2:
        raise ValueError("São necessárias ao menos 2 observações.")

    mean = float(np.mean(x))
    sigma_overall = float(np.std(x, ddof=1))
    sigma_within = _within_sigma(x, subgroup_size)

    within = _indices(mean, sigma_within, lsl, usl)
    overall = _indices(mean, sigma_overall, lsl, usl)
    ppm_within = _ppm(mean, sigma_within, lsl, usl)
    ppm_overall = _ppm(mean, sigma_overall, lsl, usl)

    result = {
        "n": int(x.size),
        "mean": mean,
        "sigma_within": sigma_within,
        "sigma_overall": sigma_overall,
        "lsl": lsl,
        "usl": usl,
        "target": target,
        "Cp": within["two_sided"],
        "CPU": within["upper"],
        "CPL": within["lower"],
        "Cpk": within["k"],
        "Pp": overall["two_sided"],
        "PPU": overall["upper"],
        "PPL": overall["lower"],
        "Ppk": overall["k"],
        "ppm_within": ppm_within,
        "ppm_overall": ppm_overall,
    }

    # Nível sigma (convenção Six Sigma com deslocamento de 1,5 sigma)
    p_total = ppm_overall["ppm_total"] / 1e6
    z_bench = float(stats.norm.isf(p_total)) if p_total > 0 else float("inf")
    result["z_bench_overall"] = z_bench
    result["sigma_level"] = z_bench + 1.5

    if target is not None and lsl is not None and usl is not None:
        # Cpm (Taguchi), usando o sigma overall como o Minitab
        tau = np.sqrt(sigma_overall**2 + (mean - target) ** 2)
        result["Cpm"] = float((usl - lsl) / (6 * tau))

    return result
