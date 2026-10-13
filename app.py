"""Interface web (Dash + Tailwind CSS) das análises migradas do JASP.

Rodar localmente:  python app.py
Produção (Cloud Run): gunicorn app:server
"""

from __future__ import annotations

import base64
import io
from pathlib import Path

import dash
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, State, dcc, html

from backend.quality import (
    analyze_design,
    box_behnken_design,
    c_chart,
    capability_analysis,
    central_composite_design,
    factorial_design,
    gauge_rr_crossed,
    imr_chart,
    laney_p_chart,
    laney_u_chart,
    np_chart,
    p_chart,
    u_chart,
)
from backend.quality.msa import gauge_rr_verdict

DATA_DIR = Path(__file__).parent / "data"
EXAMPLES = {
    "var": DATA_DIR / "exemplo_diametro.csv",
    "attr": DATA_DIR / "exemplo_atributos.csv",
    "msa": DATA_DIR / "exemplo_gage_rr.csv",
    "doe": DATA_DIR / "exemplo_doe.csv",
}
ATTRIBUTE_CHARTS = {
    "p": ("Carta p (proporção de defeituosos)", p_chart, True),
    "np": ("Carta np (nº de defeituosos)", np_chart, True),
    "c": ("Carta c (nº de defeitos)", c_chart, False),
    "u": ("Carta u (defeitos por unidade)", u_chart, True),
    "laney_p": ("Carta p' de Laney", laney_p_chart, True),
    "laney_u": ("Carta u' de Laney", laney_u_chart, True),
}
FIG_LAYOUT = {"margin": {"l": 40, "r": 10, "t": 10, "b": 40}, "template": "plotly_white", "height": 360}

app = dash.Dash(
    __name__,
    title="JASP para Python",
    external_scripts=["https://cdn.tailwindcss.com"],
    suppress_callback_exceptions=True,
)
server = app.server  # usado pelo gunicorn


# ---------------------------------------------------------------------------
# Componentes
# ---------------------------------------------------------------------------

def _card(children, extra=""):
    return html.Div(children, className=f"bg-white rounded-xl shadow p-6 {extra}")


def _number_input(id_, label, value=None):
    return html.Label(
        [html.Span(label, className="block text-sm text-slate-600 mb-1"),
         dcc.Input(id=id_, type="number", value=value, debounce=True,
                   className="w-full border rounded px-2 py-1")],
        className="block",
    )


def _dropdown(id_, label, multi=False, options=None, value=None):
    return html.Div([
        html.Label(label, className="block text-sm text-slate-600 mb-1"),
        dcc.Dropdown(id=id_, multi=multi, options=options or [], value=value, clearable=False),
    ], className="mb-3")


def _data_panel(prefix):
    """Upload de CSV + nome do conjunto; cada aba começa com o seu exemplo."""
    return html.Div([
        html.H2("Dados", className="font-semibold mb-3"),
        dcc.Upload(
            id=f"{prefix}-upload",
            children=html.Div("Arraste um CSV ou clique para enviar"),
            className="border-2 border-dashed rounded p-4 text-center text-sm cursor-pointer mb-2",
        ),
        html.P(id=f"{prefix}-name", className="text-xs text-slate-500 mb-4"),
        dcc.Store(id=f"{prefix}-data"),
    ])


def _table(df: pd.DataFrame, index_label: str):
    df = df.reset_index()
    df = df.rename(columns={df.columns[0]: index_label})

    def fmt(v):
        if isinstance(v, (float, np.floating)):
            return "—" if np.isnan(v) else (f"{v:.4g}" if abs(v) < 1e-3 or abs(v) >= 1e4 else f"{v:.4f}".rstrip("0").rstrip("."))
        return str(v)

    head = html.Tr([html.Th(c, className="text-left px-2 py-1 font-medium") for c in df.columns])
    body = [html.Tr([html.Td(fmt(v), className="px-2 py-1") for v in row], className="border-t")
            for row in df.itertuples(index=False)]
    return html.Div(html.Table([html.Thead(head, className="bg-slate-50"), html.Tbody(body)],
                               className="text-sm w-full"), className="overflow-x-auto")


