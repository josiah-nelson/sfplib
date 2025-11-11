# BUILD_FROM is passed by Home Assistant builder from build.yaml
# Must be declared globally for multi-stage builds
ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:3.22
ARG BUILD_VERSION=0.0.0

# ============================================================================
# Stage 1: Backend build
# ============================================================================
# Use build platform (not target) to avoid slow QEMU cross-compilation
FROM --platform=$BUILDPLATFORM python:3.12-slim AS backend-build

WORKDIR /backend

# Install build dependencies for compiling Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==1.8.5

# Copy backend dependency files
COPY backend/pyproject.toml backend/poetry.lock ./

# Export dependencies to requirements.txt
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes --without dev

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY backend/app /backend/app

# ============================================================================
# Stage 2: Final runtime image (Alpine.js static UI)
# ============================================================================
# Re-declare BUILD_FROM for this stage
ARG BUILD_FROM
ARG BUILD_VERSION
FROM ${BUILD_FROM}

# Install runtime dependencies (Alpine.js is pure HTML/JS served as static files)
RUN apk add --no-cache \
    python3 \
    py3-pip \
    dbus \
    bluez \
    bluez-deprecated \
    curl \
    jq

# Copy backend app code
COPY --from=backend-build /backend/app /app/backend/app

# Install Python dependencies in a virtualenv (PEP 668 compliant)
COPY --from=backend-build /backend/requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt \
    && /opt/venv/bin/pip install --no-cache-dir 'aiohttp>=3.10,<4'

# Prefer the venv Python on PATH for runtime
ENV PATH="/opt/venv/bin:${PATH}"

# Copy add-on files (build context is repo root)
# Static Alpine.js UI included in rootfs/usr/share/sfplib/ui/
COPY sfplib/rootfs /

# Ensure sane permissions after copying rootfs (prevent accidental no-exec/closed perms)
# Some repos may have stricter directory modes checked into VCS (e.g., 0700 on usr),
# which can break Alpine's merged-/usr layout or s6 overlay startup on HA base images.
RUN chmod 0755 /usr \
    && chmod -R a+rX /etc/s6-overlay \
    && chmod -R a+rX /usr/share/sfplib

# Create necessary directories and set permissions
# Note: /config and /share are mounted by HA at runtime
# Running as root is required for D-Bus/Bluetooth access and system operations
RUN mkdir -p /app /data && \
    chmod +x /etc/s6-overlay/s6-rc.d/init-sfplib/run && \
    chmod +x /etc/s6-overlay/s6-rc.d/backend/run

# Health check (backend API on port 80)
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:80/health || exit 1

# Expose ports (for documentation - ingress handles actual access)
EXPOSE 80

# Set version as environment variable for application use
ENV ADDON_VERSION=${BUILD_VERSION}

# Enable s6-overlay debug logging
ENV S6_VERBOSITY=3

# Explicitly set entrypoint to s6-overlay init to avoid shell form execution
# on some supervisor/docker combinations
ENTRYPOINT ["/init"]

# Set container metadata
LABEL \
    io.hass.name="SFPLiberate" \
    io.hass.description="Bluetooth companion for Ubiquiti SFP Wizard" \
    io.hass.arch="aarch64|amd64|armhf|armv7" \
    io.hass.type="addon" \
    io.hass.version=${BUILD_VERSION} \
    maintainer="Josiah Nelson <https://github.com/josiah-nelson>" \
    org.opencontainers.image.title="SFPLiberate" \
    org.opencontainers.image.description="Bluetooth companion for Ubiquiti SFP Wizard" \
    org.opencontainers.image.vendor="SFPLiberate" \
    org.opencontainers.image.authors="Josiah Nelson" \
    org.opencontainers.image.licenses="MIT" \
    org.opencontainers.image.url="https://github.com/josiah-nelson/SFPLiberate" \
    org.opencontainers.image.source="https://github.com/josiah-nelson/SFPLiberate" \
    org.opencontainers.image.documentation="https://github.com/josiah-nelson/SFPLiberate/blob/main/docs/HOME_ASSISTANT.md" \
    org.opencontainers.image.version=${BUILD_VERSION}
