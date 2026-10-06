#!/bin/bash
# stop.sh
echo "Stopping Docker containers..."
docker compose down
echo "Containers stopped."
