FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY scripts ./scripts
COPY static ./static

RUN useradd --system --uid 10001 --create-home appuser
USER appuser

EXPOSE 5000

CMD ["python", "app.py"]
