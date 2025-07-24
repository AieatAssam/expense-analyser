# Final image
FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create a static directory for frontend assets
RUN mkdir -p /app/static/assets

# Copy the application code
COPY app/ /app/app/

# Create a main.py in the root directory for correct imports
RUN echo 'from app.main import app' > /app/main.py
RUN chmod +x /app/main.py

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
