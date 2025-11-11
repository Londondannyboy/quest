#!/bin/bash
#Start both the Temporal worker and the FastAPI server

# Start FastAPI server in the background
python api.py &
API_PID=$!

# Start Temporal worker in the foreground
python worker.py &
WORKER_PID=$!

# Wait for both processes
wait $API_PID $WORKER_PID
