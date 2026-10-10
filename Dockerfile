FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=5000
EXPOSE 5000
CMD ["gunicorn", "app:app", "--worker-class", "gthread", "--threads", "4", "--workers", "2", "--bind", "0.0.0.0:5000"]
