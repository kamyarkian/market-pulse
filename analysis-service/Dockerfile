FROM python:3.9-slim

WORKDIR /app

# Install system dependencies (Required for Postgres & Metrics)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 1. Copy requirements first (Better Docker Caching)
COPY requirements.txt .

# 2. Install Python libraries from the file
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy the rest of the application code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Run the dashboard
CMD ["streamlit", "run", "dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]