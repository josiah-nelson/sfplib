#!/usr/bin/env bashio

# Create directories early
bashio::log.info "Creating data directories..."
mkdir -p /config/sfplib/submissions
mkdir -p /config/sfplib/backups

bashio::log.info "Starting SFPLiberate Home Assistant Add-On..."

# Execute s6-overlay init system
exec /init
