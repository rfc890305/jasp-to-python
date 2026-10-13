# Comparação Minitab × JASP × jasp-to-python

Matriz item a item dos menus **Calc**, **Estat** e **Gráfico** do Minitab (versão em português).
A coluna JASP diz o que pode ser **migrado**; onde ela for ⬜, a funcionalidade precisa ser
**desenvolvida** do zero em Python.

Legenda: ✅ existe · 🟡 parcial · ⬜ não existe

**Como a coluna JASP foi verificada (2026-10-13):** pelos menus (`inst/Description.qml`) e
pelas opções das telas (`inst/qml/*.qml`) dos módulos oficiais em
<https://github.com/jasp-stats>. Os itens de **Calc** dependem do editor de dados do próprio
JASP (colunas calculadas com R ou com o construtor visual), e não de um módulo.

**Nomes dos menus:** seguem a documentação pública do Minitab 21/22 em português. Podem mudar
um pouco entre versões; conferir com as capturas de tela da versão instalada.

Coluna "Onde no JASP" usa o formato `módulo › análise`.

## Resumo

| Menu | Itens | ✅ JASP | 🟡 parcial | ⬜ desenvolver |
|---|---|---|---|---|
| Calc | 11 | 1 | 9 | 1 |
| Estat | 181 | 95 | 31 | 55 |
| Gráfico | 24 | 15 | 6 | 3 |
| **Total** | **216** | **111** | **46** | **59** |

Lacunas que mais pesam num projeto Six Sigma (prioridade para desenvolver):

1. Capacidade para atributos (binomial e Poisson) e capacidade entre/dentro.
2. Intervalos de tolerância.
3. Diagrama de causa e efeito (Ishikawa), carta multi-vari e gráfico sequencial (run chart) isolado.
4. Taguchi e misturas no DOE; poder e tamanho de amostra para ANOVA e fatoriais.
5. Cartas I-MR-R/S, Z-MR, zona, média móvel, MEWMA e variância generalizada.
6. Teste de 2 variâncias e de 1 variância, teste de outlier, Mood e sinal (não paramétricos).
7. Análise de médias (ANOM).
8. Suavização exponencial, Winters, decomposição e análise de tendência.
9. Confiabilidade: identificação de distribuição com censura, vida acelerada, garantia.

## Calc

| Funcionalidade (Minitab) | JASP | Onde no JASP | Este projeto |
|---|---|---|---|
| Calculadora | 🟡 | Coluna calculada (R ou construtor visual) | ⬜ |
| Estatísticas de Colunas | 🟡 | jaspDescriptives › Descriptive Statistics (não grava em coluna) | 🟡 `describe` |
| Estatísticas de Linhas | 🟡 | Coluna calculada com R | ⬜ |
| Padronizar | 🟡 | Coluna calculada (`scale`) | ⬜ |
| Criar Dados Padronizados (sequências) | 🟡 | Coluna calculada com R (`rep`, `seq`) | ⬜ |
| Criar Dados em Malha | ⬜ | | ⬜ |
| Criar Variáveis Indicadoras | 🟡 | Modelos tratam fatores automaticamente; coluna calculada com R | ⬜ |
| Definir Base (semente) | 🟡 | Opção de semente em cada análise | ⬜ |
| Dados Aleatórios (todas as distribuições) | 🟡 | Coluna calculada com R (`rnorm`, `rbinom`...) | ⬜ |
| Distribuições de Probabilidade (PDF, CDF, inversa, gráfico) | ✅ | jaspDistributions (31 contínuas, 10 discretas) | ⬜ |
| Matrizes | 🟡 | Apenas via R; sem interface | ⬜ |

## Estat

### Estatísticas Básicas

