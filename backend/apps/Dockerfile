FROM docker.io/library/python:3.12-slim
RUN pip install --no-cache-dir "fastapi>=0.115,<1.0" "httpx>=0.27,<1.0" "uvicorn>=0.30,<1.0" \
    "sqlalchemy>=2.0,<3.0" "psycopg[binary]>=3.2,<4.0"
ARG SERVICE
WORKDIR /srv
COPY ${SERVICE}/app ./app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
