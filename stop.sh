#!/bin/bash

echo "Stopping application..."

# Kill screens
screen -S back_gpt -X quit 2>/dev/null
screen -S front_gpt -X quit 2>/dev/null

echo "Application stopped!"