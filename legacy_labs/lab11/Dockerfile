FROM python:3.12-slim

LABEL org.opencontainers.image.authors="K J NIKHIL REDDY" \
      com.example.student.usn="24BTRCL091"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scripts/labs.py .

ENTRYPOINT ["python", "/app/labs.py"]