| Funcionalidade (Minitab) | JASP | Onde no JASP | Este projeto |
|---|---|---|---|
| Exibir Estatísticas Descritivas | ✅ | jaspDescriptives › Descriptive Statistics | 🟡 `describe` |
| Armazenar Estatísticas Descritivas | 🟡 | Mostra, mas não grava em colunas | ⬜ |
| Resumo Gráfico | 🟡 | Descriptives (histograma, boxplot, IC) sem painel único nem Anderson-Darling | ⬜ |
| Z para 1 Amostra | ✅ | jaspTTests › One Sample T-Test (opção Z Test) | ⬜ |
| t para 1 Amostra | ✅ | jaspTTests › One Sample T-Test | ⬜ |
| t para 2 Amostras | ✅ | jaspTTests › Independent Samples T-Test (Student, Welch) | ⬜ |
| t Pareado | ✅ | jaspTTests › Paired Samples T-Test | ⬜ |
| 1 Proporção | ✅ | jaspFrequencies › Binomial Test | ⬜ |
| 2 Proporções | 🟡 | jaspFrequencies › Contingency Tables (qui-quadrado, Fisher); sem IC da diferença | ⬜ |
| Taxa de Poisson de 1 Amostra | ⬜ | Só no módulo de poder | ⬜ |
| Taxa de Poisson de 2 Amostras | ⬜ | Só no módulo de poder | ⬜ |
| 1 Variância | 🟡 | Descriptives dá IC da variância; sem teste | ⬜ |
| 2 Variâncias | 🟡 | Levene e Brown-Forsythe dentro do teste t; sem teste F nem análise própria | ⬜ |
| Correlação | ✅ | jaspRegression › Correlation (Pearson, Spearman, Kendall) | ⬜ |
| Covariância | ✅ | jaspDescriptives › Descriptive Statistics (matriz de covariância) | ⬜ |
| Teste de Normalidade | ✅ | Shapiro-Wilk em Descriptives; Anderson-Darling e KS em jaspDistributions | ⬜ |
| Teste de Outlier (Grubbs, Dixon) | ⬜ | | ⬜ |
| Teste de Aderência para Poisson | 🟡 | jaspDistributions › Poisson (ajuste com qui-quadrado) | ⬜ |

### Regressão

| Funcionalidade (Minitab) | JASP | Onde no JASP | Este projeto |
|---|---|---|---|
| Ajustar Modelo de Regressão | ✅ | jaspRegression › Linear Regression | ⬜ |
| Regressão Stepwise | ✅ | Linear Regression (forward, backward, stepwise) | ⬜ |
| Melhores Subconjuntos | ⬜ | | ⬜ |
| Previsão / Otimizador de Respostas da regressão | 🟡 | Previsão via ML › Prediction; otimizador só no DOE | ⬜ |
| Gráfico de Linha Ajustada (linear, quadrático, cúbico) | 🟡 | Descriptives › Scatter plots (reta e suavização) | ⬜ |
| Regressão Não Linear | ⬜ | | ⬜ |
| Regressão Ortogonal | ⬜ | | ⬜ |
| Mínimos Quadrados Parciais (PLS) | 🟡 | jaspSem › Partial Least Squares SEM (não é a PLS de regressão) | ⬜ |
| Regressão Logística Binária | ✅ | jaspRegression › Logistic Regression | ⬜ |
| Regressão Logística Ordinal | ⬜ | | ⬜ |
| Regressão Logística Nominal | 🟡 | jaspMachineLearning › Logistic / Multinomial Classification | ⬜ |
| Regressão de Poisson | ✅ | jaspRegression › Generalized Linear Model | ⬜ |
| Estudo de Estabilidade (prazo de validade) | ⬜ | | ⬜ |

### ANOVA

