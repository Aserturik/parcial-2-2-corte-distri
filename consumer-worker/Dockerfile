FROM python:3.11-slim

WORKDIR /app

# Crear directorio para datos persistentes
RUN mkdir -p /app/data

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "worker.py"] 