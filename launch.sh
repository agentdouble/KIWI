#!/bin/bash

# Kill existing screens if they exist
screen -S back_gpt -X quit 2>/dev/null
screen -S front_gpt -X quit 2>/dev/null

echo "Starting application..."

# Start backend in screen
echo "Starting backend in screen 'back_gpt'..."
screen -dmS back_gpt bash -c "cd backend && python run.py; exec bash"

# Start frontend in screen
echo "Starting frontend in screen 'front_gpt'..."
screen -dmS front_gpt bash -c "cd frontend && npm start; exec bash"

echo "Application started!"
echo ""
echo "To view backend logs: screen -r back_gpt"
echo "To view frontend logs: screen -r front_gpt"
echo ""
echo "To detach from screen: Ctrl+A then D"
echo "To list screens: screen -ls"
echo "To stop: ./stop.sh"