| Funcionalidade (Minitab) | JASP | Onde no JASP | Este projeto |
|---|---|---|---|
| ANOVA com Um Fator (Tukey, Fisher, Dunnett, Games-Howell, Welch) | ✅ | jaspAnova › ANOVA | ⬜ |
| Análise de Médias (ANOM) | ⬜ | | ⬜ |
| ANOVA Balanceada | ✅ | jaspAnova › ANOVA | ⬜ |
| Modelo Linear Geral | ✅ | jaspAnova › ANOVA / ANCOVA | ⬜ |
| Modelo Misto | ✅ | jaspMixedModels › Linear Mixed Models | ⬜ |
| ANOVA Totalmente Aninhada | 🟡 | Via Linear Mixed Models | ⬜ |
| MANOVA Geral | ✅ | jaspAnova › MANOVA | ⬜ |
| Teste para Variâncias Iguais | 🟡 | Levene e Brown-Forsythe dentro da ANOVA; sem Bartlett nem comparações múltiplas | ⬜ |
| Gráfico de Intervalo | ✅ | jaspDescriptives › Interval plots | ⬜ |
| Gráfico de Efeitos Principais | ✅ | jaspAnova › Descriptives plots | ⬜ |
| Gráfico de Interação | ✅ | jaspAnova › Descriptives plots (linhas separadas) | ⬜ |
| ANOVA de Medidas Repetidas | ✅ | jaspAnova › Repeated Measures ANOVA | ⬜ |

### DOE (Planejamento de Experimentos)

| Funcionalidade (Minitab) | JASP | Onde no JASP | Este projeto |
|---|---|---|---|
| Triagem: Plackett-Burman | 🟡 | jaspQualityControl tem `doeScreening.qml`, ainda fora do menu | ⬜ |
| Triagem: Triagem Definitiva | 🟡 | `definitiveScreeningAnalysis.qml`, ainda fora do menu | ⬜ |
| Fatorial: Criar 2 níveis (padrão e geradores) | ✅ | jaspQualityControl › Create Factorial Worksheet | ✅ `factorial_design` |
| Fatorial: Fatorial completo geral | ✅ | Create Factorial Worksheet | ⬜ |
| Fatorial: Parcelas subdivididas (split-plot) | ✅ | Create Factorial Worksheet | ⬜ |
| Fatorial: Definir planejamento personalizado | 🟡 | Analyse Design aceita colunas existentes | ⬜ |
| Fatorial: Analisar Planejamento | ✅ | jaspQualityControl › Analyse Design | 🟡 `analyze_design` (sem blocos/covariáveis) |
| Fatorial: Gráfico de Pareto e normal dos efeitos | ✅ | Analyse Design | 🟡 Pareto (com Lenth) |
| Fatorial: Gráficos fatoriais (efeitos, interação, cubo) | ⬜ | | ⬜ |
| Superfície de Resposta: Composto Central (CCD) | ✅ | Create Response Surface Worksheet | ✅ `central_composite_design` |
| Superfície de Resposta: Box-Behnken | ✅ | Create Response Surface Worksheet | ✅ `box_behnken_design` |
| Superfície de Resposta: Analisar | ✅ | Analyse Design | 🟡 `analyze_design(model="quadratic")` com ponto estacionário |
| Gráficos de Contorno e Superfície | ✅ | Analyse Design | ⬜ |
| Otimizador de Respostas (desejabilidade) | ✅ | Analyse Design › Response optimizer | ⬜ |
| Misturas (simplex, vértices extremos) | ⬜ | | ⬜ |
| Taguchi | ⬜ | | ⬜ |
| Modificar Planejamento | 🟡 | `doeModifyDesign.qml`, ainda fora do menu | ⬜ |
| Exibir Planejamento (codificado/não codificado) | ✅ | Analyse Design (unidades codificadas) | ⬜ |

### Cartas de Controle

