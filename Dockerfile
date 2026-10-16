FROM python:3.13-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    useradd --system --uid 10001 --create-home bot && \
    mkdir /data && chown bot:bot /data
COPY --chown=bot:bot app ./app
USER bot
CMD ["python", "-m", "app.main"]
