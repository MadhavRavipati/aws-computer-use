#!/bin/bash
# ABOUTME: Script to start desktop environment
# ABOUTME: Initializes X server and window manager

# Start Xvfb
Xvfb :1 -screen 0 ${VNC_RESOLUTION}x24 &
XVFB_PID=$!

# Wait for X server
sleep 3

# Set display
export DISPLAY=:1

# Start window manager
openbox &

# Configure desktop appearance
xsetroot -solid "#2D3748"

# Keep script running
wait $XVFB_PID