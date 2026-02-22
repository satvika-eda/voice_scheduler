#!/bin/bash
set -e

echo "Starting uvicorn..."
echo "Port: ${PORT:-8080}"
echo "Current directory: $(pwd)"
echo "Files in /app:"
ls -la /app/

# Run with explicit error output
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --log-level debug
