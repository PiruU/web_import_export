FROM python:3.13-slim

WORKDIR /app

COPY web_import_export/app/ /app/

RUN pip install --no-cache-dir fastapi uvicorn pydantic httpx

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]