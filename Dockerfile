# Official Playwright image ships browsers + system deps preinstalled.
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONPATH=/app/src:/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default command runs the bot headless; override args at `docker run`.
ENTRYPOINT ["python", "-m", "pricewatch.main"]
CMD ["--pages", "5"]
