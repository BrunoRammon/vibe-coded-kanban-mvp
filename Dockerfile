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

# Expose port
EXPOSE 8000

# Set Python path so imports work correctly
ENV PYTHONPATH=/app

# Command to run the application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
