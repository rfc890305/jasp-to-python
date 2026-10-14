"""Valores esperados copiados de jaspQualityControl/tests/testthat/test-msaGaugeRR.R."""

from pathlib import Path

import pandas as pd
import pytest

from backend.quality import gauge_rr_crossed
from backend.quality.msa import gauge_rr_verdict

DATA = Path(__file__).parent / "data" / "jasp"


@pytest.fixture(scope="module")
def padrao():
    d = pd.read_csv(DATA / "msaGaugeRRCrossed_long.csv", encoding="utf-8-sig")
    return gauge_rr_crossed(d, "Parts", "Operators", "Dm", tolerance=10)


def test_anova_com_interacao(padrao):
    a = padrao["anova"]
    assert a.loc["Parts", "f"] == pytest.approx(622.789783889979)
    assert a.loc["Operators", "p"] == pytest.approx(0.0152789978971193)
    assert a.loc["Parts × Operators", "p"] == pytest.approx(0.268355463232599)
    assert a.loc["Repetibilidade", "ms"] == pytest.approx(0.127777777777778)
    assert a.loc["Total", "ss"] == pytest.approx(892.722222222222)


def test_interacao_removida(padrao):
    assert padrao["interaction_removed"]
    a = padrao["anova_reduced"]
    assert a.loc["Operators", "f"] == pytest.approx(6.21439915299104)
    assert a.loc["Repetibilidade", "df"] == 78


def test_componentes_de_variancia(padrao):
    v = padrao["variance_components"]["variance"]
    assert v["R&R total"] == pytest.approx(0.157929724596391)
    assert v["Repetibilidade"] == pytest.approx(0.134544159544159)
    assert v["Operators"] == pytest.approx(0.0233855650522318)
    assert v["Peça a peça"] == pytest.approx(10.8561068903661)
    assert v["Variação total"] == pytest.approx(11.0140366149625)


def test_avaliacao_do_medidor(padrao):
    e = padrao["gauge_evaluation"]
    assert e.loc["R&R total", "study_var"] == pytest.approx(2.38442237983753)
    assert e.loc["R&R total", "pct_study_var"] == pytest.approx(11.97, abs=0.005)
    assert e.loc["R&R total", "pct_tolerance"] == pytest.approx(23.84, abs=0.005)
    assert padrao["ndc"] == 11


def test_interacao_mantida():
    d = pd.read_csv(DATA / "msaGaugeRRCrossed_realDataExample1.csv", encoding="utf-8-sig")
    r = gauge_rr_crossed(d, "Part", "Appraiser", "Response", tolerance=10)
    assert not r["interaction_removed"]
    v = r["variance_components"]["variance"]
    assert v["Part × Appraiser"] == pytest.approx(0.0139583333333333)
    assert v["Appraiser"] == 0
    assert v["Variação total"] == pytest.approx(0.305)
    assert r["gauge_evaluation"].loc["R&R total", "pct_study_var"] == pytest.approx(29.45, abs=0.005)


def test_estudo_tipo_3_sem_operador():
    d = pd.read_csv(DATA / "msaGaugeRRCrossed_long.csv", encoding="utf-8-sig")
    r = gauge_rr_crossed(d, "Parts", None, "Dm", tolerance=10)
    v = r["variance_components"]["variance"]
    assert v["Repetibilidade"] == pytest.approx(0.152083333333333)
    assert v["Peça a peça"] == pytest.approx(10.8541580932785)


def test_desbalanceado():
    d = pd.DataFrame({"p": [1, 1, 2, 2, 1], "o": ["a", "b", "a", "b", "a"], "y": [1, 2, 3, 4, 5]})
    with pytest.raises(ValueError):
        gauge_rr_crossed(d, "p", "o", "y")


def test_criterio_aiag():
    assert gauge_rr_verdict(8) == "aceitável"
    assert gauge_rr_verdict(25).startswith("marginal")
    assert gauge_rr_verdict(35) == "inaceitável"
