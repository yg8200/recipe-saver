FROM python:3.14-slim

# Unbuffered so logs show up in `docker compose logs` right away
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Own layer so a code change doesn't reinstall dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5001

# Runs migrations, then the dev server
CMD ["python", "main.py"]
