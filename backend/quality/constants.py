"""Constantes de cartas de controle por tamanho de subgrupo n.

Fonte: tabelas padrão de CEP (Montgomery, Introduction to Statistical
Quality Control, Apêndice VI), as mesmas usadas pelo JASP e pelo Minitab.
"""

# n: (d2, A2, D3, D4)
CONTROL_CHART_CONSTANTS = {
    2: (1.128, 1.880, 0.000, 3.267),
    3: (1.693, 1.023, 0.000, 2.574),
    4: (2.059, 0.729, 0.000, 2.282),
    5: (2.326, 0.577, 0.000, 2.114),
    6: (2.534, 0.483, 0.000, 2.004),
    7: (2.704, 0.419, 0.076, 1.924),
    8: (2.847, 0.373, 0.136, 1.864),
    9: (2.970, 0.337, 0.184, 1.816),
    10: (3.078, 0.308, 0.223, 1.777),
}


def constants_for(n: int) -> tuple[float, float, float, float]:
    try:
        return CONTROL_CHART_CONSTANTS[n]
    except KeyError:
        raise ValueError(f"Tamanho de subgrupo não suportado: {n} (use 2 a 10).") from None