def _error(exc):
    return html.P(str(exc), className="text-red-600")


def _control_figure(chart: pd.DataFrame, name: str, violations: list[int]) -> go.Figure:
    fig = go.Figure()
    x = np.arange(1, len(chart) + 1)
    fig.add_scatter(x=x, y=chart["value"], mode="lines+markers", name=name)
    fig.add_scatter(x=x, y=chart["center"], mode="lines", name="LC")
    for col in ("ucl", "lcl"):
        fig.add_scatter(x=x, y=chart[col], mode="lines", name=col.upper().replace("UCL", "LSC").replace("LCL", "LIC"),
                        line={"dash": "dash", "shape": "hvh"})
    if violations:
        fig.add_scatter(x=x[violations], y=chart["value"].iloc[violations], mode="markers", name="Fora de controle",
                        marker={"color": "red", "size": 11})
    fig.update_layout(**FIG_LAYOUT)
    return fig


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

variables_tab = html.Div(className="grid gap-6 md:grid-cols-3", children=[
    _card([
        _data_panel("var"),
        _dropdown("column", "Variável"),
        html.H2("Especificação", className="font-semibold mb-3"),
        html.Div(className="grid grid-cols-3 gap-2", children=[
            _number_input("lsl", "LSL", 9.85),
            _number_input("target", "Alvo", 10.0),
            _number_input("usl", "USL", 10.15),
        ]),
    ]),
    html.Div(className="md:col-span-2 grid gap-6", children=[
        _card([html.H2("Capacidade do processo", className="font-semibold mb-3"), html.Div(id="capability")]),
        _card([html.H2("Carta de controle I-MR", className="font-semibold mb-3"),
               dcc.Graph(id="imr", config={"displaylogo": False})]),
    ]),
])

attributes_tab = html.Div(className="grid gap-6 md:grid-cols-3", children=[
    _card([
        _data_panel("attr"),
        _dropdown("attr-type", "Carta", options=[{"label": v[0], "value": k} for k, v in ATTRIBUTE_CHARTS.items()],
                  value="p"),
        _dropdown("attr-count", "Defeituosos / defeitos"),
        _dropdown("attr-size", "Tamanho da amostra"),
    ]),
    html.Div(className="md:col-span-2", children=_card([
        html.H2(id="attr-title", className="font-semibold mb-3"),
        dcc.Graph(id="attr-graph", config={"displaylogo": False}),
        html.Div(id="attr-summary", className="text-sm"),
    ])),
])

msa_tab = html.Div(className="grid gap-6 md:grid-cols-3", children=[
    _card([
        _data_panel("msa"),
        _dropdown("msa-part", "Peça"),
        _dropdown("msa-operator", "Operador"),
        _dropdown("msa-measure", "Medição"),
        _number_input("msa-tol", "Tolerância (LSE − LIE, opcional)", 0.6),
    ]),
    html.Div(className="md:col-span-2 grid gap-6", children=[
        _card([html.H2("Avaliação do sistema de medição", className="font-semibold mb-3"),
               html.Div(id="msa-eval")]),
        _card([html.H2("Componentes de variação", className="font-semibold mb-3"),
               dcc.Graph(id="msa-graph", config={"displaylogo": False})]),
        _card([html.H2("ANOVA", className="font-semibold mb-3"), html.Div(id="msa-anova")]),
    ]),
])

