FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /workspace/backend
COPY backend/pyproject.toml backend/requirements.lock ./
RUN pip install --no-cache-dir --require-hashes -r requirements.lock
COPY backend/app ./app
RUN pip install --no-cache-dir --no-deps .
COPY pipelines /workspace/pipelines
ENV PYTHONPATH=/workspace
RUN useradd --create-home datapulse && mkdir -p /workspace/backend/data && chown -R datapulse:datapulse /workspace/backend/data
USER datapulse
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
