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
EXPOSE 8002 
# or 8001, depending on the service; will be overridden by docker-compose

# Run the FastAPI server
CMD ["uvicorn", "chat-service:app", "--host", "0.0.0.0", "--port", "8002"]