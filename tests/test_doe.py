"""Valores esperados de jaspQualityControl/tests/testthat/test-doeAnalysis.R (conferidos lá com o Minitab)."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from backend.quality import analyze_design, box_behnken_design, central_composite_design, factorial_design
from backend.quality.doe import lenth_pse

DATA = Path(__file__).parent / "data" / "jasp"


def _read(name):
    return pd.read_csv(DATA / name, encoding="utf-8-sig")


def test_fatorial_completo_ortogonal():
    d = factorial_design(3)
    assert len(d) == 8
    assert list(d["A"]) == [-1, 1, -1, 1, -1, 1, -1, 1]  # ordem padrão de Yates
    assert (d[["A", "B", "C"]].prod(axis=1).sum()) == 0


@pytest.mark.parametrize("k, runs, resolution", [(4, 8, 4), (5, 16, 5), (7, 8, 3), (6, 16, 4)])
def test_fracionado_resolucao(k, runs, resolution):
    d = factorial_design(k, runs)
    assert len(d) == runs
    assert d.attrs["resolution"] == resolution


def test_fracionado_gerador_aplicado():
    d = factorial_design(4, 8)
    assert (d["D"] == d["A"] * d["B"] * d["C"]).all()


def test_pontos_centrais_replicas_e_aleatorizacao():
    d = factorial_design(2, center_points=3, replicates=2, randomize=True, seed=1)
    assert len(d) == 14
    assert (d["CenterPt"] == 0).sum() == 6
    assert list(d["RunOrder"]) == list(range(1, 15))
    assert sorted(d["StdOrder"]) == list(range(1, 15))


def test_ccd_e_box_behnken():
    c = central_composite_design(3)
    assert len(c) == 8 + 6 + 6
    assert c["A"].abs().max() == pytest.approx(8 ** 0.25)
    assert central_composite_design(2, alpha="face")["A"].abs().max() == 1
    b = box_behnken_design(3)
    assert len(b) == 15
    assert ((b[["A", "B", "C"]] != 0).sum(axis=1).isin([0, 2])).all()


def test_fatorial_2_fatores_saturado():
    r = analyze_design(_read("2level2facFull.csv"), "Result", ["A", "B"])
    c = r["coefficients"]
    assert c.loc["Intercepto", "coef"] == pytest.approx(99.3133959225)
    assert c.loc["A", "effect"] == pytest.approx(7.87462465500001)
    assert c.loc["AB", "coef"] == pytest.approx(-1.7533264275)
    assert r["summary"]["R2"] == pytest.approx(1)
    assert r["pareto"]["method"] == "Lenth"


def test_fatorial_5_fatores_com_interacoes():
    r = analyze_design(_read("2level5facFull.csv"), "Result", list("ABCDE"))
    c, a = r["coefficients"], r["anova"]
    assert c.loc["A", "coef"] == pytest.approx(2.25096480031251)
    assert c.loc["A", "se"] == pytest.approx(1.18642646950104)
    assert c.loc["E", "p"] == pytest.approx(0.00671125493403696)
    assert c.loc["AB", "effect"] == pytest.approx(2.90261955312499)
    assert a.loc["Modelo", "ss"] == pytest.approx(1778.13332839816)
    assert a.loc["Modelo", "p"] == pytest.approx(0.0318832484215919)
    assert a.loc["CE", "f"] == pytest.approx(4.67486806299832)
    assert a.loc["Erro", "ms"] == pytest.approx(45.0434485610464)
    assert a.loc["Total", "ss"] == pytest.approx(2498.82850537491)
    assert r["pareto"]["method"] == "t"
    assert r["pareto"]["effects"]["term"].iloc[0] == "E"


def test_superficie_de_resposta_ccd():
    r = analyze_design(_read("RSM3contCCD.csv"), "Result", ["A", "B", "C"], model="quadratic", coding="none")
    c, a = r["coefficients"], r["anova"]
    assert c.loc["Intercepto", "coef"] == pytest.approx(101.126534122288)
    assert c.loc["B^2", "coef"] == pytest.approx(-2.32172444992377)
    assert c.loc["B^2", "se"] == pytest.approx(2.04721118835923)
    assert c.loc["BC", "p"] == pytest.approx(0.386194705961586)
    assert a.loc["B", "ss"] == pytest.approx(110.228628924466)
    assert a.loc["Erro", "ss"] == pytest.approx(553.494647542538)
    assert r["summary"]["R2"] == pytest.approx(0.356816916827087)
    assert r["summary"]["S"] == pytest.approx(7.43972208850934)
    # O JASP soma as SQ tipo III na linha Total (854,24); aqui o Total é a SQ total real dos dados.
    y = r["fitted"] + r["residuals"]
    assert a.loc["Total", "ss"] == pytest.approx(((y - y.mean()) ** 2).sum())
    assert r["stationary_point"]["nature"] == "sela"


def test_ponto_estacionario_maximo():
    d = central_composite_design(2, center_points=3)
    d["y"] = 50 - (d["A"] - 0.3) ** 2 - 2 * (d["B"] + 0.2) ** 2
    r = analyze_design(d, "y", ["A", "B"], model="quadratic", coding="none")
    sp = r["stationary_point"]
    assert sp["nature"] == "máximo"
    assert sp["coded"]["A"] == pytest.approx(0.3)
    assert sp["coded"]["B"] == pytest.approx(-0.2)
    assert sp["response"] == pytest.approx(50)


def test_codificacao_manual_ccd():
    d = central_composite_design(2, center_points=3)
    d["temp"] = 100 + 10 * d["A"]
    d["y"] = 3 * d["A"] + 1
    r = analyze_design(d, "y", ["temp"], model="linear", coding={"temp": (90, 110)})
    assert r["coefficients"].loc["temp", "coef"] == pytest.approx(3)


def test_lenth_pse():
    assert lenth_pse([10, -1, 1, 2, -2]) == pytest.approx(1.5 * 1.5)


def test_modelo_confundido():
    d = factorial_design(4, 8)
    d["y"] = np.arange(8.0)
    with pytest.raises(ValueError):
        analyze_design(d, "y", list("ABCD"), max_order=2)
