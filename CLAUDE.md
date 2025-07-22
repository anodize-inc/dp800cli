# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
This is a Python CLI tool for communicating with Rigol DP800 series power supplies via SCPI (Standard Commands for Programmable Instruments) over TCP/IP network connection.

## Architecture
- Single Python script (`id_device.py`) that demonstrates basic SCPI communication
- Uses PyVISA library for instrument communication
- Connects to Rigol device via TCP socket (IP:PORT format)
- Default configuration: `192.168.1.100:5555`

## Development Commands

```bash
# Install dependencies (manual installation required)
pip install pyvisa pyvisa-py

# Validate code with pylint (required after any changes)
make

# Clean lint cache files
make clean
```

## Code Quality
- Always run `make` after making changes to validate with pylint
- Code must achieve 10.00/10 pylint rating
- Makefile automatically lints all Python files in the project

## Git Workflow
- When committing changes, always use `git add` on specific files, never `git add .` or `git add --all`
- Explicitly specify each file to be committed to maintain precise control over what gets added
- Example: `git add file1.py file2.py` instead of `git add .`

## Key Configuration
- **RIGOL_IP**: Must be updated to match your device's actual IP address in `id_device.py:3`
- **RIGOL_PORT**: Rigol devices use port 5555 for SCPI over LAN
- **Termination**: Rigol devices use newline (`\n`) for command termination

## SCPI Communication Pattern
- Uses PyVISA resource manager with `@py` backend
- Resource format: `TCPIP::{IP}::{PORT}::SOCKET`
- Standard SCPI commands like `*IDN?` for device identification
- Proper connection cleanup in finally block