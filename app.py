"""Interface web (Dash + Tailwind CSS) das análises migradas do JASP.

Rodar localmente:  python app.py
Produção (Cloud Run): gunicorn app:server
"""

from __future__ import annotations

import base64
import io
from pathlib import Path

import dash
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, State, dcc, html

from backend.quality import capability_analysis, imr_chart

EXAMPLE = Path(__file__).parent / "data" / "exemplo_diametro.csv"

app = dash.Dash(
    __name__,
    title="JASP para Python",
    external_scripts=["https://cdn.tailwindcss.com"],
)
server = app.server  # usado pelo gunicorn


def _card(children, extra=""):
    return html.Div(children, className=f"bg-white rounded-xl shadow p-6 {extra}")


def _number_input(id_, label, value=None):
    return html.Label(
        [html.Span(label, className="block text-sm text-slate-600 mb-1"),
         dcc.Input(id=id_, type="number", value=value, debounce=True,
                   className="w-full border rounded px-2 py-1")],
        className="block",
    )


app.layout = html.Div(
    className="min-h-screen bg-slate-100 text-slate-800",
    children=[
        html.Header(
            html.H1("Análises estatísticas · JASP em Python", className="text-xl font-semibold"),
            className="bg-slate-900 text-white px-6 py-4",
        ),
        html.Main(
            className="max-w-6xl mx-auto p-6 grid gap-6 md:grid-cols-3",
            children=[
                _card([
                    html.H2("Dados", className="font-semibold mb-3"),
                    dcc.Upload(
                        id="upload",
                        children=html.Div("Arraste um CSV ou clique para enviar"),
                        className="border-2 border-dashed rounded p-4 text-center text-sm cursor-pointer mb-2",
                    ),
                    html.P(id="dataset-name", className="text-xs text-slate-500 mb-4"),
                    html.Label("Variável", className="block text-sm text-slate-600 mb-1"),
                    dcc.Dropdown(id="column", className="mb-4"),
                    html.H2("Especificação", className="font-semibold mb-3"),
                    html.Div(className="grid grid-cols-3 gap-2", children=[
                        _number_input("lsl", "LSL", 9.85),
                        _number_input("target", "Alvo", 10.0),
                        _number_input("usl", "USL", 10.15),
                    ]),
                    dcc.Store(id="data"),
                ]),
                html.Div(className="md:col-span-2 grid gap-6", children=[
                    _card([html.H2("Capacidade do processo", className="font-semibold mb-3"),
                           html.Div(id="capability")]),
                    _card([html.H2("Carta de controle I-MR", className="font-semibold mb-3"),
                           dcc.Graph(id="imr", config={"displaylogo": False})]),
                ]),
            ],
        ),
    ],
)


@app.callback(
    Output("data", "data"), Output("dataset-name", "children"),
    Input("upload", "contents"), State("upload", "filename"),
)
def load_data(contents, filename):
    if contents is None:
        return pd.read_csv(EXAMPLE).to_json(orient="split"), f"Exemplo: {EXAMPLE.name}"
    _, b64 = contents.split(",", 1)
    df = pd.read_csv(io.StringIO(base64.b64decode(b64).decode("utf-8")), sep=None, engine="python")
    return df.to_json(orient="split"), filename


@app.callback(Output("column", "options"), Output("column", "value"), Input("data", "data"))
def list_columns(data):
    df = pd.read_json(io.StringIO(data), orient="split")
    numeric = df.select_dtypes("number").columns.tolist()
    return numeric, numeric[-1] if numeric else None


def _fmt(v):
    return "—" if v is None else f"{v:.3f}"


@app.callback(
    Output("capability", "children"), Output("imr", "figure"),
    Input("data", "data"), Input("column", "value"),
    Input("lsl", "value"), Input("usl", "value"), Input("target", "value"),
)
def analyse(data, column, lsl, usl, target):
    if not column:
        return html.P("Selecione uma variável numérica."), go.Figure()
    values = pd.read_json(io.StringIO(data), orient="split")[column]

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
        capability = html.P(str(exc), className="text-red-600")

    imr = imr_chart(values)["individuals"]
    fig = go.Figure()
    fig.add_scatter(y=imr["value"], mode="lines+markers", name=column)
    for col, dash_style in (("center", "solid"), ("ucl", "dash"), ("lcl", "dash")):
        fig.add_scatter(y=imr[col], mode="lines", name=col.upper(), line={"dash": dash_style})
    fig.update_layout(margin={"l": 40, "r": 10, "t": 10, "b": 40}, template="plotly_white", height=360)
    return capability, fig


if __name__ == "__main__":
    app.run(debug=True, port=8050)
