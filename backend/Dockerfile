FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ ./app/

# Let Railway handle everything
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

## And in Railway Settings:

1. **Go to Settings → Deploy**
2. **Custom Start Command**: Leave EMPTY
3. **Restart Policy**: Change to `always` (not `on-failure`)
4. **Healthcheck**: Remove it entirely (delete the healthcheck path if set)

## Environment Variables - Make sure you have:
```
ALLOWED_ORIGINS=https://shortlist-seven.vercel.app,http://localhost:3000
PORT=8080
