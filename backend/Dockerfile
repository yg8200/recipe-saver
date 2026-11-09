# Image for the Flask backend.
FROM python:3.14-slim

# Don't write .pyc files, and print logs immediately (otherwise Python buffers them
# and `docker compose logs` looks empty).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy requirements first and install them in their own layer. Docker caches each step,
# so dependencies are only reinstalled when requirements.txt changes, not on every code edit.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5001

# main.py creates missing tables, then runs Flask's dev server on 0.0.0.0:5001 with auto-reload.
# 0.0.0.0 (not 127.0.0.1) is required so the server is reachable from outside the container.
CMD ["python", "main.py"]
