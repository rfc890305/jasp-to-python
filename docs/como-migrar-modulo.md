# Como migrar um módulo do JASP

1. **Clonar só o módulo estatístico** (não é preciso o código C++ da interface):

   ```bash
   mkdir -p vendor && cd vendor
   git clone --depth 1 https://github.com/jasp-stats/jaspQualityControl   # Six Sigma
   git clone --depth 1 https://github.com/jasp-stats/jaspDescriptives     # descritivas
   ```

   A pasta `vendor/` está no `.gitignore`: o código R é referência, não faz parte deste repositório.

2. **Localizar o cálculo** em `R/` do módulo. Separe o que é matemática do que é interface
   do JASP (`createJaspTable`, `createJaspPlot`, `jaspResults`, opções do QML) e migre só a matemática.

3. **Converter para Python** em `backend/<area>/<analise>.py`, usando apenas pandas, NumPy,
   SciPy e statsmodels. A função recebe dados e parâmetros e devolve `dict` ou `DataFrame`.
   Prompt sugerido para usar com IA:

   > Atue como engenheiro de dados e estatístico sênior. Este script R pertence ao backend do JASP.
   > Converta a lógica matemática, o tratamento de dados e os cálculos para Python usando apenas
   > pandas, NumPy, SciPy e statsmodels. Remova as funções de interface do JASP e retorne
   > dicionários ou DataFrames com os resultados numéricos.

4. **Validar** em `tests/`: rode a mesma análise no JASP (e, se possível, no Minitab) com um
   conjunto de dados de `data/` e fixe os valores esperados no teste.

5. **Documentar** no manual (`docs/manual/`) e atualizar o status em `docs/roadmap.md`.

6. **Expor na interface** (`app.py`) quando fizer sentido.
