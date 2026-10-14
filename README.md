# jasp-to-python

Migração das análises estatísticas do [JASP](https://github.com/jasp-stats) (R) para Python,
com foco em aplicações Six Sigma e em cobrir as funcionalidades do Minitab.

Objetivos do projeto:

1. **Migrar** a lógica de cálculo dos módulos R do JASP para Python puro
   (pandas, NumPy, SciPy, statsmodels).
2. **Documentar** cada funcionalidade num manual com aplicação no ciclo DMAIC.
3. **Comparar** com o Minitab e desenvolver o que estiver faltando.

## Estrutura

```
app.py                  Interface web (Dash + Tailwind CSS), expõe `server` para o gunicorn
menu.py                 Menus Calc, Estat e Gráfico no estilo do Minitab (o que tem tela e o que está "em breve")
backend/                Cálculos estatísticos puros, sem dependência de interface
  descriptives.py       Estatística descritiva (jaspDescriptives)
  quality/              Controle de qualidade / Six Sigma (jaspQualityControl)
    capability.py       Cp, Cpk, Pp, Ppk, Cpm, PPM, nível sigma
    control_charts.py   Cartas I-MR e Xbarra-R, regras de Nelson
    attribute_charts.py Cartas p, np, c, u e p'/u' de Laney
    msa.py              Gage R&R cruzado (ANOVA)
    doe.py              Criação (fatorial, CCD, Box-Behnken) e análise de experimentos
    constants.py        Constantes d2, A2, D3, D4
tests/                  Testes (pytest) com valores calculados à mão ou dos testes do JASP
  data/jasp/            Dados de referência copiados do jaspQualityControl
data/                   Conjuntos de dados de exemplo
docs/
  roadmap.md            Mapa de módulos JASP → Python e status
  como-migrar-modulo.md Passo a passo para converter um arquivo R do JASP
  manual/               Manual das funcionalidades com aplicação Six Sigma
  comparacao-minitab.md Matriz Minitab × JASP × este projeto
  deploy-cloud-run.md   Publicação no Google Cloud Run
scripts/gcp-setup.sh    Configuração única do Google Cloud para o deploy
Dockerfile              Imagem para o Google Cloud Run
```

## Rodando localmente

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest            # testes do backend
python app.py     # http://localhost:8050
```

## Deploy no Cloud Run

O deploy é automático pelo GitHub Actions a cada push na `main`, depois de uma
configuração única no Google Cloud. Passo a passo em
[docs/deploy-cloud-run.md](docs/deploy-cloud-run.md).

Deploy manual, direto do Cloud Shell:

```bash
gcloud run deploy jasp-to-python --source . --region southamerica-east1 --allow-unauthenticated --memory 1Gi
```

O `Dockerfile` usa `gunicorn app:server` e respeita a variável `PORT` definida pelo Cloud Run.

## Convenções

- O `backend/` nunca importa Dash: funções recebem dados e devolvem `dict`/`DataFrame`.
- Toda função migrada cita o arquivo R de origem no docstring e tem teste em `tests/`.
- Sempre que possível, os testes comparam com valores de referência do JASP ou do Minitab.
