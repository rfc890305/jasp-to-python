"""Planejamento de experimentos (DOE): criação e análise de fatoriais e superfícies de resposta.

Referências JASP: jaspQualityControl/R/doeFactorial.R (criação de fatoriais 2^k e 2^(k−p)),
doeResponseSurfaceMethodology.R (CCD e Box-Behnken) e doeAnalysis.R (ajuste por mínimos
quadrados com fatores codificados em −1/+1, efeitos = 2 × coeficiente, gráfico de Pareto
dos efeitos padronizados).

Os geradores padrão das frações seguem a tabela de Montgomery (Design and Analysis of
Experiments, Tabela 8.14), a mesma usada como padrão pelo Minitab.
"""

from __future__ import annotations

import itertools
import string

import numpy as np
import pandas as pd
from scipy import stats

FACTOR_NAMES = string.ascii_uppercase.replace("I", "")  # Minitab pula a letra I

# (fatores, corridas) -> geradores padrão
DEFAULT_GENERATORS = {
    (3, 4): ["C=AB"],
    (4, 8): ["D=ABC"],
    (5, 8): ["D=AB", "E=AC"],
    (5, 16): ["E=ABCD"],
    (6, 8): ["D=AB", "E=AC", "F=BC"],
    (6, 16): ["E=ABC", "F=BCD"],
    (6, 32): ["F=ABCDE"],
    (7, 8): ["D=AB", "E=AC", "F=BC", "G=ABC"],
    (7, 16): ["E=ABC", "F=BCD", "G=ACD"],
    (7, 32): ["F=ABCD", "G=ABDE"],
    (7, 64): ["G=ABCDEF"],
    (8, 16): ["E=BCD", "F=ACD", "G=ABC", "H=ABD"],
    (8, 32): ["F=ABC", "G=ABD", "H=BCDE"],
    (8, 64): ["G=ABCD", "H=ABEF"],
}


# ---------------------------------------------------------------------------
# Criação de planejamentos
# ---------------------------------------------------------------------------

def _finish(design: pd.DataFrame, replicates: int, randomize: bool, seed) -> pd.DataFrame:
    design = pd.concat([design] * replicates, ignore_index=True)
    design.insert(0, "StdOrder", np.arange(1, len(design) + 1))
    order = np.random.default_rng(seed).permutation(len(design)) if randomize else np.arange(len(design))
    design = design.iloc[order].reset_index(drop=True)
    design.insert(1, "RunOrder", np.arange(1, len(design) + 1))
    return design


def _base_matrix(k: int) -> np.ndarray:
    """Matriz 2^k em ordem padrão (Yates): o primeiro fator alterna mais rápido."""
    runs = np.array(list(itertools.product([-1, 1], repeat=k)))
    return runs[:, ::-1]


def factorial_design(
    n_factors: int,
    runs: int | None = None,
    generators: list[str] | None = None,
    center_points: int = 0,
    replicates: int = 1,
    randomize: bool = False,
    seed: int | None = None,
) -> pd.DataFrame:
    """Fatorial de 2 níveis completo (``runs`` = 2^k) ou fracionado 2^(k−p).

    ``generators`` no formato ``["D=ABC", "E=AB"]``; sem eles, usa ``DEFAULT_GENERATORS``.
    Os pontos centrais (todos os fatores em 0) entram uma vez por réplica.
    O resultado traz ``StdOrder``, ``RunOrder``, ``CenterPt`` (1 = vértice, 0 = centro) e os fatores
    codificados em −1/0/+1. ``design.attrs`` guarda geradores, relação de definição e resolução.
    """
    if not 2 <= n_factors <= len(FACTOR_NAMES):
        raise ValueError("Use de 2 a 25 fatores.")
    names = list(FACTOR_NAMES[:n_factors])
    runs = runs or 2 ** n_factors
    if generators is None and runs < 2 ** n_factors:
        try:
            generators = DEFAULT_GENERATORS[(n_factors, runs)]
        except KeyError:
            raise ValueError(
                f"Sem geradores padrão para {n_factors} fatores em {runs} corridas; informe `generators`."
            ) from None
    generators = generators or []
    n_base = n_factors - len(generators)
    if 2 ** n_base != runs:
        raise ValueError(f"{len(generators)} geradores com {n_factors} fatores dão {2 ** n_base} corridas, não {runs}.")

    base = _base_matrix(n_base)
    columns = {name: base[:, i] for i, name in enumerate(names[:n_base])}
    words = []
    for gen in generators:
        lhs, rhs = (s.strip().upper() for s in gen.split("="))
        if lhs not in names[n_base:] or any(c not in names[:n_base] for c in rhs):
            raise ValueError(f"Gerador inválido: {gen}")
        columns[lhs] = np.prod([columns[c] for c in rhs], axis=0)
        words.append(frozenset(lhs + rhs))

    design = pd.DataFrame({"CenterPt": 1, **{n: columns[n] for n in names}})
    if center_points:
        center = pd.DataFrame({"CenterPt": [0] * center_points, **{n: 0 for n in names}})
        design = pd.concat([design, center], ignore_index=True)

    relation = _defining_relation(words)
    design = _finish(design, replicates, randomize, seed)
    design.attrs.update(
        generators=generators,
        defining_relation=["I"] + ["".join(sorted(w)) for w in relation],
        resolution=min((len(w) for w in relation), default=None),
    )
    return design


