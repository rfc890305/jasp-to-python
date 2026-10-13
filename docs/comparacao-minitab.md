# Comparação Minitab × JASP × jasp-to-python

Matriz inicial, a ser detalhada análise por análise. A coluna JASP indica o que precisa ser
**migrado**; onde ela for "Não", a funcionalidade precisa ser **desenvolvida** do zero.

Legenda: ✅ disponível · 🟡 parcial · ⬜ ausente · ❓ a verificar

| Área (menu do Minitab) | Funcionalidade | JASP | Este projeto |
|---|---|---|---|
| Estatística básica | Descritivas, testes t, proporções, normalidade | ✅ | 🟡 descritivas |
| Estatística básica | Testes de variância (F, Levene, Bartlett) | ✅ | ⬜ |
| Regressão | Linear, logística, melhores subconjuntos | ✅ | ⬜ |
| ANOVA | Um e dois fatores, modelo linear geral | ✅ | ⬜ |
| DOE | Fatorial, superfície de resposta | ✅ | ⬜ |
| DOE | Misturas, Taguchi | ❓ | ⬜ |
| Cartas de controle | I-MR, Xbarra-R, Xbarra-S | ✅ | 🟡 I-MR, Xbarra-R |
| Cartas de controle | p, np, c, u, Laney P'/U' | ✅ | ⬜ |
| Cartas de controle | EWMA, CUSUM | ✅ | ⬜ |
| Ferramentas da qualidade | Capacidade normal | ✅ | 🟡 |
| Ferramentas da qualidade | Capacidade não normal, Box-Cox, Johnson | ❓ | ⬜ |
| Ferramentas da qualidade | Gauge R&R, linearidade/viés, tipo 1 | ✅ | ⬜ |
| Ferramentas da qualidade | Concordância por atributos | ✅ | ⬜ |
| Ferramentas da qualidade | Pareto, causa e efeito (Ishikawa) | ❓ | ⬜ |
| Ferramentas da qualidade | Multi-vari, run chart | ❓ | ⬜ |
| Ferramentas da qualidade | Amostragem de aceitação | ❓ | ⬜ |
| Ferramentas da qualidade | Intervalos de tolerância | ❓ | ⬜ |
| Confiabilidade | Análise de distribuição, Weibull | ❓ | ⬜ |
| Poder e tamanho de amostra | Testes t, proporções, ANOVA, DOE | ❓ | ⬜ |
| Séries temporais | Tendência, decomposição, ARIMA | ✅ | ⬜ |
| Assistente | Fluxos guiados por fase do DMAIC | ⬜ | ⬜ |
