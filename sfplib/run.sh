#!/usr/bin/with-contenv bashio

# Create directories early
bashio::log.info "Creating data directories..."
mkdir -p /config/sfplib/submissions
mkdir -p /config/sfplib/backups

# Set deployment mode to HA addon
export DEPLOYMENT_MODE="homeassistant"
export HA_ADDON_MODE="true"

bashio::log.info "Starting SFPLiberate Home Assistant Add-On..."
bashio::log.info "Configuration will be loaded by backend service"

# Note: Environment variables are exported by /etc/services.d/backend/run
# This avoids duplication and ensures configuration is loaded just-in-time
