"""Estatística descritiva (equivalente ao módulo jaspDescriptives)."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def describe(values) -> dict:
    """Resumo descritivo de uma variável numérica, ignorando valores ausentes."""
    x = pd.Series(values, dtype=float).dropna().to_numpy()
    n = x.size
    if n == 0:
        raise ValueError("A variável não possui valores numéricos.")
    q1, median, q3 = np.percentile(x, [25, 50, 75])
    std = float(np.std(x, ddof=1)) if n > 1 else float("nan")
    return {
        "n": int(n),
        "mean": float(np.mean(x)),
        "std": std,
        "se_mean": std / np.sqrt(n) if n > 1 else float("nan"),
        "min": float(np.min(x)),
        "q1": float(q1),
        "median": float(median),
        "q3": float(q3),
        "max": float(np.max(x)),
        "skewness": float(stats.skew(x, bias=False)) if n > 2 else float("nan"),
        "kurtosis": float(stats.kurtosis(x, bias=False)) if n > 3 else float("nan"),
    }
