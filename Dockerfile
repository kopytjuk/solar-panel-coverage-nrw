FROM python:3.12-slim-bookworm

WORKDIR /app

COPY src/hello_app.py .

CMD ["python", "hello_app.py"]