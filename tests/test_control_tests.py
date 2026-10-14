"""Testes para causas especiais (1 a 8 do Minitab)."""

import numpy as np
import pytest

from backend.quality.control_tests import describe, special_cause_tests


def ends(result, test):
    return [e for _, e in result[test]]


def test_test1_uses_k_sigmas():
    x = [0, 0, 3.5, 0, -2.5]
    assert ends(special_cause_tests(x, 0, 1, tests=(1,)), 1) == [2]
    assert ends(special_cause_tests(x, 0, 1, tests=(1,), k={1: 2}), 1) == [2, 4]


def test_test2_nine_on_one_side_marks_run():
    x = [-1] + [0.5] * 10
    res = special_cause_tests(x, 0, 1, tests=(2,))
    assert res[2] == [(1, 9), (2, 10)]


def test_test3_six_increasing():
    x = [5, 1, 2, 3, 4, 5, 6, 0]
    assert special_cause_tests(x, 3, 1, tests=(3,))[3] == [(1, 6)]
    assert special_cause_tests(x, 3, 1, tests=(3,), k={3: 7})[3] == []


def test_test4_alternating():
    x = [0, 1] * 7 + [0]  # 15 pontos alternando
    assert special_cause_tests(x, 0.5, 1, tests=(4,))[4] == [(0, 13), (1, 14)]


def test_tests5_and_6_k_minus_one_of_k_same_side():
    x = [0, 2.5, 0, 2.5, 0, 0]
    assert ends(special_cause_tests(x, 0, 1, tests=(5,)), 5) == [3]
    x = [1.5, 1.5, 0, 1.5, 1.5, 0]
    assert ends(special_cause_tests(x, 0, 1, tests=(6,)), 6) == [4]
    # lados opostos não contam juntos
    assert special_cause_tests([2.5, 0, -2.5], 0, 1, tests=(5,))[5] == []


def test_tests7_and_8():
    assert ends(special_cause_tests([0.1] * 15, 0, 1, tests=(7,)), 7) == [14]
    x = [1.5, -1.5] * 4
    assert ends(special_cause_tests(x, 0, 1, tests=(8,)), 8) == [7]


def test_variable_sigma_per_point():
    # mesmo desvio, sigmas diferentes: só o ponto de sigma pequeno passa de 3σ
    res = special_cause_tests([1, 1], 0, np.array([1.0, 0.25]), tests=(1,))
    assert ends(res, 1) == [1]


def test_describe_and_validation():
    assert describe(5) == "2 de 3 pontos a mais de 2 desvios-padrão da linha central (mesmo lado)"
    assert describe(2, 7).startswith("7 pontos")
    with pytest.raises(ValueError):
        special_cause_tests([1, 2, 3], 0, 1, tests=(2,), k={2: 1})
