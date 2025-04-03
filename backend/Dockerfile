# Base image
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of the backend (code files)
COPY . .

# Set environment variables (optional but nice)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Open Railway port
EXPOSE 8000

# Start Flask
CMD ["python", "app/server.py"]
