FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY extractor_api ./extractor_api
RUN useradd -m app
USER app
EXPOSE 8000
CMD ["uvicorn", "extractor_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
