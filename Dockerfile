# Imagem oficial e leve do Python
FROM python:3.11-slim

# Não grava .pyc e envia o output direto ao terminal
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependências de sistema para compilar pacotes científicos, se necessário
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copia os requisitos primeiro para aproveitar o cache de camadas
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# O Cloud Run injeta a porta em $PORT (padrão 8080)
ENV PORT=8080
EXPOSE 8080

# 'app:server' é o servidor Flask interno do Dash
CMD exec gunicorn --bind 0.0.0.0:${PORT} --workers 2 --threads 4 app:server
