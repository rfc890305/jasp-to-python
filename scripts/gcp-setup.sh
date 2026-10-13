#!/usr/bin/env bash
# Configuração única do Google Cloud para o deploy automático pelo GitHub Actions.
# Rode no Cloud Shell (ou com o gcloud logado como dono do projeto):
#
#   bash scripts/gcp-setup.sh            # projeto padrão: jasp-to-pyhton
#   PROJECT_ID=outro-projeto bash scripts/gcp-setup.sh
#
# Ao final, o script imprime as variáveis para cadastrar no GitHub.
# Pode ser executado de novo sem problemas: o que já existe é mantido.
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-jasp-to-pyhton}"
REGION="${REGION:-southamerica-east1}"
GITHUB_REPO="${GITHUB_REPO:-rfc890305/jasp-to-python}"
REPOSITORY="${REPOSITORY:-jasp-to-python}"   # repositório no Artifact Registry
POOL="${POOL:-github}"
PROVIDER="${PROVIDER:-github}"
DEPLOY_SA_NAME="${DEPLOY_SA_NAME:-github-deployer}"

gcloud config set project "$PROJECT_ID" >/dev/null
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
DEPLOY_SA="${DEPLOY_SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
RUNTIME_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

echo "==> Ativando APIs"
gcloud services enable run.googleapis.com artifactregistry.googleapis.com \
  iamcredentials.googleapis.com sts.googleapis.com cloudresourcemanager.googleapis.com

echo "==> Repositório de imagens (Artifact Registry)"
gcloud artifacts repositories describe "$REPOSITORY" --location "$REGION" >/dev/null 2>&1 ||
  gcloud artifacts repositories create "$REPOSITORY" --location "$REGION" \
    --repository-format docker --description "Imagens do jasp-to-python"

echo "==> Conta de serviço usada pelo GitHub Actions"
gcloud iam service-accounts describe "$DEPLOY_SA" >/dev/null 2>&1 ||
  gcloud iam service-accounts create "$DEPLOY_SA_NAME" --display-name "Deploy pelo GitHub Actions"

for ROLE in roles/run.admin roles/artifactregistry.writer; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" --condition=None \
    --member "serviceAccount:${DEPLOY_SA}" --role "$ROLE" >/dev/null
done
# Permite que o deploy rode o serviço com a conta padrão do Compute Engine
gcloud iam service-accounts add-iam-policy-binding "$RUNTIME_SA" \
  --member "serviceAccount:${DEPLOY_SA}" --role roles/iam.serviceAccountUser >/dev/null

echo "==> Workload Identity Federation (login sem chave a partir do GitHub)"
gcloud iam workload-identity-pools describe "$POOL" --location global >/dev/null 2>&1 ||
  gcloud iam workload-identity-pools create "$POOL" --location global --display-name "GitHub Actions"

gcloud iam workload-identity-pools providers describe "$PROVIDER" \
  --workload-identity-pool "$POOL" --location global >/dev/null 2>&1 ||
  gcloud iam workload-identity-pools providers create-oidc "$PROVIDER" \
    --workload-identity-pool "$POOL" --location global \
    --issuer-uri "https://token.actions.githubusercontent.com" \
    --attribute-mapping "google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref" \
    --attribute-condition "assertion.repository == '${GITHUB_REPO}'"

# Só este repositório do GitHub pode se passar pela conta de deploy
gcloud iam service-accounts add-iam-policy-binding "$DEPLOY_SA" \
  --role roles/iam.workloadIdentityUser \
  --member "principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL}/attribute.repository/${GITHUB_REPO}" >/dev/null

WIF_PROVIDER="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL}/providers/${PROVIDER}"

cat <<MSG

Pronto. Cadastre estas variáveis no GitHub, em
Settings > Secrets and variables > Actions > aba "Variables":

  GCP_PROJECT_ID    = ${PROJECT_ID}
  GCP_REGION        = ${REGION}
  GCP_WIF_PROVIDER  = ${WIF_PROVIDER}
  GCP_DEPLOY_SA     = ${DEPLOY_SA}

Ou, com o GitHub CLI:

  gh variable set GCP_PROJECT_ID   -R ${GITHUB_REPO} -b "${PROJECT_ID}"
  gh variable set GCP_REGION       -R ${GITHUB_REPO} -b "${REGION}"
  gh variable set GCP_WIF_PROVIDER -R ${GITHUB_REPO} -b "${WIF_PROVIDER}"
  gh variable set GCP_DEPLOY_SA    -R ${GITHUB_REPO} -b "${DEPLOY_SA}"
MSG
