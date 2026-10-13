# Imagem oficial e leve do Python
FROM python:3.11-slim

# Não grava .pyc e envia o output direto ao terminal
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Todas as dependências (numpy, scipy, pandas, statsmodels) têm wheels prontos
# para Linux, então não é preciso instalar compiladores na imagem.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Roda como usuário sem privilégios
RUN useradd --create-home --uid 1000 app && chown -R app /app
USER app

# O Cloud Run injeta a porta em $PORT (padrão 8080).
# WEB_CONCURRENCY permite ajustar o número de workers sem rebuild.
ENV PORT=8080 \
    WEB_CONCURRENCY=2
EXPOSE 8080

# 'app:server' é o servidor Flask interno do Dash.
# --timeout 0 deixa o Cloud Run controlar o tempo limite das requisições.
CMD exec gunicorn --bind 0.0.0.0:${PORT} --workers ${WEB_CONCURRENCY} --threads 4 --timeout 0 app:server
