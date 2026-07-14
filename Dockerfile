# Official Playwright image: Chromium + all required system libraries preinstalled.
# Tag matches playwright==1.53.0 in requirements.txt.
FROM mcr.microsoft.com/playwright/python:v1.53.0-jammy

WORKDIR /app

# Install Python dependencies first for better layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install the Chromium browser into the path the app looks in
# (app/services/pdf/assets.py -> BROWSER_DIR = <repo>/.playwright-browsers).
ENV PLAYWRIGHT_BROWSERS_PATH=/app/.playwright-browsers
RUN python -m playwright install chromium

# Copy the application source.
COPY . .

# Railway injects $PORT at runtime. Shell form so the variable expands.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