| Funcionalidade (Minitab) | JASP | Onde no JASP | Este projeto |
|---|---|---|---|
| Transformação de Box-Cox | 🟡 | Só dentro de Process Capability Study | ⬜ |
| Xbarra-R | ✅ | jaspQualityControl › Variables Charts for Subgroups | ✅ `xbar_r_chart` |
| Xbarra-S | ✅ | Variables Charts for Subgroups | ⬜ |
| Xbarra, R e S isoladas | ✅ | Variables Charts for Subgroups | 🟡 |
| I-MR-R/S (entre/dentro) | ⬜ | | ⬜ |
| Carta de Zona | ⬜ | | ⬜ |
| I-MR | ✅ | jaspQualityControl › Variables Charts for Individuals (inclui autocorrelação) | ✅ `imr_chart` |
| Z-MR | ⬜ | | ⬜ |
| P | ✅ | jaspQualityControl › Control Charts for Attributes | ✅ `p_chart` |
| NP | ✅ | Control Charts for Attributes | ✅ `np_chart` |
| C | ✅ | Control Charts for Attributes | ✅ `c_chart` |
| U | ✅ | Control Charts for Attributes | ✅ `u_chart` |
| P' de Laney | ✅ | Control Charts for Attributes | ✅ `laney_p_chart` |
| U' de Laney | ✅ | Control Charts for Attributes | ✅ `laney_u_chart` |
| Média Móvel (MA) | ⬜ | | ⬜ |
| EWMA | ✅ | jaspQualityControl › Time Weighted Charts | ⬜ |
| CUSUM | ✅ | Time Weighted Charts | ⬜ |
| T² de Hotelling | ✅ | jaspQualityControl › Multivariate Control Charts | ⬜ |
| Variância Generalizada | ⬜ | | ⬜ |
| MEWMA | ⬜ | | ⬜ |
| Carta G | ✅ | jaspQualityControl › Rare Event Charts | ⬜ |
| Carta T | ✅ | Rare Event Charts | ⬜ |
| Testes de causas especiais (8 regras) | ✅ | Todas as cartas (testes 1 a 9) | 🟡 regras 1 a 3 |
| Estágios (fases históricas) | ✅ | Todas as cartas por variáveis e atributos | ⬜ |

### Ferramentas da Qualidade

| Funcionalidade (Minitab) | JASP | Onde no JASP | Este projeto |
|---|---|---|---|
| Gráfico Sequencial (run chart) | 🟡 | Só dentro de MSA Type 1 e Test-retest | ⬜ |
| Gráfico de Pareto | ✅ | jaspDescriptives › Pareto plots | ⬜ |
| Causa e Efeito (Ishikawa) | ⬜ | | ⬜ |
| Identificação de Distribuição Individual | 🟡 | jaspDistributions › Compare Continuous Distributions (sem Box-Cox/Johnson juntos) | ⬜ |
| Transformação de Johnson | 🟡 | Só dentro de Process Capability Study | ⬜ |
| Capacidade Normal | ✅ | jaspQualityControl › Process Capability Study | 🟡 `capability_analysis` |
| Capacidade Entre/Dentro | ⬜ | | ⬜ |
| Capacidade Não Normal (Weibull, lognormal, gama, Box-Cox, Johnson...) | ✅ | Process Capability Study | ⬜ |
| Capacidade de Múltiplas Variáveis | 🟡 | Uma análise por variável | ⬜ |
| Capacidade Binomial | ⬜ | | ⬜ |
| Capacidade de Poisson | ⬜ | | ⬜ |
| Sixpack de Capacidade | ✅ | Process Capability Study › Show Report | ⬜ |
| Intervalos de Tolerância | ⬜ | | ⬜ |
| Gráfico Sequencial do Medidor | 🟡 | Run chart dentro de Type 1 / Test-retest | ⬜ |
| Linearidade e Tendência do Medidor | ✅ | jaspQualityControl › Type 4 Linearity Study | ⬜ |
| R&R do Medidor (Cruzado) | ✅ | Type 2 and 3 Gauge r&R Study | ✅ `gauge_rr_crossed` |
| R&R do Medidor (Aninhado) | ✅ | Gauge r&R Study (Non-replicable Measurements) | ⬜ |
| R&R do Medidor (Expandido) | ⬜ | | ⬜ |
| Estudo Tipo 1 | ✅ | Type 1 Instrument Capability Study | ⬜ |
| Estudo de Medição por Atributos (Método Analítico) | 🟡 | Probability of Detection (abordagem parecida) | ⬜ |
| Análise de Concordância por Atributos | ✅ | Attributes Agreement Analysis (kappa de Cohen e Fleiss, Kendall) | ⬜ |
| Criar/Comparar Plano de Amostragem por Atributos | ✅ | jaspAcceptanceSampling › Create / Analyze Attribute Plan | ⬜ |
| Amostragem de Aceitação por Variáveis | ✅ | jaspAcceptanceSampling › Variable Sampling (incl. aceitar/rejeitar lotes) | ⬜ |
| Carta Multi-Vari | ⬜ | | ⬜ |
| Gráfico de Simetria | ⬜ | | ⬜ |

