import pytest

from backend.quality import imr_chart, xbar_r_chart
from backend.quality.control_charts import nelson_rules


def test_imr_limites():
    r = imr_chart([1, 2, 3, 4, 5])
    ind, mr = r["individuals"], r["moving_range"]
    assert ind["center"].iloc[0] == pytest.approx(3)
    assert ind["ucl"].iloc[0] == pytest.approx(3 + 3 / 1.128)
    assert mr["center"].iloc[0] == pytest.approx(1)
    assert mr["ucl"].iloc[0] == pytest.approx(3.267)
    assert mr["lcl"].iloc[0] == 0


def test_xbar_r_limites():
    r = xbar_r_chart([1, 2, 3, 2, 3, 4], subgroup_size=3)
    xbar, rng = r["xbar"], r["range"]
    assert list(xbar["value"]) == [2, 3]
    assert xbar["center"].iloc[0] == pytest.approx(2.5)
    assert xbar["ucl"].iloc[0] == pytest.approx(2.5 + 1.023 * 2)
    assert rng["ucl"].iloc[0] == pytest.approx(2.574 * 2)


def test_xbar_r_exige_dois_subgrupos():
    with pytest.raises(ValueError):
        xbar_r_chart([1, 2, 3], subgroup_size=3)


def test_regra_1_ponto_fora():
    v = nelson_rules([0, 0, 10, 0], center=0, sigma=1)
    assert v["rule1"] == [2]


def test_regra_2_nove_do_mesmo_lado():
    v = nelson_rules([1] * 10, center=0, sigma=5)
    assert v["rule2"] == [8, 9]


def test_regra_3_tendencia():
    v = nelson_rules([0, 1, 2, 3, 4, 5, 4], center=2.5, sigma=10)
    assert v["rule3"] == [5]
