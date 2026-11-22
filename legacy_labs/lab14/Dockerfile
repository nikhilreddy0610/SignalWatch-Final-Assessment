FROM mongo:7.0

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt
ENV PATH="/opt/venv/bin:${PATH}"

COPY monitoring.py backup_verify.py restore_verify.py benchmark.py backup_scheduler.py config.py README.md ./

RUN mkdir -p /app/backups /app/logs

CMD ["python3", "monitoring.py"]
