# Use official lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy everything from backend into the container
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port Railway expects (usually 8000)
EXPOSE 8000

# Run your Flask app
CMD ["python", "app/server.py"]
