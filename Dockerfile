# Stage 1: Build React frontend
FROM node:18-alpine AS frontend-builder

# Install Python and build tools for native dependencies
RUN apk add --no-cache python3 make g++

WORKDIR /frontend

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci

# Copy frontend source code
COPY frontend/ ./

# Build arguments for React environment variables
ARG REACT_APP_AUTH0_DOMAIN
ARG REACT_APP_AUTH0_CLIENT_ID
ARG REACT_APP_AUTH0_AUDIENCE

# Set environment variables for the build
ENV REACT_APP_AUTH0_DOMAIN=$REACT_APP_AUTH0_DOMAIN
ENV REACT_APP_AUTH0_CLIENT_ID=$REACT_APP_AUTH0_CLIENT_ID
ENV REACT_APP_AUTH0_AUDIENCE=$REACT_APP_AUTH0_AUDIENCE

# Build the React app
RUN npm run build

# Stage 2: Python backend with built frontend
FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app/ /app/app/

# Copy built frontend from stage 1
COPY --from=frontend-builder /frontend/build /app/static

# Create a main.py in the root directory for correct imports
RUN echo 'from app.main import app' > /app/main.py
RUN chmod +x /app/main.py

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