### Confiabilidade/Sobrevivência

| Funcionalidade (Minitab) | JASP | Onde no JASP | Este projeto |
|---|---|---|---|
| Gráfico de Identificação de Distribuição (censura) | ⬜ | | ⬜ |
| Gráfico Panorâmico da Distribuição | ⬜ | | ⬜ |
| Análise de Distribuição Paramétrica (Weibull etc.) | 🟡 | jaspSurvival › Parametric Survival Analysis | ⬜ |
| Análise de Distribuição Não Paramétrica (Kaplan-Meier) | ✅ | jaspSurvival › Non-parametric Survival Analysis | ⬜ |
| Censura arbitrária (intervalar) | ⬜ | | ⬜ |
| Regressão com Dados de Vida | 🟡 | Parametric Survival Analysis com covariáveis | ⬜ |
| Modelo de Cox | ✅ | jaspSurvival › Semi-parametric Survival Analysis | ⬜ |
| Teste de Vida Acelerada | ⬜ | | ⬜ |
| Análise Probit | 🟡 | jaspRegression › Generalized Linear Model (link probit) | ⬜ |
| Análise de Garantia | ⬜ | | ⬜ |
| Planos de Teste (demonstração, estimação) | ⬜ | | ⬜ |
| Sistemas Reparáveis | ⬜ | | ⬜ |

### Análise Preditiva (aprendizado de máquina)

| Funcionalidade (Minitab) | JASP | Onde no JASP | Este projeto |
|---|---|---|---|
| CART (regressão e classificação) | ✅ | jaspMachineLearning › Decision Tree | ⬜ |
| Florestas Aleatórias | ✅ | jaspMachineLearning › Random Forest | ⬜ |
| TreeNet (boosting) | ✅ | jaspMachineLearning › Boosting | ⬜ |
| MARS | ⬜ | | ⬜ |
| Aprendizado de Máquina Automatizado (comparar modelos) | 🟡 | Cada modelo roda separado | ⬜ |

### Multivariada

| Funcionalidade (Minitab) | JASP | Onde no JASP | Este projeto |
|---|---|---|---|
| Componentes Principais | ✅ | jaspFactor › Principal Component Analysis | ⬜ |
| Análise Fatorial | ✅ | jaspFactor › Exploratory / Confirmatory Factor Analysis | ⬜ |
| Análise de Itens (alfa de Cronbach) | ✅ | jaspReliability › Reliability | ⬜ |
| Agrupar Observações (hierárquico) | ✅ | jaspMachineLearning › Hierarchical Clustering | ⬜ |
| Agrupar Variáveis | 🟡 | Hierarchical Clustering (feito para observações) | ⬜ |
| Agrupamento K-médias | ✅ | jaspMachineLearning › Neighborhood-Based Clustering | ⬜ |
| Análise Discriminante | ✅ | jaspMachineLearning › Linear Discriminant | ⬜ |
| Análise de Correspondência Simples | ⬜ | | ⬜ |
| Análise de Correspondência Múltipla | ⬜ | | ⬜ |

### Séries Temporais

