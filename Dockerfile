FROM python:3.11-slim

# Install system dependencies for WeasyPrint and other utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libjpeg-dev \
    libopenjp2-7-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Ensure uploads directory exists
RUN mkdir -p uploads

# Expose port (default 8000, railway sets PORT env)
EXPOSE 8000

# Start command
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