def _defining_relation(words: list[frozenset]) -> list[frozenset]:
    """Todos os produtos dos geradores (letras repetidas se cancelam)."""
    relation = set()
    for r in range(1, len(words) + 1):
        for combo in itertools.combinations(words, r):
            w = frozenset()
            for g in combo:
                w = w.symmetric_difference(g)
            relation.add(w)
    return sorted(relation, key=lambda w: (len(w), sorted(w)))


def central_composite_design(
    n_factors: int,
    alpha: str | float = "rotatable",
    center_points: int | None = None,
    replicates: int = 1,
    randomize: bool = False,
    seed: int | None = None,
) -> pd.DataFrame:
    """Planejamento composto central (CCD) com fatorial completo + pontos axiais + centrais.

    ``alpha``: ``"rotatable"`` (α = (2^k)^¼), ``"face"`` (α = 1, face centrada) ou um número.
    ``center_points`` padrão: 6 para k = 2–3 e 7 para k = 4–5, como no Minitab (sem blocos).
    ``PtType``: 1 = vértice, −1 = axial, 0 = centro (convenção do Minitab).
    """
    if not 2 <= n_factors <= 6:
        raise ValueError("Use de 2 a 6 fatores.")
    names = list(FACTOR_NAMES[:n_factors])
    a = {"rotatable": (2 ** n_factors) ** 0.25, "face": 1.0}.get(alpha, alpha)
    if isinstance(a, str):
        raise ValueError("alpha deve ser 'rotatable', 'face' ou um número.")
    if center_points is None:
        center_points = 6 if n_factors <= 3 else 7

    cube = _base_matrix(n_factors).astype(float)
    axial = np.zeros((2 * n_factors, n_factors))
    for i in range(n_factors):
        axial[2 * i, i], axial[2 * i + 1, i] = -a, a
    center = np.zeros((center_points, n_factors))
    points = np.vstack([cube, axial, center])
    pt_type = [1] * len(cube) + [-1] * len(axial) + [0] * center_points
    design = pd.DataFrame(points, columns=names)
    design.insert(0, "PtType", pt_type)
    design = _finish(design, replicates, randomize, seed)
    design.attrs["alpha"] = float(a)
    return design


def box_behnken_design(
    n_factors: int,
    center_points: int | None = None,
    replicates: int = 1,
    randomize: bool = False,
    seed: int | None = None,
) -> pd.DataFrame:
    """Planejamento Box-Behnken para 3 a 5 fatores: cada par de fatores em ±1 com os demais em 0.

    ``center_points`` padrão: 3 (k = 3), 3 (k = 4) e 6 (k = 5), como no Minitab.
    """
    if not 3 <= n_factors <= 5:
        raise ValueError("Box-Behnken disponível para 3 a 5 fatores.")
    names = list(FACTOR_NAMES[:n_factors])
    if center_points is None:
        center_points = {3: 3, 4: 3, 5: 6}[n_factors]
    rows = []
    for i, j in itertools.combinations(range(n_factors), 2):
        for a, b in itertools.product([-1, 1], repeat=2):
            row = [0] * n_factors
            row[i], row[j] = a, b
            rows.append(row)
    rows += [[0] * n_factors] * center_points
    design = pd.DataFrame(rows, columns=names)
    design.insert(0, "PtType", [2] * (len(rows) - center_points) + [0] * center_points)
    return _finish(design, replicates, randomize, seed)


# ---------------------------------------------------------------------------
# Análise
# ---------------------------------------------------------------------------

