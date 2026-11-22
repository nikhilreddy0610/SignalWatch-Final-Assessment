FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY lab_10_1_bank_transfer.py lab_10_2_inventory_reservation.py run_labs.py ./

CMD ["python", "run_labs.py"]
