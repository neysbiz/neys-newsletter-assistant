FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock
COPY backend ./backend
RUN useradd --create-home newsletter && mkdir -p /app/staticfiles /app/media && chown -R newsletter:newsletter /app
USER newsletter
WORKDIR /app/backend
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "/dev/null"]