doe_tab = html.Div(className="grid gap-6 md:grid-cols-3", children=[
    html.Div(className="grid gap-6 content-start", children=[
        _card([
            html.H2("Criar planejamento", className="font-semibold mb-3"),
            _dropdown("doe-design", "Tipo", value="factorial", options=[
                {"label": "Fatorial 2 níveis", "value": "factorial"},
                {"label": "Composto central (CCD)", "value": "ccd"},
                {"label": "Box-Behnken", "value": "bbd"},
            ]),
            html.Div(className="grid grid-cols-3 gap-2 mb-3", children=[
                _number_input("doe-k", "Fatores", 3),
                _number_input("doe-runs", "Corridas", None),
                _number_input("doe-center", "Centrais", 0),
            ]),
            html.Button("Gerar e baixar CSV", id="doe-create",
                        className="bg-slate-900 text-white rounded px-3 py-1 text-sm"),
            html.P(id="doe-created", className="text-xs text-slate-500 mt-2"),
            dcc.Download(id="doe-download"),
        ]),
        _card([
            html.H2("Analisar", className="font-semibold mb-3"),
            _data_panel("doe"),
            _dropdown("doe-response", "Resposta"),
            _dropdown("doe-factors", "Fatores", multi=True),
            _dropdown("doe-model", "Modelo", value="interactions", options=[
                {"label": "Efeitos principais", "value": "linear"},
                {"label": "Com interações de 2ª ordem", "value": "interactions"},
                {"label": "Quadrático (superfície de resposta)", "value": "quadratic"},
            ]),
            dcc.Checklist(id="doe-coded", options=[{"label": " Fatores já codificados (−1/+1)", "value": "coded"}],
                          value=[], className="text-sm"),
        ]),
    ]),
    html.Div(className="md:col-span-2 grid gap-6 content-start", children=[
        _card([html.H2("Pareto dos efeitos padronizados", className="font-semibold mb-3"),
               dcc.Graph(id="doe-pareto", config={"displaylogo": False})]),
        _card([html.H2("Coeficientes codificados", className="font-semibold mb-3"), html.Div(id="doe-coef")]),
    ]),
])

app.layout = html.Div(
    className="min-h-screen bg-slate-100 text-slate-800",
    children=[
        html.Header(
            html.H1("Análises estatísticas · JASP em Python", className="text-xl font-semibold"),
            className="bg-slate-900 text-white px-6 py-4",
        ),
        html.Main(className="max-w-6xl mx-auto p-6", children=dcc.Tabs(
            value="var", className="mb-6",
            children=[
                dcc.Tab(label="Variáveis (capacidade e I-MR)", value="var", children=html.Div(variables_tab, className="pt-6")),
                dcc.Tab(label="Atributos (p, np, c, u)", value="attr", children=html.Div(attributes_tab, className="pt-6")),
                dcc.Tab(label="Gage R&R (MSA)", value="msa", children=html.Div(msa_tab, className="pt-6")),
                dcc.Tab(label="DOE", value="doe", children=html.Div(doe_tab, className="pt-6")),
            ],
        )),
    ],
)


# ---------------------------------------------------------------------------
# Dados
# ---------------------------------------------------------------------------

def _register_loader(prefix):
    @app.callback(
        Output(f"{prefix}-data", "data"), Output(f"{prefix}-name", "children"),
        Input(f"{prefix}-upload", "contents"), State(f"{prefix}-upload", "filename"),
    )
    def load(contents, filename):
        if contents is None:
            example = EXAMPLES[prefix]
            return pd.read_csv(example).to_json(orient="split"), f"Exemplo: {example.name}"
        _, b64 = contents.split(",", 1)
        df = pd.read_csv(io.StringIO(base64.b64decode(b64).decode("utf-8-sig")), sep=None, engine="python")
        return df.to_json(orient="split"), filename


for _prefix in EXAMPLES:
    _register_loader(_prefix)


def _df(data) -> pd.DataFrame:
    return pd.read_json(io.StringIO(data), orient="split")


def _pick(columns, *candidates, default=None):
    lower = {c.lower(): c for c in columns}
    for cand in candidates:
        for low, col in lower.items():
            if cand in low:
                return col
    return default


# ---------------------------------------------------------------------------
# Aba Variáveis
# ---------------------------------------------------------------------------

