FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Full pipeline: extract + load + transform -> data quality tests -> train models
CMD ["sh", "-c", "python ingestion.py && pytest -q && python train.py"]
