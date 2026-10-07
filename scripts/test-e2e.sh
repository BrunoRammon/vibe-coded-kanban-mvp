#!/bin/bash
# test-e2e.sh
echo "Running E2E tests using Playwright Docker image..."
docker run --rm --network pm_default -e BASE_URL=http://app:8000 -v $(pwd)/frontend:/app/frontend -w /app/frontend mcr.microsoft.com/playwright:v1.58.0-jammy sh -c "npm ci && npx playwright test"

