from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from backend.quality import c_chart, laney_p_chart, laney_u_chart, np_chart, p_chart, u_chart

DATA = Path(__file__).parent / "data" / "jasp"


def test_p_chart_limites_variaveis():
    d = pd.read_csv(DATA / "SPC_P.csv")
    r = p_chart(d["D"], d["Size"])
    p_bar = d["D"].sum() / d["Size"].sum()
    chart = r["chart"]
    assert r["center"] == pytest.approx(p_bar)
    assert chart["value"].iloc[0] == pytest.approx(21 / 150)
    assert chart["ucl"].iloc[0] == pytest.approx(p_bar + 3 * np.sqrt(p_bar * (1 - p_bar) / 150))
    assert chart["lcl"].iloc[3] == pytest.approx(p_bar - 3 * np.sqrt(p_bar * (1 - p_bar) / 226))
    assert r["violations"]["rule1"] == []  # processo estável, como no exemplo do JASP


def test_p_chart_rejeita_defeituosos_acima_de_n():
    with pytest.raises(ValueError):
        p_chart([5, 60], [50, 50])


def test_np_chart_tamanho_constante():
    r = np_chart([2, 4, 3, 1, 5], [50] * 5)
    p_bar = 15 / 250
    chart = r["chart"]
    assert chart["center"].iloc[0] == pytest.approx(50 * p_bar)
    assert chart["ucl"].iloc[0] == pytest.approx(3 + 3 * np.sqrt(50 * p_bar * (1 - p_bar)))
    assert chart["lcl"].iloc[0] == 0


def test_c_chart():
    r = c_chart([4, 6, 5, 3, 7, 5, 20])
    c_bar = 50 / 7
    assert r["center"] == pytest.approx(c_bar)
    assert r["chart"]["ucl"].iloc[0] == pytest.approx(c_bar + 3 * np.sqrt(c_bar))
    assert r["violations"]["rule1"] == [6]


def test_u_chart():
    r = u_chart([10, 12, 8], [5, 6, 4])
    assert r["center"] == pytest.approx(2.0)
    assert list(r["chart"]["value"]) == pytest.approx([2, 2, 2])
    assert r["chart"]["ucl"].iloc[2] == pytest.approx(2 + 3 * np.sqrt(2 / 4))


def test_laney_com_tamanhos_iguais_igual_ao_jasp():
    # Com n constante, z_i = (p_i − p̄)/σ e σz = MR̄(z)/1,128, como em .LanyP do JASP.
    d, n = np.array([20, 35, 28, 40, 22, 31]), np.full(6, 1000)
    r = laney_p_chart(d, n)
    p = d / n
    p_bar = d.sum() / n.sum()
    sigma = np.sqrt(p_bar * (1 - p_bar) / 1000)
    sigma_z = np.mean(np.abs(np.diff((p - p_bar) / sigma))) / 1.128
    assert r["sigma_z"] == pytest.approx(sigma_z)
    assert r["chart"]["ucl"].iloc[0] == pytest.approx(p_bar + 3 * sigma * sigma_z)
    assert laney_u_chart(d, n)["sigma_z"] > 0


def test_regra_2_nove_acima_da_linha_central():
    r = c_chart([1] * 4 + [6] * 9)
    assert r["violations"]["rule2"] == [12]