def code_factor(x, low: float | None = None, high: float | None = None) -> pd.Series:
    """Codifica para −1..+1: ``low`` → −1 e ``high`` → +1.

    Sem ``low``/``high`` usa o mínimo e o máximo observados (``.scaleDOEvariable`` do JASP). Em um CCD
    rotacionável informe os níveis do cubo, senão os pontos axiais viram ±1.
    """
    x = pd.Series(x, dtype=float)
    lo = x.min() if low is None else low
    hi = x.max() if high is None else high
    if hi == lo:
        raise ValueError(f"O fator {x.name} tem um único nível.")
    return 2 * (x - lo) / (hi - lo) - 1


def model_terms(factors: list[str], model: str = "interactions", max_order: int = 2) -> list[tuple[str, ...]]:
    """Termos do modelo.

    ``"linear"``: só efeitos principais; ``"interactions"``: interações até ``max_order``;
    ``"quadratic"``: superfície de resposta completa (lineares, quadrados e interações de 2ª ordem).
    Um termo quadrático é representado por ``(A, A)``.
    """
    terms: list[tuple[str, ...]] = [(f,) for f in factors]
    if model == "linear":
        return terms
    if model == "quadratic":
        return terms + [(f, f) for f in factors] + list(itertools.combinations(factors, 2))
    if model == "interactions":
        for order in range(2, max_order + 1):
            terms += list(itertools.combinations(factors, order))
        return terms
    raise ValueError("model deve ser 'linear', 'interactions' ou 'quadratic'.")


def term_name(term: tuple[str, ...]) -> str:
    if len(term) == 2 and term[0] == term[1]:
        return f"{term[0]}^2"
    return "".join(term) if all(len(t) == 1 for t in term) else "×".join(term)


def lenth_pse(effects) -> float:
    """Pseudo erro padrão de Lenth, usado quando não há graus de liberdade para o erro."""
    abs_eff = np.abs(np.asarray(effects, dtype=float))
    s0 = 1.5 * np.median(abs_eff)
    return float(1.5 * np.median(abs_eff[abs_eff < 2.5 * s0]))


