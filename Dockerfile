FROM python:3.12-slim

WORKDIR /app

ARG APPLICATION_VERSION=0.0.0
ARG GIT_COMMIT=local

ENV APPLICATION_VERSION=$APPLICATION_VERSION
ENV GIT_COMMIT=$GIT_COMMIT

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 5000

CMD ["python", "app.py"]