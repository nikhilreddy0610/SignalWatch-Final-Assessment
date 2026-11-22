FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY lab_01_write_concern_latency.py lab_02_write_probe.py \
     labctl.sh lab_02_simulate_partition.sh compose.yaml README.md \
     submission_report.txt submission_report.pdf ./

ENTRYPOINT ["python"]
CMD ["/app/lab_01_write_concern_latency.py"]
