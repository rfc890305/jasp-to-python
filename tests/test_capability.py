import math

import numpy as np
import pytest

from backend.quality import capability_analysis


def test_indices_calculados_a_mao():
    # Amplitudes móveis todas iguais a 1 -> sigma_within = 1 / 1,128
    r = capability_analysis([1, 2, 3, 4, 5], lsl=0, usl=6)
    assert r["sigma_within"] == pytest.approx(1 / 1.128)
    assert r["Cp"] == pytest.approx(1.128)
    assert r["Cpk"] == pytest.approx(1.128)
    assert r["sigma_overall"] == pytest.approx(np.std([1, 2, 3, 4, 5], ddof=1))
    assert r["Pp"] == pytest.approx(6 / (6 * r["sigma_overall"]))


def test_processo_descentrado_reduz_cpk():
    r = capability_analysis([1, 2, 3, 4, 5], lsl=0, usl=10)
    assert r["Cpk"] == pytest.approx(r["CPL"])
    assert r["Cpk"] < r["Cp"]


def test_limite_unilateral():
    r = capability_analysis([1, 2, 3, 4, 5], usl=6)
    assert r["Cp"] is None
    assert r["Cpk"] == pytest.approx(r["CPU"])
    assert r["ppm_overall"]["ppm_below_lsl"] == 0.0


def test_processo_seis_sigma_tem_ppm_baixo():
    rng = np.random.default_rng(1)
    x = rng.normal(10, 0.1, 500)
    r = capability_analysis(x, lsl=9.4, usl=10.6)
    assert r["Ppk"] > 1.5
    assert r["ppm_overall"]["ppm_total"] < 50


def test_cpm_com_alvo():
    r = capability_analysis([1, 2, 3, 4, 5], lsl=0, usl=6, target=3)
    tau = r["sigma_overall"]
    assert r["Cpm"] == pytest.approx(6 / (6 * tau))


def test_subgrupos_usa_rbar_d2():
    x = [1, 2, 3, 2, 3, 4]  # dois subgrupos de 3, amplitudes 2 e 2
    r = capability_analysis(x, lsl=0, usl=6, subgroup_size=3)
    assert r["sigma_within"] == pytest.approx(2 / 1.693)


@pytest.mark.parametrize("kwargs", [{}, {"lsl": 5, "usl": 1}])
def test_validacao_de_limites(kwargs):
    with pytest.raises(ValueError):
        capability_analysis([1, 2, 3], **kwargs)


def test_ignora_valores_ausentes():
    r = capability_analysis([1, None, 2, math.nan, 3], lsl=0, usl=4)
    assert r["n"] == 3