@app.callback(Output("column", "options"), Output("column", "value"), Input("var-data", "data"))
def list_columns(data):
    numeric = _df(data).select_dtypes("number").columns.tolist()
    return numeric, numeric[-1] if numeric else None


def _fmt(v):
    return "—" if v is None else f"{v:.3f}"


@app.callback(
    Output("capability", "children"), Output("imr", "figure"),
    Input("var-data", "data"), Input("column", "value"),
    Input("lsl", "value"), Input("usl", "value"), Input("target", "value"),
)
def analyse(data, column, lsl, usl, target):
    if not column:
        return html.P("Selecione uma variável numérica."), go.Figure()
    values = _df(data)[column]

    try:
        cap = capability_analysis(values, lsl=lsl, usl=usl, target=target)
        rows = [("Cp", cap["Cp"]), ("Cpk", cap["Cpk"]), ("Pp", cap["Pp"]), ("Ppk", cap["Ppk"]),
                ("Cpm", cap.get("Cpm")), ("PPM total", cap["ppm_overall"]["ppm_total"]),
                ("Nível sigma", cap["sigma_level"])]
        capability = html.Div(className="grid grid-cols-2 md:grid-cols-4 gap-3", children=[
            html.Div([html.Div(k, className="text-xs text-slate-500"),
                      html.Div(_fmt(v), className="text-lg font-semibold")],
                     className="bg-slate-50 rounded p-3")
            for k, v in rows
        ])
    except ValueError as exc:
        capability = _error(exc)

    imr = imr_chart(values)["individuals"]
    fig = go.Figure()
    fig.add_scatter(y=imr["value"], mode="lines+markers", name=column)
    for col, dash_style in (("center", "solid"), ("ucl", "dash"), ("lcl", "dash")):
        fig.add_scatter(y=imr[col], mode="lines", name=col.upper(), line={"dash": dash_style})
    fig.update_layout(**FIG_LAYOUT)
    return capability, fig


# ---------------------------------------------------------------------------
# Aba Atributos
# ---------------------------------------------------------------------------

@app.callback(
    Output("attr-count", "options"), Output("attr-count", "value"),
    Output("attr-size", "options"), Output("attr-size", "value"),
    Input("attr-data", "data"), Input("attr-type", "value"),
)
def attr_columns(data, chart_type):
    cols = _df(data).select_dtypes("number").columns.tolist()
    defects = chart_type in ("c", "u", "laney_u")
    count = _pick(cols, *(("defeitos", "defects") if defects else ("defeituos", "defective")), default=cols[-1] if cols else None)
    size = _pick(cols, "inspec", "tamanho", "size", default=cols[0] if cols else None)
    return cols, count, cols, size


@app.callback(
    Output("attr-title", "children"), Output("attr-graph", "figure"), Output("attr-summary", "children"),
    Input("attr-data", "data"), Input("attr-type", "value"),
    Input("attr-count", "value"), Input("attr-size", "value"),
)
def attr_analyse(data, chart_type, count, size):
    title, func, needs_size = ATTRIBUTE_CHARTS[chart_type]
    if not count or (needs_size and not size):
        return title, go.Figure(), html.P("Selecione as colunas.")
    df = _df(data)
    try:
        res = func(df[count], df[size]) if needs_size else func(df[count])
    except ValueError as exc:
        return title, go.Figure(), _error(exc)
    v = res["violations"]
    lines = [f"Linha central: {res['center']:.4g}."]
    lines.append(f"Pontos fora dos limites (subgrupos): {', '.join(str(i + 1) for i in v['rule1'])}."
                 if v["rule1"] else "Nenhum ponto fora dos limites.")
    if v["rule2"]:
        lines.append(f"Regra 2 (9 do mesmo lado) nos subgrupos {', '.join(str(i + 1) for i in v['rule2'])}.")
    if v["rule3"]:
        lines.append(f"Regra 3 (6 em tendência) nos subgrupos {', '.join(str(i + 1) for i in v['rule3'])}.")
    if "sigma_z" in res:
        lines.append(f"σz de Laney = {res['sigma_z']:.3f} (> 1 indica sobredispersão).")
    return title, _control_figure(res["chart"], count, v["rule1"]), html.Ul([html.Li(t) for t in lines])


