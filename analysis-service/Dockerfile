FROM python:3.9-slim

WORKDIR /app

# Install system dependencies for Postgres
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python libraries
RUN pip install --no-cache-dir \
    kafka-python \
    psycopg2-binary \
    pandas \
    streamlit \
    altair \
    watchdog

COPY . .

# Expose Streamlit port
EXPOSE 8501

CMD ["streamlit", "run", "dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]