| Funcionalidade (Minitab) | JASP | Onde no JASP | Este projeto |
|---|---|---|---|
| Gráfico de Série Temporal | ✅ | jaspTimeSeries › Time Series Descriptives | ⬜ |
| Análise de Tendência | ⬜ | | ⬜ |
| Decomposição | ⬜ | | ⬜ |
| Média Móvel | ⬜ | | ⬜ |
| Suavização Exponencial Simples | ⬜ | | ⬜ |
| Suavização Exponencial Dupla (Holt) | ⬜ | | ⬜ |
| Método de Winters | ⬜ | | ⬜ |
| Diferenças e Defasagem | 🟡 | jaspTimeSeries › Stationarity (diferenciação) | ⬜ |
| Autocorrelação e Autocorrelação Parcial | ✅ | Time Series Descriptives / Stationarity | ⬜ |
| Correlação Cruzada | ⬜ | | ⬜ |
| ARIMA | ✅ | jaspTimeSeries › ARIMA | ⬜ |
| Previsão com Melhor Modelo | 🟡 | ARIMA e jaspProphet › Prophet, sem comparação automática | ⬜ |
| Análise Espectral | ✅ | jaspTimeSeries › Spectral Analysis (não existe no Minitab) | ⬜ |

### Tabelas

| Funcionalidade (Minitab) | JASP | Onde no JASP | Este projeto |
|---|---|---|---|
| Contagem de Variáveis Individuais | ✅ | jaspDescriptives › Frequency tables | ⬜ |
| Tabulação Cruzada e Qui-Quadrado | ✅ | jaspFrequencies › Contingency Tables | ⬜ |
| Teste Qui-Quadrado de Associação | ✅ | Contingency Tables (inclui Fisher e McNemar) | ⬜ |
| Teste Qui-Quadrado de Aderência (uma variável) | ✅ | jaspFrequencies › Multinomial Test | ⬜ |
| Estatísticas Descritivas em Tabela | 🟡 | Descriptives com split por fator | ⬜ |

### Não Paramétricos

| Funcionalidade (Minitab) | JASP | Onde no JASP | Este projeto |
|---|---|---|---|
| Teste do Sinal para 1 Amostra | ⬜ | | ⬜ |
| Wilcoxon para 1 Amostra | ✅ | jaspTTests › One Sample T-Test (Wilcoxon signed-rank) | ⬜ |
| Mann-Whitney | ✅ | jaspTTests › Independent Samples T-Test (inclui Hodges-Lehmann) | ⬜ |
| Kruskal-Wallis | ✅ | jaspAnova › ANOVA › Nonparametrics | ⬜ |
| Mediana de Mood | ⬜ | | ⬜ |
| Friedman | ✅ | jaspAnova › Repeated Measures ANOVA | ⬜ |
| Teste de Sequências (runs) | ⬜ | | ⬜ |
| Médias, Diferenças e Inclinações Pareadas (Walsh) | ⬜ | | ⬜ |

### Testes de Equivalência

| Funcionalidade (Minitab) | JASP | Onde no JASP | Este projeto |
|---|---|---|---|
| Equivalência para 1 Amostra | ✅ | jaspEquivalenceTTests › One Sample T-Test | ⬜ |
| Equivalência para 2 Amostras | ✅ | jaspEquivalenceTTests › Independent Samples T-Test | ⬜ |
| Equivalência Pareada | ✅ | jaspEquivalenceTTests › Paired Samples T-Test | ⬜ |
| Crossover 2x2 | ⬜ | | ⬜ |

### Poder e Tamanho Amostral

