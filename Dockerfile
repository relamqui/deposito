FROM python:3.11-slim

WORKDIR /app

# Instala as bibliotecas de dependência limpas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todos os arquivos pro docker
COPY . .

EXPOSE 8000

# Comando para iniciar o servidor
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