def analyze_design(
    data: pd.DataFrame,
    response: str,
    factors: list[str],
    model: str = "interactions",
    max_order: int = 2,
    terms: list[tuple[str, ...]] | None = None,
    coding: str | dict = "auto",
    alpha: float = 0.05,
) -> dict:
    """Ajusta o modelo do experimento por mínimos quadrados com fatores codificados (−1/+1).

    ``coding``: ``"auto"`` (mínimo/máximo de cada fator), ``"none"`` (dados já codificados) ou
    ``{fator: (baixo, alto)}`` com os níveis que viram −1 e +1.

    Retorna:
    - ``coefficients``: termo, efeito (2 × coef.), coeficiente, EP, t e p;
    - ``anova``: SQ, GL, QM, F e p de cada termo (SQ tipo III = t² × QM do erro), modelo, erro, total;
    - ``summary``: S, R², R² ajustado e R² de predição (PRESS);
    - ``pareto``: efeitos padronizados em ordem decrescente e o valor crítico. Sem GL de erro
      (fatorial sem réplica), usa o pseudo erro padrão de Lenth com GL = m/3, como o Minitab;
    - ``equation``: equação em unidades codificadas;
    - ``stationary_point``: para modelos quadráticos, ponto estacionário codificado e sua natureza.
    """
    df = data[[response] + factors].dropna()
    y = df[response].astype(float).to_numpy()
    if coding == "none":
        coded = df[factors].astype(float)
    elif coding == "auto":
        coded = pd.DataFrame({f: code_factor(df[f]) for f in factors})
    else:
        coded = pd.DataFrame({f: code_factor(df[f], *coding.get(f, (None, None))) for f in factors})
    terms = terms or model_terms(factors, model, max_order)
    names = [term_name(t) for t in terms]

    X = np.column_stack([np.ones(len(y))] + [coded[list(t)].prod(axis=1).to_numpy() for t in terms])
    if np.linalg.matrix_rank(X) < X.shape[1]:
        raise ValueError(
            "Termos confundidos (aliases) no modelo: reduza a ordem das interações ou, para termos "
            "quadráticos, use um planejamento com pontos axiais (CCD ou Box-Behnken)."
        )
    n, k = X.shape
    xtx_inv = np.linalg.inv(X.T @ X)
    beta = xtx_inv @ X.T @ y
    fitted = X @ beta
    resid = y - fitted
    sse = float(resid @ resid)
    sst = float(((y - y.mean()) ** 2).sum())
    df_err = n - k
    mse = sse / df_err if df_err > 0 else np.nan

    se = np.sqrt(np.diag(xtx_inv) * mse) if df_err > 0 else np.full(k, np.nan)
    t = beta / se
    p = 2 * stats.t.sf(np.abs(t), df_err) if df_err > 0 else np.full(k, np.nan)

    effects = 2 * beta
    effects[0] = np.nan
    coefficients = pd.DataFrame(
        {"effect": effects, "coef": beta, "se": se, "t": t, "p": p},
        index=pd.Index(["Intercepto"] + names, name="term"),
    )

    ss_terms = t[1:] ** 2 * mse if df_err > 0 else np.full(k - 1, np.nan)
    ss_model = sst - sse
    df_model = k - 1
    anova = pd.DataFrame(
        {"df": 1, "ss": ss_terms, "ms": ss_terms, "f": t[1:] ** 2, "p": p[1:]},
        index=pd.Index(names, name="source"),
    )
    f_model = (ss_model / df_model) / mse if df_err > 0 else np.nan
    anova.loc["Modelo"] = [df_model, ss_model, ss_model / df_model, f_model,
                          stats.f.sf(f_model, df_model, df_err) if df_err > 0 else np.nan]
    anova.loc["Erro"] = [df_err, sse, mse, np.nan, np.nan]
    anova.loc["Total"] = [n - 1, sst, np.nan, np.nan, np.nan]
    anova["df"] = anova["df"].astype(int)
    anova = anova.loc[["Modelo"] + names + ["Erro", "Total"]]

    leverage = np.einsum("ij,jk,ik->i", X, xtx_inv, X)
    with np.errstate(divide="ignore", invalid="ignore"):
        press = float(np.sum((resid / (1 - leverage)) ** 2)) if np.all(leverage < 1 - 1e-12) else np.nan
    summary = {
        "S": float(np.sqrt(mse)) if df_err > 0 else np.nan,
        "R2": 1 - sse / sst,
        "R2_adj": 1 - mse / (sst / (n - 1)) if df_err > 0 else np.nan,
        "R2_pred": max(0.0, 1 - press / sst) if not np.isnan(press) else np.nan,
        "df_error": df_err,
    }

    if df_err > 0:
        std_effects, crit, method = np.abs(t[1:]), stats.t.ppf(1 - alpha / 2, df_err), "t"
    else:
        pse = lenth_pse(effects[1:])
        std_effects = np.abs(effects[1:]) / pse
        crit, method = stats.t.ppf(1 - alpha / 2, (k - 1) / 3), "Lenth"
    pareto = pd.DataFrame({"term": names, "standardized_effect": std_effects}).sort_values(
        "standardized_effect", ascending=False, ignore_index=True)

    eq = f"{response} = {beta[0]:.4g}" + "".join(
        f" {'−' if b < 0 else '+'} {abs(b):.4g} {nm}" for nm, b in zip(names, beta[1:]))

    result = {
        "coefficients": coefficients,
        "anova": anova,
        "summary": summary,
        "pareto": {"effects": pareto, "critical": float(crit), "method": method},
        "equation": eq,
        "fitted": fitted,
        "residuals": resid,
    }
    if any(len(t) == 2 and t[0] == t[1] for t in terms):
        result["stationary_point"] = _stationary_point(terms, beta, factors)
    return result


def _stationary_point(terms, beta, factors) -> dict | None:
    """x* = −½·B⁻¹·b do modelo quadrático codificado; autovalores de B dão a natureza."""
    idx = {f: i for i, f in enumerate(factors)}
    b = np.zeros(len(factors))
    B = np.zeros((len(factors), len(factors)))
    for term, coef in zip(terms, beta[1:]):
        if len(term) == 1:
            b[idx[term[0]]] = coef
        elif len(term) == 2 and term[0] == term[1]:
            B[idx[term[0]], idx[term[0]]] = coef
        elif len(term) == 2:
            i, j = idx[term[0]], idx[term[1]]
            B[i, j] = B[j, i] = coef / 2
    if abs(np.linalg.det(B)) < 1e-12:
        return None
    x = -0.5 * np.linalg.solve(B, b)
    eig = np.linalg.eigvalsh(B)
    nature = "máximo" if np.all(eig < 0) else "mínimo" if np.all(eig > 0) else "sela"
    return {
        "coded": dict(zip(factors, x)),
        "response": float(beta[0] + 0.5 * x @ b),
        "eigenvalues": eig,
        "nature": nature,
    }
