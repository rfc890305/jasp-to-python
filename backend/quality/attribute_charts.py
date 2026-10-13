"""Cartas de controle por atributos: p, np, c, u e as versões de Laney (p', u').

Referência JASP: jaspQualityControl/R/attributesCharts.R (.Pchart, .NPchart,
.Cchart, .Uchart, .LanyP, .LanyU), que usa qcc::qcc para p, np, c e u.

Cada função devolve um ``dict`` com:

- ``chart``: DataFrame com ``value``, ``center``, ``ucl`` e ``lcl`` por subgrupo
  (limites variam por subgrupo quando os tamanhos de amostra variam);
- ``center``: linha central;
- ``violations``: índices (base 0) por regra: ``rule1`` usa os limites de cada
  ponto; ``rule2`` e ``rule3`` são as regras de Nelson da linha central.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .constants import constants_for
from .control_charts import nelson_rules


def _counts(defects, sizes=None) -> tuple[np.ndarray, np.ndarray | None]:
    d = pd.Series(defects, dtype=float).to_numpy()
    n = None if sizes is None else pd.Series(sizes, dtype=float).to_numpy()
    if n is not None and n.size != d.size:
        raise ValueError("Defeitos e tamanhos de amostra precisam ter o mesmo comprimento.")
    keep = ~np.isnan(d) if n is None else ~(np.isnan(d) | np.isnan(n))
    d = d[keep]
    n = None if n is None else n[keep]
    if d.size < 2:
        raise ValueError("São necessários ao menos 2 subgrupos.")
    if np.any(d < 0) or (n is not None and np.any(n <= 0)):
        raise ValueError("Contagens não podem ser negativas e tamanhos devem ser positivos.")
    return d, n


def _result(value, center, half_width, upper_bound=None) -> dict:
    value = np.asarray(value, dtype=float)
    center = np.broadcast_to(np.asarray(center, dtype=float), value.shape)
    ucl = center + half_width
    if upper_bound is not None:
        ucl = np.minimum(ucl, upper_bound)
    lcl = np.maximum(center - half_width, 0.0)
    chart = pd.DataFrame({"value": value, "center": center, "ucl": ucl, "lcl": lcl})
    rule1 = [int(i) for i in np.where((value > ucl) | (value < lcl))[0]]
    # Regras 2 e 3 só dependem da posição em relação à linha central de cada ponto.
    runs = nelson_rules(value - center, 0.0, np.inf)
    return {
        "chart": chart,
        "center": float(center.mean()),
        "violations": {"rule1": rule1, "rule2": runs["rule2"], "rule3": runs["rule3"]},
    }


def p_chart(defectives, sizes) -> dict:
    """Carta p: proporção de defeituosos por subgrupo.

    LC = p̄ = Σd/Σn; LSC/LIC = p̄ ± 3·√(p̄(1−p̄)/nᵢ), truncados em [0, 1].
    """
    d, n = _counts(defectives, sizes)
    if np.any(d > n):
        raise ValueError("O número de defeituosos não pode passar do tamanho da amostra.")
    p_bar = d.sum() / n.sum()
    return _result(d / n, p_bar, 3 * np.sqrt(p_bar * (1 - p_bar) / n), upper_bound=1.0)


def np_chart(defectives, sizes) -> dict:
    """Carta np: número de defeituosos por subgrupo.

    LC = nᵢ·p̄; LSC/LIC = nᵢ·p̄ ± 3·√(nᵢ·p̄(1−p̄)). Com tamanhos iguais os limites são constantes,
    que é o caso de uso recomendado.
    """
    d, n = _counts(defectives, sizes)
    if np.any(d > n):
        raise ValueError("O número de defeituosos não pode passar do tamanho da amostra.")
    p_bar = d.sum() / n.sum()
    return _result(d, n * p_bar, 3 * np.sqrt(n * p_bar * (1 - p_bar)), upper_bound=n)


def c_chart(defects) -> dict:
    """Carta c: número de defeitos por unidade de inspeção de tamanho constante.

    LC = c̄; LSC/LIC = c̄ ± 3·√c̄.
    """
    d, _ = _counts(defects)
    c_bar = d.mean()
    return _result(d, c_bar, 3 * np.sqrt(c_bar))


def u_chart(defects, sizes) -> dict:
    """Carta u: defeitos por unidade, com número de unidades inspecionadas variável.

    LC = ū = Σc/Σn; LSC/LIC = ū ± 3·√(ū/nᵢ).
    """
    d, n = _counts(defects, sizes)
    u_bar = d.sum() / n.sum()
    return _result(d / n, u_bar, 3 * np.sqrt(u_bar / n))


def _laney_sigma_z(ratio, center, sigma_i) -> float:
    z = (ratio - center) / sigma_i
    return float(np.mean(np.abs(np.diff(z))) / constants_for(2)[0])


def laney_p_chart(defectives, sizes) -> dict:
    """Carta p' de Laney: carta p corrigida para sobredispersão (amostras grandes).

    σz = MR̄(zᵢ)/1,128 com zᵢ = (pᵢ − p̄)/σᵢ; LSC/LIC = p̄ ± 3·σᵢ·σz.
    Diferença do JASP: aqui zᵢ usa o σᵢ de cada subgrupo (como no Minitab e no artigo de Laney);
    o JASP usa o tamanho do primeiro subgrupo para todos. Com tamanhos iguais os resultados coincidem.
    """
    d, n = _counts(defectives, sizes)
    p_bar = d.sum() / n.sum()
    sigma_i = np.sqrt(p_bar * (1 - p_bar) / n)
    sigma_z = _laney_sigma_z(d / n, p_bar, sigma_i)
    res = _result(d / n, p_bar, 3 * sigma_i * sigma_z, upper_bound=1.0)
    res["sigma_z"] = sigma_z
    return res


def laney_u_chart(defects, sizes) -> dict:
    """Carta u' de Laney: carta u corrigida para sobredispersão.

    Mesma construção da p' com σᵢ = √(ū/nᵢ).
    """
    d, n = _counts(defects, sizes)
    u_bar = d.sum() / n.sum()
    sigma_i = np.sqrt(u_bar / n)
    sigma_z = _laney_sigma_z(d / n, u_bar, sigma_i)
    res = _result(d / n, u_bar, 3 * sigma_i * sigma_z)
    res["sigma_z"] = sigma_z
    return res
