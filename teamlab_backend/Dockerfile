# Build from the repository root:
# docker build -f teamlab_backend/Dockerfile .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY teamlab_backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY teamlab_backend/ .
COPY docs /docs

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
