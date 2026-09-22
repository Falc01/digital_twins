FROM python:3.11-slim

# Instala dependências de compilação básicas necessárias para pacotes Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instala dependências do requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código fonte do backend
COPY . .

# Expõe a porta de comunicação do FastAPI
EXPOSE 8000

# Adiciona o diretório src ao PYTHONPATH do container
ENV PYTHONPATH=/app/src

# Inicializa o servidor Uvicorn
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
