# Stage 1: Build the Next.js frontend
FROM node:20-slim AS builder
WORKDIR /app
COPY frontend/package*.json ./frontend/
WORKDIR /app/frontend
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Build the FastAPI backend
FROM python:3.12-slim

# Install uv
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY backend/requirements.txt /app/backend/

# Install dependencies using uv
RUN uv pip install --system -r /app/backend/requirements.txt

# Copy the rest of the backend code
COPY backend /app/backend

# Copy the built Next.js static files to backend/static
COPY --from=builder /app/frontend/out /app/backend/static

# Expose port
EXPOSE 8000

# Set Python path so imports work correctly
ENV PYTHONPATH=/app

# Command to run the application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