# ---------------------------------------------------------------------------
# Aba Gage R&R
# ---------------------------------------------------------------------------

@app.callback(
    Output("msa-part", "options"), Output("msa-part", "value"),
    Output("msa-operator", "options"), Output("msa-operator", "value"),
    Output("msa-measure", "options"), Output("msa-measure", "value"),
    Input("msa-data", "data"),
)
def msa_columns(data):
    df = _df(data)
    cols = df.columns.tolist()
    numeric = df.select_dtypes("number").columns.tolist()
    ops = [{"label": "(nenhum: estudo tipo 3)", "value": ""}] + [{"label": c, "value": c} for c in cols]
    return (cols, _pick(cols, "peça", "peca", "part", default=cols[0]),
            ops, _pick(cols, "oper", "apprais", default=""),
            numeric, _pick(numeric, "medi", "measure", "resp", default=numeric[-1] if numeric else None))


@app.callback(
    Output("msa-eval", "children"), Output("msa-graph", "figure"), Output("msa-anova", "children"),
    Input("msa-data", "data"), Input("msa-part", "value"), Input("msa-operator", "value"),
    Input("msa-measure", "value"), Input("msa-tol", "value"),
)
def msa_analyse(data, part, operator, measure, tol):
    if not part or not measure:
        return html.P("Selecione as colunas."), go.Figure(), None
    try:
        r = gauge_rr_crossed(_df(data), part, operator or None, measure, tolerance=tol or None)
    except (ValueError, KeyError) as exc:
        return _error(exc), go.Figure(), None
    ev = r["gauge_evaluation"]
    pct = ev.loc["R&R total", "pct_study_var"]
    names = {"sd": "Desvio padrão", "study_var": "Var. do estudo (6σ)", "pct_study_var": "% Var. estudo",
             "pct_tolerance": "% Tolerância"}
    verdict = html.P([
        html.Span(f"R&R total = {pct:.1f}% da variação do estudo: {gauge_rr_verdict(pct)}. ", className="font-medium"),
        f"Categorias distintas (ndc) = {r['ndc']}" + (" (≥ 5 recomendado)." if r["ndc"] is not None else "."),
    ], className="text-sm mb-3")
    evaluation = html.Div([verdict, _table(ev.rename(columns=names), "Fonte")])

    vc = r["variance_components"]
    keys = [k for k in ("R&R total", "Repetibilidade", "Reprodutibilidade", "Peça a peça") if k in vc.index]
    fig = go.Figure()
    fig.add_bar(x=keys, y=vc.loc[keys, "pct_contribution"], name="% Contribuição")
    fig.add_bar(x=keys, y=ev.loc[keys, "pct_study_var"], name="% Var. estudo")
    if "pct_tolerance" in ev:
        fig.add_bar(x=keys, y=ev.loc[keys, "pct_tolerance"], name="% Tolerância")
    fig.update_layout(barmode="group", **FIG_LAYOUT)

    anova_cols = {"df": "GL", "ss": "SQ", "ms": "QM", "f": "F", "p": "p"}
    anova = [_table(r["anova"].rename(columns=anova_cols), "Fonte")]
    if r["interaction_removed"]:
        anova += [html.P("Interação não significativa: removida e incorporada à repetibilidade.",
                         className="text-sm text-slate-500 my-3"),
                  _table(r["anova_reduced"].rename(columns=anova_cols), "Fonte")]
    return evaluation, fig, html.Div(anova)


# ---------------------------------------------------------------------------
# Aba DOE
# ---------------------------------------------------------------------------

