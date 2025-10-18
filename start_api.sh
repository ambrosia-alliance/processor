#!/bin/bash

echo "Starting Therapy Classification API..."
echo "API will be available at http://localhost:8000"
echo "Documentation at http://localhost:8000/docs"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

