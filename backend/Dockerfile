# Playwright's official Python image ships Chromium plus every system dependency
# headless browsing needs — required because Railway has no display and a plain
# Python buildpack cannot run Chromium. Pin the tag to the playwright pip version.
FROM mcr.microsoft.com/playwright/python:v1.49.0-noble

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Railway injects PORT; default for local docker runs.
ENV PORT=8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
