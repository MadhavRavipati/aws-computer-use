# ABOUTME: Docker configuration for Ubuntu desktop environment
# ABOUTME: Includes XVFB, VNC server, browser, and Python for agent

FROM ubuntu:22.04

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:1
ENV VNC_RESOLUTION=1920x1080
ENV VNC_PASSWORD=changeme

# Install system packages
RUN apt-get update && apt-get install -y \
    # X11 and VNC
    xvfb \
    x11vnc \
    novnc \
    websockify \
    # Window manager
    openbox \
    # Browsers
    firefox \
    chromium-browser \
    # Python and tools
    python3.12 \
    python3-pip \
    python3-venv \
    # System utilities
    supervisor \
    curl \
    wget \
    jq \
    git \
    vim \
    htop \
    net-tools \
    iputils-ping \
    # Fonts
    fonts-liberation \
    fonts-dejavu-core \
    # Clean up
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /tmp/
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Create user for running desktop
RUN useradd -m -s /bin/bash desktop && \
    echo "desktop:desktop" | chpasswd

# Setup VNC password
RUN mkdir -p /home/desktop/.vnc && \
    x11vnc -storepasswd ${VNC_PASSWORD} /home/desktop/.vnc/passwd && \
    chown -R desktop:desktop /home/desktop/.vnc

# Copy supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy startup scripts
COPY scripts/start-vnc.sh /usr/local/bin/
COPY scripts/start-desktop.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/start-*.sh

# Copy VNC bridge application
COPY --from=vnc-bridge /app /app
WORKDIR /app

# Expose ports
EXPOSE 5900 6080 8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:6080/ || exit 1

# Run supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]