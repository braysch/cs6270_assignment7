FROM python:3.11-slim

WORKDIR /app

RUN pip install boto3

COPY consumer/ .

CMD ["python", "consumer.py", "--request-queue", "cs5270-requests", "--storage-target", "dynamodb", "--widget-destination", "widgets"]
