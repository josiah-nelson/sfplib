"""
Test patterns for BLE protocol exploration.

This module provides common command patterns to test against
BLE devices for protocol reverse engineering.
"""

from typing import List, Dict, Any


def get_test_patterns() -> List[Dict[str, Any]]:
    """
    Get list of test patterns for protocol exploration.

    Returns:
        List of test pattern dictionaries with data and metadata
    """
    patterns = []

    # HTTP-like commands (SFP Wizard protocol)
    http_verbs = ["GET", "POST", "PUT", "DELETE", "PATCH"]
    endpoints = [
        "/",
        "/api",
        "/api/1.0",
        "/api/1.0/version",
        "/stats",
        "/status",
        "/sif",
        "/sif/start",
        "/sif/read",
        "/sif/write",
        "/sif/erase",
        "/sif/status",
    ]

    for verb in http_verbs:
        for endpoint in endpoints:
            command = f"{verb} {endpoint}"
            patterns.append({
                "type": "http_command",
                "data": command.encode('utf-8'),
                "description": command
            })

    # Common protocol commands
    common_commands = [
        b"AT",
        b"AT+",
        b"AT+VERSION",
        b"AT+RESET",
        b"VERSION",
        b"STATUS",
        b"READ",
        b"WRITE",
        b"START",
        b"STOP",
        b"INIT",
    ]

    for cmd in common_commands:
        patterns.append({
            "type": "at_command",
            "data": cmd,
            "description": cmd.decode('utf-8')
        })

    # Binary patterns
    binary_patterns = [
        b"\x00",  # NULL
        b"\x01",  # Start of heading
        b"\x02",  # Start of text
        b"\x03",  # End of text
        b"\x04",  # End of transmission
        b"\xFF",  # All bits set
        b"\xAA\x55",  # Alternating bits
    ]

    for data in binary_patterns:
        patterns.append({
            "type": "binary",
            "data": data,
            "description": f"Binary: {data.hex()}"
        })

    return patterns
