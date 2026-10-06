#!/bin/bash
# test.sh
echo "Running automated tests..."
docker compose exec app pytest backend/tests/
