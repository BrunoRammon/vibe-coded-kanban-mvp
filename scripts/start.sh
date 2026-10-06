#!/bin/bash
# start.sh
echo "Starting Docker containers..."
docker compose up --build -d
echo "Server is running at http://localhost:8000"
