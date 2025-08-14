FROM python:3.11-slim

LABEL maintainer="Firebreather"
LABEL description="Dockerfile for a bidding tool"

# Set work directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies needed for PostgreSQL client
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire Django project
COPY . .

# Remove unnecessary files from the container
RUN rm -f docker-compose.yml Dockerfile .gitignore

RUN mkdir -p /app/logs

# Set proper permissions for logs
RUN chown -R 1000:1000 /app/logs

RUN python manage.py collectstatic --noinput --settings=bidlord.config.local

# Expose the port for the Django development server
EXPOSE 8000

# Command to run the application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]