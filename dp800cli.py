#!/usr/bin/env python3
"""CLI tool for interacting with Rigol DP832A power supply."""

import argparse
import sys
from dp800lib import DP800Controller, DP800Error


def cmd_id(args):
    """Handle the 'id' subcommand."""
    try:
        controller = DP800Controller(args.ip, args.port)
        controller.connect()
        device_id = controller.get_device_id()
        controller.validate_device_id(device_id)
        print(f"Device ID: {device_id}")
    except DP800Error as error_msg:
        print(f"Error: {error_msg}", file=sys.stderr)
        sys.exit(1)
    finally:
        if 'controller' in locals():
            controller.disconnect()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="CLI tool for interacting with Rigol DP832A power supply"
    )

    # Global arguments
    parser.add_argument(
        '--ip',
        default='192.168.0.55',
        help='IP address of the DP832A device (default: 192.168.0.55)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5555,
        help='Port number for SCPI communication (default: 5555)'
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # ID command
    id_parser = subparsers.add_parser('id', help='Get device identification information')
    id_parser.set_defaults(func=cmd_id)

    # Parse arguments
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    # Execute the command
    args.func(args)


if __name__ == "__main__":
    main()