@app.callback(
    Output("doe-download", "data"), Output("doe-created", "children"),
    Input("doe-create", "n_clicks"),
    State("doe-design", "value"), State("doe-k", "value"), State("doe-runs", "value"), State("doe-center", "value"),
    prevent_initial_call=True,
)
def doe_create(_, kind, k, runs, center):
    try:
        k = int(k or 3)
        center = int(center) if center is not None else None
        if kind == "factorial":
            design = factorial_design(k, runs=int(runs) if runs else None, center_points=center or 0,
                                      randomize=True, seed=1)
            info = f"{len(design)} corridas, resolução {design.attrs['resolution'] or 'completa'}."
        elif kind == "ccd":
            design = central_composite_design(k, center_points=center or None, randomize=True, seed=1)
            info = f"{len(design)} corridas, α = {design.attrs['alpha']:.3f}."
        else:
            design = box_behnken_design(k, center_points=center or None, randomize=True, seed=1)
            info = f"{len(design)} corridas."
    except ValueError as exc:
        return None, str(exc)
    return dcc.send_data_frame(design.to_csv, f"planejamento_{kind}_{k}fatores.csv", index=False), info


@app.callback(
    Output("doe-response", "options"), Output("doe-response", "value"),
    Output("doe-factors", "options"), Output("doe-factors", "value"),
    Input("doe-data", "data"),
)
def doe_columns(data):
    numeric = _df(data).select_dtypes("number").columns.tolist()
    design_cols = {"StdOrder", "RunOrder", "CenterPt", "PtType", "Blocks"}
    candidates = [c for c in numeric if c not in design_cols]
    response = candidates[-1] if candidates else None
    return numeric, response, numeric, [c for c in candidates if c != response]


@app.callback(
    Output("doe-pareto", "figure"), Output("doe-coef", "children"),
    Input("doe-data", "data"), Input("doe-response", "value"), Input("doe-factors", "value"),
    Input("doe-model", "value"), Input("doe-coded", "value"),
)
def doe_analyse(data, response, factors, model, coded):
    if not response or not factors:
        return go.Figure(), html.P("Selecione a resposta e os fatores.")
    try:
        r = analyze_design(_df(data), response, list(factors), model=model,
                           coding="none" if "coded" in (coded or []) else "auto")
    except (ValueError, KeyError) as exc:
        return go.Figure(), _error(exc)

    par = r["pareto"]["effects"].iloc[::-1]
    crit = r["pareto"]["critical"]
    fig = go.Figure(go.Bar(x=par["standardized_effect"], y=par["term"], orientation="h",
                           marker_color=np.where(par["standardized_effect"] > crit, "#dc2626", "#64748b")))
    fig.add_vline(x=crit, line_dash="dash", line_color="#dc2626",
                  annotation_text=f"{'t' if r['pareto']['method'] == 't' else 'Lenth'} = {crit:.2f}")
    fig.update_layout(**{**FIG_LAYOUT, "height": max(300, 28 * len(par) + 80)})

    s = r["summary"]
    summary = html.P(
        f"S = {s['S']:.4g} · R² = {100 * s['R2']:.1f}% · R² ajustado = {100 * s['R2_adj']:.1f}% · "
        f"R² predito = {100 * s['R2_pred']:.1f}%" if s["df_error"] > 0 else
        "Modelo saturado (sem graus de liberdade para o erro): efeitos avaliados pelo método de Lenth.",
        className="text-sm mb-2")
    coef = r["coefficients"].rename(columns={"effect": "Efeito", "coef": "Coef.", "se": "EP", "t": "t", "p": "p"})
    parts = [summary, html.P(r["equation"], className="text-sm font-mono mb-3"), _table(coef, "Termo")]
    sp = r.get("stationary_point")
    if sp:
        coords = ", ".join(f"{k} = {v:.3f}" for k, v in sp["coded"].items())
        parts.append(html.P(f"Ponto estacionário ({sp['nature']}): {coords} → {response} = {sp['response']:.4g}",
                            className="text-sm mt-3"))
    return fig, html.Div(parts)


if __name__ == "__main__":
    app.run(debug=True, port=8050)
