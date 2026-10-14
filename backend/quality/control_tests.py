"""Testes para causas especiais (os 8 testes do Minitab, equivalentes às regras de Nelson).

Referência: Minitab, "Testes para causas especiais" das cartas de controle, e
Nelson (1984), "The Shewhart Control Chart — Tests for Special Causes". O JASP
(jaspQualityControl/R/commonQualityControl.R) usa os mesmos testes com outros nomes.

Os testes trabalham com o escore z de cada ponto, z = (x − LC) / σ, em que σ pode variar
por subgrupo (cartas por atributos com tamanhos diferentes). Cada violação é devolvida
como ``(inicio, fim)`` em índices base 0: ``fim`` é o ponto que o Minitab marca e
``inicio`` é o primeiro ponto da sequência que levou à falha.
"""

from __future__ import annotations

import numpy as np

# número: (descrição com {k}, K padrão do Minitab)
TESTS = {
    1: ("1 ponto a mais de {k} desvios-padrão da linha central", 3),
    2: ("{k} pontos seguidos do mesmo lado da linha central", 9),
    3: ("{k} pontos seguidos, todos crescentes ou todos decrescentes", 6),
    4: ("{k} pontos seguidos, alternando para cima e para baixo", 14),
    5: ("{k1} de {k} pontos a mais de 2 desvios-padrão da linha central (mesmo lado)", 3),
    6: ("{k1} de {k} pontos a mais de 1 desvio-padrão da linha central (mesmo lado)", 5),
    7: ("{k} pontos seguidos a menos de 1 desvio-padrão da linha central (qualquer lado)", 15),
    8: ("{k} pontos seguidos a mais de 1 desvio-padrão da linha central (qualquer lado)", 8),
}
ATTRIBUTE_TESTS = (1, 2, 3, 4)  # o Minitab só oferece os testes 1 a 4 nas cartas por atributos


def describe(test: int, k: int | None = None) -> str:
    k = TESTS[test][1] if k is None else k
    return TESTS[test][0].format(k=k, k1=k - 1)


def _runs(flags: np.ndarray, k: int) -> list[tuple[int, int]]:
    """Pontos que fecham k ou mais ``True`` consecutivos."""
    out, run = [], 0
    for i, f in enumerate(flags):
        run = run + 1 if f else 0
        if run >= k:
            out.append((i - k + 1, i))
    return out


def _k_minus_one_of_k(z: np.ndarray, limit: float, k: int) -> list[tuple[int, int]]:
    out = []
    for i in range(k - 1, z.size):
        window = z[i - k + 1: i + 1]
        for side in (1, -1):
            beyond = side * window > limit
            if side * z[i] > limit and beyond.sum() >= k - 1:
                out.append((i - k + 1, i))
                break
    return out


def special_cause_tests(values, center, sigma, tests=(1, 2, 3, 4, 5, 6, 7, 8), k=None) -> dict[int, list[tuple[int, int]]]:
    """Aplica os testes escolhidos; ``k`` troca o K padrão de cada teste ({teste: K})."""
    x = np.asarray(values, dtype=float)
    center = np.broadcast_to(np.asarray(center, dtype=float), x.shape)
    sigma = np.broadcast_to(np.asarray(sigma, dtype=float), x.shape)
    with np.errstate(divide="ignore", invalid="ignore"):
        z = np.where(sigma > 0, (x - center) / sigma, 0.0)
    k = {**{t: d for t, (_, d) in TESTS.items()}, **(k or {})}
    diff = np.sign(np.diff(x))
    result = {}
    for t in tests:
        kt = int(k[t])
        if kt < (1 if t == 1 else 2):
            raise ValueError(f"K do teste {t} é pequeno demais.")
        if t == 1:
            hits = [(i, i) for i in np.where(np.abs(z) > kt)[0]]
        elif t == 2:
            side = np.sign(z)
            hits = sorted(set(_runs(side > 0, kt)) | set(_runs(side < 0, kt)))
        elif t == 3:
            # k pontos = k − 1 variações no mesmo sentido; o índice i da variação aponta para o ponto i + 1
            up, down = _runs(diff > 0, kt - 1), _runs(diff < 0, kt - 1)
            hits = sorted((s, e + 1) for s, e in set(up) | set(down))
        elif t == 4:
            alternating = np.concatenate([[False], (diff[1:] * diff[:-1]) < 0])
            # sequência de k pontos tem k − 2 trocas de sentido seguidas
            hits = [(s - 1, e + 1) for s, e in _runs(alternating, kt - 2)] if kt > 2 else []
        elif t in (5, 6):
            hits = _k_minus_one_of_k(z, 2.0 if t == 5 else 1.0, kt)
        elif t == 7:
            hits = _runs(np.abs(z) < 1, kt)
        else:
            hits = _runs(np.abs(z) > 1, kt)
        result[t] = [(int(s), int(e)) for s, e in hits]
    return result
