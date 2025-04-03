# Use slim Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install first (for layer caching)
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Now copy everything else
COPY . .

# Expose port for Railway
EXPOSE 8000

# Run your Flask app
CMD ["python", "app/server.py"]
