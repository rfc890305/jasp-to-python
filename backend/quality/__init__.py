"""Controle de qualidade / Six Sigma (equivalente ao módulo jaspQualityControl)."""

from .capability import capability_analysis
from .control_charts import imr_chart, xbar_r_chart

__all__ = ["capability_analysis", "imr_chart", "xbar_r_chart"]
