import pytest

from backend.descriptives import describe


def test_describe_basico():
    r = describe([1, 2, 3, 4, 5])
    assert r["n"] == 5
    assert r["mean"] == 3
    assert r["median"] == 3
    assert r["std"] == pytest.approx(1.5811388)


def test_describe_vazio():
    with pytest.raises(ValueError):
        describe([None])
