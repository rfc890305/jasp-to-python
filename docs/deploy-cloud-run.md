# Publicação no Google Cloud Run

O app roda no Cloud Run a partir do `Dockerfile` da raiz (`gunicorn app:server`,
porta `$PORT`). O deploy é feito pelo GitHub Actions
(`.github/workflows/deploy-cloud-run.yml`) a cada push na `main`, ou manualmente
pela aba **Actions › Deploy Cloud Run › Run workflow**.

A autenticação usa **Workload Identity Federation**: o GitHub recebe um token
temporário do Google a cada execução, então nenhuma chave JSON fica guardada no
repositório nem nos secrets.

Enquanto a variável `GCP_WIF_PROVIDER` não for cadastrada, o workflow de deploy é
ignorado (não falha).

## O que você precisa ter

| Item | Valor sugerido | Observação |
|---|---|---|
| Projeto no Google Cloud | `jasp-to-pyhton` | com faturamento ativado (o Cloud Run tem cota gratuita mensal); é o padrão do script e do workflow |
| Região | `southamerica-east1` (São Paulo) | pode trocar pela variável `GCP_REGION` |
| Nome do serviço | `jasp-to-python` | opcional: variável `CLOUD_RUN_SERVICE` |
| Repositório de imagens | `jasp-to-python` (Artifact Registry) | opcional: variável `GAR_REPOSITORY` |

## Passo 1: configurar o Google Cloud (uma vez)

1. Abra o [Cloud Shell](https://shell.cloud.google.com) logado com a conta dona do projeto.
2. Rode:

   ```bash
   git clone https://github.com/rfc890305/jasp-to-python.git
   cd jasp-to-python
   bash scripts/gcp-setup.sh   # usa o projeto jasp-to-pyhton
   ```

O script [`scripts/gcp-setup.sh`](../scripts/gcp-setup.sh) faz o seguinte (e pode
ser rodado de novo sem problemas):

- ativa as APIs do Cloud Run, Artifact Registry, IAM Credentials e STS;
- cria o repositório Docker no Artifact Registry;
- cria a conta de serviço `github-deployer` com os papéis
  `roles/run.admin`, `roles/artifactregistry.writer` e
  `roles/iam.serviceAccountUser` (sobre a conta padrão do Compute que executa o serviço);
- cria o pool e o provedor de Workload Identity para o GitHub, aceitando
  **somente** tokens do repositório `rfc890305/jasp-to-python`.

No final ele imprime os quatro valores do passo 2.

## Passo 2: cadastrar as variáveis no GitHub

Em **Settings › Secrets and variables › Actions › Variables** do repositório,
crie (são *variables*, não *secrets*, porque nenhum desses valores é sigiloso):

| Variável | Exemplo |
|---|---|
| `GCP_PROJECT_ID` | `jasp-to-pyhton` |
| `GCP_REGION` | `southamerica-east1` |
| `GCP_WIF_PROVIDER` | `projects/<número do projeto>/locations/global/workloadIdentityPools/github/providers/github` |
| `GCP_DEPLOY_SA` | `github-deployer@jasp-to-pyhton.iam.gserviceaccount.com` |

## Passo 3: publicar

Vá em **Actions › Deploy Cloud Run › Run workflow** (ou faça um merge na `main`).
O workflow:

1. roda os testes (`pytest`);
2. monta a imagem e envia para
   `REGION-docker.pkg.dev/PROJECT_ID/jasp-to-python/jasp-to-python:<commit>`;
3. publica no Cloud Run com acesso público, 1 vCPU, 1 GiB de memória,
   de 0 a 3 instâncias (escala a zero quando ninguém usa, então o custo parado é zero);
4. mostra a URL do app no resumo da execução.

Para mudar memória, instâncias ou deixar o app privado, edite os `flags` no
workflow (por exemplo, troque `--allow-unauthenticated` por
`--no-allow-unauthenticated`).

## Deploy manual (sem GitHub Actions)

Para testar uma vez direto do Cloud Shell, sem configurar nada do passo 1:

```bash
gcloud run deploy jasp-to-python --source . --project jasp-to-pyhton \
  --region southamerica-east1 --allow-unauthenticated --memory 1Gi
```

## Testar a imagem localmente

```bash
docker build -t jasp-to-python .
docker run --rm -p 8080:8080 jasp-to-python
# abra http://localhost:8080
```

A imagem roda como usuário sem privilégios, usa 2 workers do gunicorn
(ajustável com `-e WEB_CONCURRENCY=...`) e ocupa cerca de 240 MiB de memória
em repouso. O CI monta e sobe a imagem em todo PR para garantir que o deploy
não quebre.

## Problemas comuns

- **`Permission 'iam.serviceAccounts.getAccessToken' denied`**: o
  `GCP_WIF_PROVIDER` ou o `GCP_DEPLOY_SA` foi copiado errado, ou o repositório
  mudou de nome; rode o script de novo com `GITHUB_REPO=<dono>/<repo>`.
- **`allUsers` bloqueado ao publicar**: contas de organização podem ter a
  política "Domain restricted sharing". Peça a liberação ao administrador ou
  publique com `--no-allow-unauthenticated`.
- **Faturamento desativado**: o Cloud Run e o Artifact Registry exigem uma conta
  de faturamento vinculada ao projeto, mesmo dentro da cota gratuita.
