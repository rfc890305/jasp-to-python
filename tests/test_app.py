"""Navegação do app: menus no estilo do Minitab e páginas de cada item."""

import pytest

import app
from menu import ITEMS, MENU, Item, Node


def test_every_page_key_exists():
    for item in ITEMS.values():
        if item.page:
            name, _, _ = item.page.partition(":")
            assert name in app.PAGES, item.path


def test_menu_has_at_most_three_levels_below_top():
    # Topo (Calc/Estat/Gráfico) › submenu › grupo › item: o layout dos menus não desenha mais que isso
    for menu in MENU:
        for child in menu.children:
            for grand in getattr(child, "children", []):
                for leaf in getattr(grand, "children", []):
                    assert isinstance(leaf, Item), leaf
            assert isinstance(child, (Item, Node))


def test_paths_are_slugs():
    assert "/estat/cartas-de-controle/cartas-de-atributos/p-de-laney" in ITEMS
    assert "/assistente/doe/planejar-e-criar" in ITEMS
    assert ITEMS["/estat/cartas-de-controle/cartas-de-variaveis-para-subgrupos/xbarra-r"].page == "xbar-r"


@pytest.mark.parametrize("path", ["/", "/nao-existe", *ITEMS])
def test_every_route_renders(path):
    assert app.render(path) is not None


def test_attribute_labels_follow_chart_type():
    import pandas as pd

    data = pd.read_csv(app.DATA_DIR / "teste_cartas_controle.csv").to_json(orient="split")
    _, count, _, size, label, size_style, _ = app.attr_columns(data, "p")
    assert (count, size, size_style) == ("Defeituosos", "Inspecionados", None)
    assert "defeituosas" in label
    _, count, _, _, label, size_style, help_ = app.attr_columns(data, "c")
    assert count == "Defeitos" and "defeitos" in label
    assert size_style == {"display": "none"} and "não usa tamanho" in help_


def test_constant_sample_size_and_column_numbers():
    import pandas as pd

    data = pd.DataFrame({"mes": range(1, 13), "N_Acidentes": [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 8]}).to_json(orient="split")
    count_opts, count, size_opts, size, *_ = app.attr_columns(data, "u")
    assert count_opts[1] == {"label": "C2 N_Acidentes", "value": "N_Acidentes"}
    assert size == app.CONSTANT and size_opts[-1]["value"] == app.CONSTANT
    _, fig, summary = app.attr_analyse(data, "u", "N_Acidentes", app.CONSTANT, 1)
    assert len(fig.data) >= 4 and "Linha central" in str(summary)
