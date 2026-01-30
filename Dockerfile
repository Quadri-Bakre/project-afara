FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies (ping utility is required for your ping driver)
RUN apt-get update && apt-get install -y iputils-ping && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run the Excel Converter FIRST, then the Main Engine
# Use 'sh -c' to chain these commands together
CMD ["sh", "-c", "python tools/excel_to_yaml.py && python main.py"]