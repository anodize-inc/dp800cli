#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Steve deRosier

"""CLI tool to identify Rigol DP800 series power supplies via SCPI over TCP/IP."""
import pyvisa

RIGOL_IP = '192.168.0.55' # <<< IMPORTANT: Replace with your Rigol's actual IP address
RIGOL_PORT = 5555           # <<< IMPORTANT: Rigol uses port 5555 for SCPI over LAN [4, 5]

def main():
    """Connect to Rigol device and query identification information."""
    resource_manager = pyvisa.ResourceManager('@py')
    resource_name = f'TCPIP::{RIGOL_IP}::{RIGOL_PORT}::SOCKET'

    try:
        inst = resource_manager.open_resource(resource_name)
        inst.read_termination = '\n' # Rigol typically uses newline for termination
        inst.write_termination = '\n'

        print(f"Connecting to: {resource_name}")

        # Query instrument identification
        idn_response = inst.query('*IDN?')
        print(f"Instrument ID: {idn_response}") # Expected format: RIGOL TECHNOLOGIES,DP832,... [4]

    except pyvisa.errors.VisaIOError as error_msg:
        print(f"Error connecting or communicating: {error_msg}")

    finally:
        if 'inst' in locals() and inst:
            inst.close()
            print("Connection closed.")

if __name__ == "__main__":
    main()
