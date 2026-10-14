"""Interface web (Dash + Tailwind CSS) das análises migradas do JASP.

A navegação segue os menus do Minitab (Calc, Estat, Gráfico), definidos em menu.py.
Cada item com tela tem uma página aqui (PAGES); os demais aparecem como "em breve".

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
from dash import Input, Output, State, ctx, dcc, html

from backend.descriptives import describe
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
    xbar_r_chart,
)
from backend.quality.msa import gauge_rr_verdict
from menu import ITEMS, MENU, Item, Node

DATA_DIR = Path(__file__).parent / "data"
MATRIX_URL = "https://github.com/rfc890305/jasp-to-python/blob/main/docs/comparacao-minitab.md"
# Conjunto de exemplo carregado em cada página até o usuário enviar um CSV
EXAMPLES = {
    "desc": DATA_DIR / "exemplo_diametro.csv",
    "cap": DATA_DIR / "exemplo_diametro.csv",
    "imr": DATA_DIR / "exemplo_diametro.csv",
    "xbar": DATA_DIR / "exemplo_diametro.csv",
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
DOE_DESIGNS = {"factorial": "Fatorial 2 níveis", "ccd": "Composto central (CCD)", "bbd": "Box-Behnken"}
JASP_STATUS = {
    "✅": "Existe no JASP: será migrado do módulo R correspondente.",
    "🟡": "Existe em parte no JASP: parte será migrada e o restante desenvolvido.",
    "⬜": "Não existe no JASP: será desenvolvido do zero em Python.",
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


def _section(title, *children):
    return _card([html.H2(title, className="font-semibold mb-3"), *children])


def _number_input(id_, label, value=None):
    return html.Label(
        [html.Span(label, className="block text-sm text-slate-600 mb-1"),
         dcc.Input(id=id_, type="number", value=value, debounce=True,
                   className="w-full border rounded px-2 py-1")],
        className="block",
    )


def _dropdown(id_, label, multi=False, options=None, value=None):
    return html.Div([
        html.Label(label, id=f"{id_}-label", htmlFor=id_, className="block text-sm text-slate-600 mb-1"),
        dcc.Dropdown(id=id_, multi=multi, options=options or [], value=value, clearable=False),
    ], className="mb-3")


def _data_panel(prefix):
    """Upload de CSV + nome do conjunto; sem arquivo enviado, a página usa o seu exemplo."""
    return html.Div([
        html.H2("Dados", className="font-semibold mb-3"),
        dcc.Upload(
            id=f"{prefix}-upload",
            children=html.Div("Arraste um CSV ou clique para enviar"),
            className="border-2 border-dashed rounded p-4 text-center text-sm cursor-pointer mb-2",
        ),
        html.Div(className="flex items-center justify-between gap-2 mb-4", children=[
            html.P(id=f"{prefix}-name", className="text-xs text-slate-500"),
            html.Button("Usar exemplo", id=f"{prefix}-example", className="text-xs text-sky-700 underline"),
        ]),
        html.P("O arquivo enviado vale para todas as análises até você enviar outro.",
               className="text-xs text-slate-400 -mt-3 mb-4"),
        dcc.Store(id=f"{prefix}-data"),
    ])


def _graph(id_):
    return dcc.Graph(id=id_, config={"displaylogo": False})


def _two_columns(side, *main):
    return html.Div(className="grid gap-6 md:grid-cols-3", children=[
        html.Div(side, className="grid gap-6 content-start"),
        html.Div(className="md:col-span-2 grid gap-6 content-start", children=list(main)),
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


def _control_figure(chart: pd.DataFrame, name: str, violations: list[int], height=None) -> go.Figure:
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
    fig.update_layout(**{**FIG_LAYOUT, **({"height": height} if height else {})})
    return fig


def _out_of_limits(chart: pd.DataFrame) -> list[int]:
    """Pontos além de LSC/LIC (teste 1), para as cartas de amplitude."""
    value = chart["value"]
    return [int(i) for i in np.where((value > chart["ucl"]) | (value < chart["lcl"]))[0]]


def _violations_summary(center, v, unit="subgrupos"):
    lines = [f"Linha central: {center:.4g}."]
    lines.append(f"Pontos fora dos limites ({unit}): {', '.join(str(i + 1) for i in v['rule1'])}."
                 if v["rule1"] else "Nenhum ponto fora dos limites.")
    if v["rule2"]:
        lines.append(f"Regra 2 (9 do mesmo lado), {unit}: {', '.join(str(i + 1) for i in v['rule2'])}.")
    if v["rule3"]:
        lines.append(f"Regra 3 (6 em tendência), {unit}: {', '.join(str(i + 1) for i in v['rule3'])}.")
    return lines


# ---------------------------------------------------------------------------
# Menus no estilo do Minitab
# ---------------------------------------------------------------------------

def _menu_link(item: Item, indent=False):
    pad = "pl-6 pr-3" if indent else "px-3"
    if item.page:
        return dcc.Link(item.label, href=item.path,
                        className=f"block {pad} py-1.5 whitespace-nowrap font-medium text-slate-900 hover:bg-sky-50")
    return dcc.Link([item.label, html.Span("em breve", className="ml-2 text-[10px] uppercase text-slate-400")],
                    href=item.path, className=f"block {pad} py-1.5 whitespace-nowrap text-slate-400 hover:bg-slate-50")


def _flyout_entries(node: Node):
    """Conteúdo de um submenu: itens e, quando houver, grupos com título."""
    out = []
    for child in node.children:
        if isinstance(child, Item):
            out.append(_menu_link(child))
        else:
            out.append(html.Div(child.label, className="px-3 pt-3 pb-1 text-xs font-semibold text-slate-500"))
            out += [_menu_link(grand, indent=True) for grand in child.children]
    return out


def _dropdown_entry(child):
    if isinstance(child, Item):
        return _menu_link(child)
    return html.Div(className="group/sub", children=[
        html.Div([html.Span(child.label), html.Span("›", className="ml-4 text-slate-400")], tabIndex=0,
                 className="flex justify-between px-3 py-1.5 whitespace-nowrap cursor-default "
                           "group-hover/sub:bg-slate-100 group-focus-within/sub:bg-slate-100"),
        html.Div(_flyout_entries(child),
                 # No celular o submenu abre logo abaixo; em telas maiores, ao lado
                 className="hidden group-hover/sub:block group-focus-within/sub:block bg-slate-50 py-1 "
                           "md:absolute md:left-full md:top-0 md:min-w-[16rem] md:max-h-[80vh] md:overflow-y-auto "
                           "md:bg-white md:rounded-r md:shadow-lg md:border"),
    ])


def _menu_bar():
    menus = []
    for menu in MENU:
        flat = all(isinstance(c, Item) for c in menu.children)
        panel_cls = ("hidden group-hover:block group-focus-within:block absolute left-0 top-full z-50 min-w-[16rem] "
                     "bg-white text-slate-800 rounded-b shadow-lg border py-1")
        menus.append(html.Div(className="group relative", children=[
            html.Button(menu.label, className="px-4 py-2 hover:bg-slate-700 group-focus-within:bg-slate-700"),
            # Submenus abrem ao lado, por isso só listas simples podem rolar
            html.Div([_dropdown_entry(c) for c in menu.children],
                     className=panel_cls + (" max-h-[80vh] overflow-y-auto" if flat else "")),
        ]))
    return html.Nav(menus, id="menu-bar", className="bg-slate-800 text-white text-sm px-2 flex relative z-40")


def _breadcrumb(trail):
    return html.P(" › ".join(trail), className="text-xs text-slate-500 mb-1")


def _page_header(item: Item, title=None):
    return html.Div([_breadcrumb(item.trail[:-1]),
                     html.H1(title or item.label, className="text-2xl font-semibold mb-6")])


# ---------------------------------------------------------------------------
# Páginas
# ---------------------------------------------------------------------------

def home_page():
    available = [it for it in ITEMS.values() if it.page]
    cards = [dcc.Link(_card([_breadcrumb(it.trail[:-1]), html.Div(it.label, className="font-semibold")],
                            "hover:ring-2 hover:ring-sky-400 h-full"), href=it.path)
             for it in available]
    return html.Div([
        html.H1("Análises disponíveis", className="text-2xl font-semibold mb-2"),
        html.P(f"{len(available)} de {len(ITEMS)} itens dos menus do Minitab já têm tela. "
               "Os demais aparecem nos menus como “em breve”.", className="text-sm text-slate-600 mb-6"),
        html.Div(cards, className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"),
    ])


def coming_soon_page(item: Item):
    return html.Div([
        _page_header(item),
        _card([
            html.P("Esta análise ainda não está disponível no app.", className="font-medium mb-2"),
            html.P(f"{item.jasp} {JASP_STATUS[item.jasp]}", className="text-sm text-slate-600 mb-4"),
            html.A("Ver a matriz Minitab × JASP", href=MATRIX_URL, target="_blank",
                   className="text-sm text-sky-700 underline"),
        ]),
    ])


def describe_page(item, _arg):
    return html.Div([_page_header(item), _two_columns(
        _card([_data_panel("desc"), _dropdown("desc-cols", "Colunas a resumir", multi=True)]),
        _section("Estatísticas descritivas", html.Div(id="desc-table")),
        _section("Boxplot", _graph("desc-box")),
    )])


def capability_page(item, _arg):
    return html.Div([_page_header(item, "Análise de capacidade normal"), _two_columns(
        _card([
            _data_panel("cap"),
            _dropdown("cap-col", "Coluna com as medições"),
            html.H2("Especificação", className="font-semibold mb-3"),
            html.Div(className="grid grid-cols-3 gap-2", children=[
                _number_input("cap-lsl", "LSL", 9.85),
                _number_input("cap-target", "Alvo", 10.0),
                _number_input("cap-usl", "USL", 10.15),
            ]),
        ]),
        _section("Índices de capacidade", html.Div(id="cap-result")),
        _section("Histograma e limites de especificação", _graph("cap-hist")),
    )])


def imr_page(item, _arg):
    return html.Div([_page_header(item, "Carta I-AM (valores individuais e amplitude móvel)"), _two_columns(
        _card([_data_panel("imr"), _dropdown("imr-col", "Coluna com as medições (uma por linha)")]),
        _section("Valores individuais", _graph("imr-i"), html.Div(id="imr-summary", className="text-sm")),
        _section("Amplitude móvel", _graph("imr-mr")),
    )])


def xbar_page(item, _arg):
    return html.Div([_page_header(item, "Carta Xbarra-R"), _two_columns(
        _card([
            _data_panel("xbar"),
            _dropdown("xbar-cols", "Colunas com as medições", multi=True),
            html.P("Uma coluna: subgrupos consecutivos do tamanho abaixo. Várias colunas: cada linha é um subgrupo.",
                   className="text-xs text-slate-500 mb-3"),
            _number_input("xbar-n", "Tamanho do subgrupo", 5),
        ]),
        _section("Médias (Xbarra)", _graph("xbar-x"), html.Div(id="xbar-summary", className="text-sm")),
        _section("Amplitudes (R)", _graph("xbar-r")),
    )])


def attr_page(item, chart_type):
    return html.Div([_page_header(item, ATTRIBUTE_CHARTS[chart_type][0]), _two_columns(
        _card([
            _data_panel("attr"),
            _dropdown("attr-type", "Carta", value=chart_type,
                      options=[{"label": v[0], "value": k} for k, v in ATTRIBUTE_CHARTS.items()]),
            _dropdown("attr-count", "Coluna de contagem"),
            html.Div(id="attr-size-box", children=_dropdown("attr-size", "Coluna com o tamanho da amostra")),
            html.P(id="attr-help", className="text-xs text-slate-500 mb-3"),
        ]),
        _card([
            html.H2(id="attr-title", className="font-semibold mb-3"),
            _graph("attr-graph"),
            html.Div(id="attr-summary", className="text-sm"),
        ]),
    )])


def msa_page(item, _arg):
    return html.Div([_page_header(item, "Gage R&R cruzado (ANOVA)"), _two_columns(
        _card([
            _data_panel("msa"),
            _dropdown("msa-part", "Coluna de peças"),
            _dropdown("msa-operator", "Coluna de operadores"),
            _dropdown("msa-measure", "Coluna com as medições"),
            _number_input("msa-tol", "Tolerância (LSE − LIE, opcional)", 0.6),
        ]),
        _section("Avaliação do sistema de medição", html.Div(id="msa-eval")),
        _section("Componentes de variação", _graph("msa-graph")),
        _section("ANOVA", html.Div(id="msa-anova")),
    )])


def doe_create_page(item, kind):
    return html.Div([_page_header(item, f"Criar planejamento: {DOE_DESIGNS[kind]}"), html.Div(
        className="max-w-md", children=_card([
            _dropdown("doe-design", "Tipo", value=kind,
                      options=[{"label": v, "value": k} for k, v in DOE_DESIGNS.items()]),
            html.Div(className="grid grid-cols-3 gap-2 mb-3", children=[
                _number_input("doe-k", "Fatores", 3),
                _number_input("doe-runs", "Corridas", None),
                _number_input("doe-center", "Centrais", 0),
            ]),
            html.P("Corridas vale só para o fatorial (fração); vazio gera o fatorial completo.",
                   className="text-xs text-slate-500 mb-3"),
            html.Button("Gerar e baixar CSV", id="doe-create",
                        className="bg-slate-900 text-white rounded px-3 py-1 text-sm"),
            html.P(id="doe-created", className="text-xs text-slate-500 mt-2"),
            dcc.Download(id="doe-download"),
        ]),
    )])


def doe_analyze_page(item, model):
    return html.Div([_page_header(item), _two_columns(
        _card([
            _data_panel("doe"),
            _dropdown("doe-response", "Coluna da resposta"),
            _dropdown("doe-factors", "Colunas dos fatores", multi=True),
            _dropdown("doe-model", "Modelo", value=model, options=[
                {"label": "Efeitos principais", "value": "linear"},
                {"label": "Com interações de 2ª ordem", "value": "interactions"},
                {"label": "Quadrático (superfície de resposta)", "value": "quadratic"},
            ]),
            dcc.Checklist(id="doe-coded", options=[{"label": " Fatores já codificados (−1/+1)", "value": "coded"}],
                          value=[], className="text-sm"),
        ]),
        _section("Pareto dos efeitos padronizados", _graph("doe-pareto")),
        _section("Coeficientes codificados", html.Div(id="doe-coef")),
    )])


PAGES = {
    "describe": describe_page,
    "capability": capability_page,
    "imr": imr_page,
    "xbar-r": xbar_page,
    "attr": attr_page,
    "gage-rr": msa_page,
    "doe-create": doe_create_page,
    "doe-analyze": doe_analyze_page,
}


def render(pathname: str | None):
    """Conteúdo da página para um caminho da URL."""
    path = (pathname or "/").rstrip("/") or "/"
    if path == "/":
        return home_page()
    item = ITEMS.get(path)
    if item is None:
        return _card([html.P("Página não encontrada.", className="mb-2"),
                      dcc.Link("Voltar ao início", href="/", className="text-sky-700 underline")])
    if not item.page:
        return coming_soon_page(item)
    name, _, arg = item.page.partition(":")
    return PAGES[name](item, arg)


app.layout = html.Div(
    className="min-h-screen bg-slate-100 text-slate-800",
    children=[
        dcc.Location(id="url"),
        dcc.Store(id="dataset", storage_type="session"),
        html.Header(
            dcc.Link(html.H1("Análises estatísticas · JASP em Python", className="text-xl font-semibold"), href="/"),
            className="bg-slate-900 text-white px-6 py-4",
        ),
        _menu_bar(),
        html.Main(id="page", className="max-w-6xl mx-auto p-6"),
    ],
)


@app.callback(Output("page", "children"), Input("url", "pathname"))
def route(pathname):
    return render(pathname)


# Fecha o menu depois de escolher um item (o foco no link o manteria aberto)
app.clientside_callback(
    "function(_) { if (document.activeElement) { document.activeElement.blur(); } return window.dash_clientside.no_update; }",
    Output("menu-bar", "title"), Input("url", "pathname"),
)


# ---------------------------------------------------------------------------
# Dados
# ---------------------------------------------------------------------------

def _register_loader(prefix):
    # O CSV enviado fica em "dataset" (sessão do navegador) e vale para todas as páginas,
    # como a planilha ativa do Minitab; sem envio, cada página usa o seu exemplo.
    @app.callback(
        Output(f"{prefix}-data", "data"), Output(f"{prefix}-name", "children"),
        Output("dataset", "data", allow_duplicate=True),
        Input(f"{prefix}-upload", "contents"), Input(f"{prefix}-example", "n_clicks"),
        State(f"{prefix}-upload", "filename"), State("dataset", "data"),
        prevent_initial_call="initial_duplicate",
    )
    def load(contents, _example, filename, dataset):
        if ctx.triggered_id == f"{prefix}-example":
            dataset = None
        elif contents is not None:
            _, b64 = contents.split(",", 1)
            df = pd.read_csv(io.StringIO(base64.b64decode(b64).decode("utf-8-sig")), sep=None, engine="python")
            dataset = {"name": filename, "data": df.to_json(orient="split")}
        if dataset:
            return dataset["data"], f"Arquivo: {dataset['name']}", dataset
        example = EXAMPLES[prefix]
        return pd.read_csv(example).to_json(orient="split"), f"Exemplo: {example.name}", None


for _prefix in EXAMPLES:
    _register_loader(_prefix)


def _df(data) -> pd.DataFrame:
    return pd.read_json(io.StringIO(data), orient="split")


def _numeric(data) -> list[str]:
    return _df(data).select_dtypes("number").columns.tolist()


def _pick(columns, *candidates, default=None):
    lower = {c.lower(): c for c in columns}
    for cand in candidates:
        for low, col in lower.items():
            if cand in low:
                return col
    return default


def _single_column(prefix):
    @app.callback(Output(f"{prefix}-col", "options"), Output(f"{prefix}-col", "value"), Input(f"{prefix}-data", "data"))
    def columns(data):
        numeric = _numeric(data)
        return numeric, _pick(numeric, "diam", "medi", default=numeric[-1] if numeric else None)


for _prefix in ("cap", "imr"):
    _single_column(_prefix)


def _fmt(v):
    return "—" if v is None else f"{v:.3f}"


# ---------------------------------------------------------------------------
# Estatísticas descritivas
# ---------------------------------------------------------------------------

@app.callback(Output("desc-cols", "options"), Output("desc-cols", "value"), Input("desc-data", "data"))
def desc_columns(data):
    numeric = _numeric(data)
    return numeric, [c for c in numeric if c.lower() not in ("amostra", "lote", "subgrupo")] or numeric


@app.callback(Output("desc-table", "children"), Output("desc-box", "figure"),
              Input("desc-data", "data"), Input("desc-cols", "value"))
def desc_analyse(data, cols):
    if not cols:
        return html.P("Selecione ao menos uma variável."), go.Figure()
    df = _df(data)
    names = {"n": "N", "mean": "Média", "std": "Desvio padrão", "se_mean": "EP da média", "min": "Mínimo",
             "q1": "Q1", "median": "Mediana", "q3": "Q3", "max": "Máximo", "skewness": "Assimetria",
             "kurtosis": "Curtose"}
    try:
        table = pd.DataFrame({c: describe(df[c]) for c in cols}).rename(index=names)
    except ValueError as exc:
        return _error(exc), go.Figure()
    fig = go.Figure([go.Box(y=df[c], name=c, boxmean=True) for c in cols])
    fig.update_layout(**FIG_LAYOUT, showlegend=False)
    return _table(table.T, "Variável"), fig


# ---------------------------------------------------------------------------
# Capacidade normal
# ---------------------------------------------------------------------------

@app.callback(
    Output("cap-result", "children"), Output("cap-hist", "figure"),
    Input("cap-data", "data"), Input("cap-col", "value"),
    Input("cap-lsl", "value"), Input("cap-usl", "value"), Input("cap-target", "value"),
)
def cap_analyse(data, column, lsl, usl, target):
    if not column:
        return html.P("Selecione uma variável numérica."), go.Figure()
    values = _df(data)[column].dropna()
    fig = go.Figure(go.Histogram(x=values, name=column, marker_color="#94a3b8"))
    for value, name, color in ((lsl, "LSL", "#dc2626"), (target, "Alvo", "#16a34a"), (usl, "USL", "#dc2626")):
        if value is not None:
            fig.add_vline(x=value, line_dash="dash", line_color=color, annotation_text=name)
    fig.update_layout(**FIG_LAYOUT, showlegend=False)
    try:
        cap = capability_analysis(values, lsl=lsl, usl=usl, target=target)
    except ValueError as exc:
        return _error(exc), fig
    rows = [("Cp", cap["Cp"]), ("Cpk", cap["Cpk"]), ("Pp", cap["Pp"]), ("Ppk", cap["Ppk"]),
            ("Cpm", cap.get("Cpm")), ("PPM total", cap["ppm_overall"]["ppm_total"]),
            ("Nível sigma", cap["sigma_level"]), ("N", float(cap["n"]))]
    return html.Div(className="grid grid-cols-2 md:grid-cols-4 gap-3", children=[
        html.Div([html.Div(k, className="text-xs text-slate-500"),
                  html.Div(_fmt(v) if k != "N" else str(int(v)), className="text-lg font-semibold")],
                 className="bg-slate-50 rounded p-3")
        for k, v in rows
    ]), fig


# ---------------------------------------------------------------------------
# Cartas por variáveis
# ---------------------------------------------------------------------------

@app.callback(
    Output("imr-i", "figure"), Output("imr-mr", "figure"), Output("imr-summary", "children"),
    Input("imr-data", "data"), Input("imr-col", "value"),
)
def imr_analyse(data, column):
    if not column:
        return go.Figure(), go.Figure(), html.P("Selecione uma variável numérica.")
    try:
        r = imr_chart(_df(data)[column])
    except ValueError as exc:
        return go.Figure(), go.Figure(), _error(exc)
    v = r["violations"]
    lines = _violations_summary(r["individuals"]["center"].iloc[0], v, "observações")
    return (_control_figure(r["individuals"], column, v["rule1"]),
            _control_figure(r["moving_range"], "MR", _out_of_limits(r["moving_range"]), height=280),
            html.Ul([html.Li(t) for t in lines]))


@app.callback(Output("xbar-cols", "options"), Output("xbar-cols", "value"), Input("xbar-data", "data"))
def xbar_columns(data):
    numeric = _numeric(data)
    subgroups = [c for c in numeric if c.lower().startswith("sub")]
    if len(subgroups) >= 2:
        return numeric, subgroups
    return numeric, [_pick(numeric, "diam", "medi", default=numeric[-1] if numeric else None)]


@app.callback(
    Output("xbar-x", "figure"), Output("xbar-r", "figure"), Output("xbar-summary", "children"),
    Input("xbar-data", "data"), Input("xbar-cols", "value"), Input("xbar-n", "value"),
)
def xbar_analyse(data, cols, size):
    cols = [c for c in (cols or []) if c]
    if not cols:
        return go.Figure(), go.Figure(), html.P("Selecione as colunas.")
    df = _df(data)
    try:
        if len(cols) == 1:
            values, n = df[cols[0]], int(size or 0)
        else:
            rows = df[cols].dropna()  # subgrupo incompleto quebraria o tamanho fixo
            values, n = rows.to_numpy().ravel(), len(cols)
        if n < 2:
            raise ValueError("O subgrupo precisa ter ao menos 2 observações.")
        r = xbar_r_chart(values, n)
    except ValueError as exc:
        return go.Figure(), go.Figure(), _error(exc)
    v = r["violations"]
    lines = _violations_summary(r["xbar"]["center"].iloc[0], v)
    out_r = _out_of_limits(r["range"])
    if out_r:
        lines.append(f"Amplitudes fora dos limites (subgrupos): {', '.join(str(i + 1) for i in out_r)}.")
    lines.append(f"Tamanho do subgrupo: {n}. Sigma estimado (R̄/d2): {r['sigma']:.4g}.")
    return (_control_figure(r["xbar"], "Média", v["rule1"]),
            _control_figure(r["range"], "Amplitude", out_r, height=280),
            html.Ul([html.Li(t) for t in lines]))


# ---------------------------------------------------------------------------
# Cartas por atributos
# ---------------------------------------------------------------------------

@app.callback(
    Output("attr-count", "options"), Output("attr-count", "value"),
    Output("attr-size", "options"), Output("attr-size", "value"),
    Output("attr-count-label", "children"), Output("attr-size-box", "style"), Output("attr-help", "children"),
    Input("attr-data", "data"), Input("attr-type", "value"),
)
def attr_columns(data, chart_type):
    cols = _numeric(data)
    defects = chart_type in ("c", "u", "laney_u")
    count = _pick(cols, *(("defeitos", "defects") if defects else ("defeituos", "defective")), default=cols[-1] if cols else None)
    size = _pick(cols, "inspec", "tamanho", "size", default=cols[0] if cols else None)
    needs_size = ATTRIBUTE_CHARTS[chart_type][2]
    if defects:
        label = "Coluna com o nº de defeitos por subgrupo"
        help_ = "Defeitos: falhas contadas (uma peça pode ter várias)."
    else:
        label = "Coluna com o nº de peças defeituosas por subgrupo"
        help_ = "Defeituosos: peças reprovadas (no máximo o tamanho da amostra)."
    if needs_size:
        help_ += " Tamanho da amostra: quantas peças foram inspecionadas em cada subgrupo."
    else:
        help_ += " A carta c supõe a mesma área de inspeção em todos os subgrupos e não usa tamanho de amostra."
    return cols, count, cols, size, label, None if needs_size else {"display": "none"}, help_


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
    lines = _violations_summary(res["center"], v)
    if "sigma_z" in res:
        lines.append(f"σz de Laney = {res['sigma_z']:.3f} (> 1 indica sobredispersão).")
    return title, _control_figure(res["chart"], count, v["rule1"]), html.Ul([html.Li(t) for t in lines])


# ---------------------------------------------------------------------------
# Gage R&R
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
# DOE
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
    numeric = _numeric(data)
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
