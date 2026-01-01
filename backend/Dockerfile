# Use an official Python runtime as the base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements files
COPY pyproject.toml requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire backend directory
COPY . .

# Expose the port that the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "rag_agent.main:app", "--host", "0.0.0.0", "--port", "8000"]