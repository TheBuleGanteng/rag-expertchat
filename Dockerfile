FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir --no-deps -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p /app/static
RUN mkdir -p /app/media

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8001

# Run the application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8001"]