| Funcionalidade (Minitab) | JASP | Onde no JASP | Este projeto |
|---|---|---|---|
| Z para 1 Amostra | ✅ | jaspPower › Power | ⬜ |
| t para 1 Amostra | ✅ | jaspPower › Power | ⬜ |
| t para 2 Amostras | ✅ | jaspPower › Power | ⬜ |
| t Pareado | ✅ | jaspPower › Power | ⬜ |
| 1 Proporção | ✅ | jaspPower › Power | ⬜ |
| 2 Proporções | ✅ | jaspPower › Power | ⬜ |
| Taxa de Poisson de 1 e 2 Amostras | ✅ | jaspPower › Power | ⬜ |
| 1 Variância e 2 Variâncias | ✅ | jaspPower › Power | ⬜ |
| Testes de Equivalência | ⬜ | | ⬜ |
| ANOVA com Um Fator | ⬜ | | ⬜ |
| Fatorial de 2 Níveis | ⬜ | | ⬜ |
| Plackett-Burman | ⬜ | | ⬜ |
| Fatorial Completo Geral | ⬜ | | ⬜ |
| Tamanho Amostral para Estimação | ⬜ | | ⬜ |
| Tamanho Amostral para Intervalos de Tolerância | ⬜ | | ⬜ |

## Gráfico

| Funcionalidade (Minitab) | JASP | Onde no JASP | Este projeto |
|---|---|---|---|
| Gráfico de Dispersão | ✅ | jaspDescriptives › Scatter plots / Plot Builder | ⬜ |
| Gráfico de Matriz | ✅ | jaspDescriptives › Correlation plots | ⬜ |
| Gráfico de Bolhas | ✅ | jaspDescriptives › Plot Builder (tamanho do ponto por variável) | ⬜ |
| Gráfico Marginal | ✅ | Scatter plots (gráfico acima e à direita) | ⬜ |
| Histograma | ✅ | jaspDescriptives › Distribution plots | ⬜ |
| Gráfico de Pontos (dotplot) | ✅ | jaspDescriptives › Dot plots | ⬜ |
| Ramo e Folhas | ✅ | jaspDescriptives › Stem and leaf tables | ⬜ |
| Gráfico de Probabilidade | 🟡 | Q-Q normal em Descriptives; outras distribuições em jaspDistributions | ⬜ |
| Gráfico da Função de Distribuição Empírica (ECDF) | 🟡 | jaspDistributions (dentro do ajuste de distribuição) | ⬜ |
| Gráfico de Distribuição de Probabilidade | ✅ | jaspDistributions | ⬜ |
| Boxplot | ✅ | jaspDescriptives › Boxplots | ⬜ |
| Gráfico de Intervalo | ✅ | jaspDescriptives › Interval plots | ⬜ |
| Gráfico de Valores Individuais | ✅ | Boxplots com elemento jitter / Raincloud Plots | ⬜ |
| Gráfico de Linhas | ✅ | jaspDescriptives › Plot Builder | ⬜ |
| Gráfico de Barras | ✅ | Descriptives (frequências) / Plot Builder | ⬜ |
| Gráfico de Setores (pizza) | ✅ | jaspDescriptives › Pie charts | ⬜ |
| Gráfico de Série Temporal | ✅ | jaspTimeSeries › Time Series Descriptives | ⬜ |
| Gráfico de Área | 🟡 | Plot Builder (área empilhada) | ⬜ |
| Gráfico de Contorno | 🟡 | Só para modelos do DOE | ⬜ |
| Gráfico de Dispersão 3D | ⬜ | | ⬜ |
| Gráfico de Superfície 3D | 🟡 | Só para modelos do DOE | ⬜ |
| Mapa de Calor | 🟡 | jaspDescriptives › Tile heatmaps (duas variáveis categóricas e um valor) | ⬜ |
| Gráfico de Dispersão Agrupado (binned) | ⬜ | | ⬜ |
| Gráfico de Coordenadas Paralelas | ⬜ | | ⬜ |

## O que o JASP tem e o Minitab não

Vale manter na migração, mesmo sem equivalente no Minitab: estatística bayesiana em quase todos
os testes, ANOVA e regressão bayesianas, meta-análise, modelagem de equações estruturais (SEM),
análise de redes, estatística circular, auditoria (lei de Benford), amostragem de aceitação
bayesiana e o módulo didático Learn Stats.
