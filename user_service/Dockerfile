# Use an official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8001 
# or 8002, depending on the service; will be overridden by docker-compose

# Run the FastAPI server
CMD ["uvicorn", "user-service:app", "--host", "0.0.0.0", "--port", "8001"]