# Stage 1: Build React frontend
FROM node:20-alpine AS frontend-builder

# Install Python and build tools for native dependencies
RUN apk add --no-cache python3 make g++

WORKDIR /frontend

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci

# Copy frontend source code
COPY frontend/ ./

# Build arguments for Vite environment variables
ARG VITE_AUTH0_DOMAIN
ARG VITE_AUTH0_CLIENT_ID
ARG VITE_AUTH0_AUDIENCE

# Set environment variables for the build (Vite consumes VITE_*)
ENV VITE_AUTH0_DOMAIN=$VITE_AUTH0_DOMAIN
ENV VITE_AUTH0_CLIENT_ID=$VITE_AUTH0_CLIENT_ID
ENV VITE_AUTH0_AUDIENCE=$VITE_AUTH0_AUDIENCE

# DEBUG
RUN env | grep -E 'VITE_AUTH0|^AUTH0_' || true

# Build the React app (Vite outputs to /frontend/dist)
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

# Copy built frontend from stage 1 (use Vite's dist output)
COPY --from=frontend-builder /frontend/dist /app/static

# Create a main.py in the root directory for correct imports
RUN echo 'from app.main import app' > /app/main.py
RUN chmod +x /app/main.py

# Copy Alembic configuration and migrations for DB migrations
COPY alembic.ini /app/alembic.ini
COPY migrations/ /app/migrations/

# Copy entrypoint that runs migrations before starting the app
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Run migrations then start the application
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
