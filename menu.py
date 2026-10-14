"""Menus do app no estilo do Minitab (Calc, Estat, Gráfico).

A hierarquia e a coluna JASP seguem docs/comparacao-minitab.md. Cada item diz se a
funcionalidade existe no JASP (✅ existe, 🟡 parcial, ⬜ não existe) e, quando já tem
tela no app, o nome da página em `page` ("nome" ou "nome:argumento", ver PAGES em app.py).
Itens sem página aparecem como "em breve".
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field


@dataclass
class Item:
    label: str
    jasp: str = "⬜"
    page: str | None = None
    path: str = ""
    trail: tuple[str, ...] = ()


@dataclass
class Node:
    label: str
    children: list = field(default_factory=list)
    path: str = ""


def I(label, jasp="⬜", page=None):  # noqa: E743 - nome curto deixa a árvore legível
    return Item(label, jasp, page)


def N(label, *children):
    return Node(label, list(children))


MENU = [
    N("Calc",
      I("Calculadora", "🟡"),
      I("Estatísticas de Colunas", "🟡"),
      I("Estatísticas de Linhas", "🟡"),
      I("Padronizar", "🟡"),
      I("Criar Dados Padronizados", "🟡"),
      I("Criar Dados em Malha"),
      I("Criar Variáveis Indicadoras", "🟡"),
      I("Definir Base", "🟡"),
      I("Dados Aleatórios", "🟡"),
      I("Distribuições de Probabilidade", "✅"),
      I("Matrizes", "🟡")),
    N("Estat",
      N("Estatísticas Básicas",
        I("Exibir Estatísticas Descritivas", "✅", "describe"),
        I("Armazenar Estatísticas Descritivas", "🟡"),
        I("Resumo Gráfico", "🟡"),
        I("Z para 1 Amostra", "✅"),
        I("t para 1 Amostra", "✅"),
        I("t para 2 Amostras", "✅"),
        I("t Pareado", "✅"),
        I("1 Proporção", "✅"),
        I("2 Proporções", "🟡"),
        I("Taxa de Poisson de 1 Amostra"),
        I("Taxa de Poisson de 2 Amostras"),
        I("1 Variância", "🟡"),
        I("2 Variâncias", "🟡"),
        I("Correlação", "✅"),
        I("Covariância", "✅"),
        I("Teste de Normalidade", "✅"),
        I("Teste de Outlier"),
        I("Teste de Aderência para Poisson", "🟡")),
      N("Regressão",
        I("Ajustar Modelo de Regressão", "✅"),
        I("Regressão Stepwise", "✅"),
        I("Melhores Subconjuntos"),
        I("Previsão e Otimizador de Respostas", "🟡"),
        I("Gráfico de Linha Ajustada", "🟡"),
        I("Regressão Não Linear"),
        I("Regressão Ortogonal"),
        I("Mínimos Quadrados Parciais (PLS)", "🟡"),
        N("Regressão Logística",
          I("Regressão Logística Binária", "✅"),
          I("Regressão Logística Ordinal"),
          I("Regressão Logística Nominal", "🟡")),
        I("Regressão de Poisson", "✅"),
        I("Estudo de Estabilidade"),),
      N("ANOVA",
        I("Um Fator", "✅"),
        I("Análise de Médias (ANOM)"),
        I("ANOVA Balanceada", "✅"),
        I("Modelo Linear Geral", "✅"),
        I("Modelo Misto", "✅"),
        I("ANOVA Totalmente Aninhada", "🟡"),
        I("MANOVA Geral", "✅"),
        I("Teste para Variâncias Iguais", "🟡"),
        I("Gráfico de Intervalo", "✅"),
        I("Gráfico de Efeitos Principais", "✅"),
        I("Gráfico de Interação", "✅"),
        I("ANOVA de Medidas Repetidas", "✅")),
      N("DOE",
        N("Triagem",
          I("Plackett-Burman", "🟡"),
          I("Triagem Definitiva", "🟡")),
        N("Fatorial",
          I("Criar Planejamento Fatorial (2 níveis)", "✅", "doe-create:factorial"),
          I("Fatorial Completo Geral", "✅"),
          I("Parcelas Subdivididas (split-plot)", "✅"),
          I("Definir Planejamento Personalizado", "🟡"),
          I("Analisar Planejamento Fatorial", "✅", "doe-analyze:interactions"),
          I("Gráficos Fatoriais", "⬜")),
        N("Superfície de Resposta",
          I("Composto Central (CCD)", "✅", "doe-create:ccd"),
          I("Box-Behnken", "✅", "doe-create:bbd"),
          I("Analisar Superfície de Resposta", "✅", "doe-analyze:quadratic"),
          I("Gráficos de Contorno e Superfície", "✅"),
          I("Otimizador de Respostas", "✅")),
        I("Misturas"),
        I("Taguchi"),
        I("Modificar Planejamento", "🟡"),
        I("Exibir Planejamento", "✅")),
      N("Cartas de Controle",
        I("Transformação de Box-Cox", "🟡"),
        N("Cartas de Variáveis para Subgrupos",
          I("Xbarra-R", "✅", "xbar-r"),
          I("Xbarra-S", "✅"),
          I("Xbarra, R e S", "✅"),
          I("I-MR-R/S (Entre/Dentro)"),
          I("Carta de Zona")),
        N("Cartas de Variáveis para Individuais",
          I("I-MR", "✅", "imr"),
          I("Z-MR")),
        N("Cartas de Atributos",
          I("P", "✅", "attr:p"),
          I("NP", "✅", "attr:np"),
          I("C", "✅", "attr:c"),
          I("U", "✅", "attr:u"),
          I("P' de Laney", "✅", "attr:laney_p"),
          I("U' de Laney", "✅", "attr:laney_u")),
        N("Cartas Ponderadas no Tempo",
          I("Média Móvel"),
          I("EWMA", "✅"),
          I("CUSUM", "✅")),
        N("Cartas Multivariadas",
          I("T² de Hotelling", "✅"),
          I("Variância Generalizada"),
          I("MEWMA")),
        N("Cartas de Eventos Raros",
          I("Carta G", "✅"),
          I("Carta T", "✅"))),
      N("Ferramentas da Qualidade",
        I("Gráfico Sequencial", "🟡"),
        I("Gráfico de Pareto", "✅"),
        I("Causa e Efeito (Ishikawa)"),
        I("Identificação de Distribuição Individual", "🟡"),
        I("Transformação de Johnson", "🟡"),
        N("Análise de Capacidade",
          I("Normal", "✅", "capability"),
          I("Entre/Dentro"),
          I("Não Normal", "✅"),
          I("Múltiplas Variáveis", "🟡"),
          I("Binomial"),
          I("Poisson"),
          I("Sixpack de Capacidade", "✅")),
        I("Intervalos de Tolerância"),
        N("Estudo do Medidor",
          I("Gráfico Sequencial do Medidor", "🟡"),
          I("Linearidade e Tendência do Medidor", "✅"),
          I("R&R do Medidor (Cruzado)", "✅", "gage-rr"),
          I("R&R do Medidor (Aninhado)", "✅"),
          I("R&R do Medidor (Expandido)"),
          I("Estudo Tipo 1", "✅"),
          I("Estudo de Medição por Atributos", "🟡"),
          I("Análise de Concordância por Atributos", "✅")),
        N("Amostragem de Aceitação",
          I("Por Atributos", "✅"),
          I("Por Variáveis", "✅")),
        I("Carta Multi-Vari"),
        I("Gráfico de Simetria")),
      N("Confiabilidade/Sobrevivência",
        I("Identificação de Distribuição (censura)"),
        I("Gráfico Panorâmico da Distribuição"),
        I("Análise de Distribuição Paramétrica", "🟡"),
        I("Análise de Distribuição Não Paramétrica", "✅"),
        I("Censura Arbitrária"),
        I("Regressão com Dados de Vida", "🟡"),
        I("Modelo de Cox", "✅"),
        I("Teste de Vida Acelerada"),
        I("Análise Probit", "🟡"),
        I("Análise de Garantia"),
        I("Planos de Teste"),
        I("Sistemas Reparáveis")),
      N("Análise Preditiva",
        I("CART", "✅"),
        I("Florestas Aleatórias", "✅"),
        I("TreeNet", "✅"),
        I("MARS"),
        I("Aprendizado de Máquina Automatizado", "🟡")),
      N("Multivariada",
        I("Componentes Principais", "✅"),
        I("Análise Fatorial", "✅"),
        I("Análise de Itens", "✅"),
        I("Agrupar Observações", "✅"),
        I("Agrupar Variáveis", "🟡"),
        I("Agrupamento K-médias", "✅"),
        I("Análise Discriminante", "✅"),
        I("Análise de Correspondência Simples"),
        I("Análise de Correspondência Múltipla")),
      N("Séries Temporais",
        I("Gráfico de Série Temporal", "✅"),
        I("Análise de Tendência"),
        I("Decomposição"),
        I("Média Móvel"),
        I("Suavização Exponencial Simples"),
        I("Suavização Exponencial Dupla"),
        I("Método de Winters"),
        I("Diferenças e Defasagem", "🟡"),
        I("Autocorrelação e Autocorrelação Parcial", "✅"),
        I("Correlação Cruzada"),
        I("ARIMA", "✅"),
        I("Previsão com Melhor Modelo", "🟡")),
      N("Tabelas",
        I("Contagem de Variáveis Individuais", "✅"),
        I("Tabulação Cruzada e Qui-Quadrado", "✅"),
        I("Teste Qui-Quadrado de Associação", "✅"),
        I("Teste Qui-Quadrado de Aderência", "✅"),
        I("Estatísticas Descritivas em Tabela", "🟡")),
      N("Não Paramétricos",
        I("Teste do Sinal para 1 Amostra"),
        I("Wilcoxon para 1 Amostra", "✅"),
        I("Mann-Whitney", "✅"),
        I("Kruskal-Wallis", "✅"),
        I("Mediana de Mood"),
        I("Friedman", "✅"),
        I("Teste de Sequências"),
        I("Médias, Diferenças e Inclinações Pareadas")),
      N("Testes de Equivalência",
        I("Equivalência para 1 Amostra", "✅"),
        I("Equivalência para 2 Amostras", "✅"),
        I("Equivalência Pareada", "✅"),
        I("Crossover 2x2")),
      N("Poder e Tamanho Amostral",
        I("Z para 1 Amostra", "✅"),
        I("t para 1 Amostra", "✅"),
        I("t para 2 Amostras", "✅"),
        I("t Pareado", "✅"),
        I("1 Proporção", "✅"),
        I("2 Proporções", "✅"),
        I("Taxa de Poisson", "✅"),
        I("Variâncias", "✅"),
        I("Testes de Equivalência"),
        I("ANOVA com Um Fator"),
        I("Fatorial de 2 Níveis"),
        I("Plackett-Burman"),
        I("Fatorial Completo Geral"),
        I("Tamanho Amostral para Estimação"),
        I("Tamanho Amostral para Intervalos de Tolerância"))),
    N("Gráfico",
      I("Gráfico de Dispersão", "✅"),
      I("Gráfico de Matriz", "✅"),
      I("Gráfico de Bolhas", "✅"),
      I("Gráfico Marginal", "✅"),
      I("Histograma", "✅"),
      I("Gráfico de Pontos", "✅"),
      I("Ramo e Folhas", "✅"),
      I("Gráfico de Probabilidade", "🟡"),
      I("Função de Distribuição Empírica", "🟡"),
      I("Gráfico de Distribuição de Probabilidade", "✅"),
      I("Boxplot", "✅"),
      I("Gráfico de Intervalo", "✅"),
      I("Gráfico de Valores Individuais", "✅"),
      I("Gráfico de Linhas", "✅"),
      I("Gráfico de Barras", "✅"),
      I("Gráfico de Setores", "✅"),
      I("Gráfico de Série Temporal", "✅"),
      I("Gráfico de Área", "🟡"),
      I("Gráfico de Contorno", "🟡"),
      I("Gráfico de Dispersão 3D"),
      I("Gráfico de Superfície 3D", "🟡"),
      I("Mapa de Calor", "🟡"),
      I("Gráfico de Dispersão Agrupado"),
      I("Gráfico de Coordenadas Paralelas")),
]


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower().replace("²", "2")).strip("-")


def _assign(node: Node, prefix: str, trail: tuple[str, ...], index: dict) -> None:
    for child in node.children:
        child.path = f"{prefix}/{slugify(child.label)}"
        if isinstance(child, Node):
            _assign(child, child.path, trail + (child.label,), index)
        else:
            child.trail = trail + (child.label,)
            if child.path in index:
                raise ValueError(f"Caminho repetido no menu: {child.path}")
            index[child.path] = child


ITEMS: dict[str, Item] = {}  # caminho da URL -> item
for _menu in MENU:
    _menu.path = f"/{slugify(_menu.label)}"
    _assign(_menu, _menu.path, (_menu.label,), ITEMS)
