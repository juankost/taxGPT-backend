#!/bin/bash

# Fetch the PORT environment variable or default to 8000
PORT=${PORT:-8000}

# Start Uvicorn with dynamic port assignment
exec uvicorn app.app:app --host 0.0.0.0 --port ${PORT}  # app.app is still ok becuase the workdir is /workspace/src
