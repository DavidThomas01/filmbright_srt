# webhook/Dockerfile NEW

# Use Python 3.10 slim
FROM python:3.10-slim

# Set environment variables
ENV PORT=8080

# Create and switch to a working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Copy credentials (if not using Secret Manager; see Security section)
COPY credentials_srt_files_translation.json .

# Expose port 8080
EXPOSE 8080

# Start Flask app
CMD ["python", "webhook_app.py"]