FROM python:3.11-slim

WORKDIR /app

# Copy backend requirements and install dependencies
COPY ../backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy backend code (needed for imports)
COPY ../backend /app/backend

# Copy worker code
COPY . /app/worker

# Set Python path to include backend
ENV PYTHONPATH=/app

# Run the worker
CMD ["python", "/app/worker/main.py"]
