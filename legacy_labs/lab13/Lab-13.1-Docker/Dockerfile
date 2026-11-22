FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /lab
COPY Lab-13.1-Docker/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY Lab-13.1-Docker/pymongo-test.py Lab-13.1-Docker/failover-test.py ./
COPY . /lab/project/

CMD ["python", "pymongo-test.py"]
