#!/bin/bash
# ABOUTME: Script to start VNC server
# ABOUTME: Configures display and starts x11vnc

# Set display
export DISPLAY=:1

# Wait for X server to be ready
sleep 5

# Start x11vnc
x11vnc -display :1 -rfbport 5900 -shared -forever -passwd ${VNC_PASSWORD:-changeme} &

# Keep script running
tail -f /dev/null