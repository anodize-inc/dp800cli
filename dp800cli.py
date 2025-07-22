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


def cmd_state(args):
    """Handle the 'state' subcommand."""
    try:
        controller = DP800Controller(args.ip, args.port)
        controller.connect()
        controller.validate_device_id(controller.get_device_id())

        if args.channel:
            # Query specific channel
            state = controller.get_channel_state(args.channel)
            print_channel_state(state)
        else:
            # Query all channels
            states = controller.get_all_channels_state()
            for state in states:
                print_channel_state(state)
                print()  # Empty line between channels

    except DP800Error as error_msg:
        print(f"Error: {error_msg}", file=sys.stderr)
        sys.exit(1)
    finally:
        if 'controller' in locals():
            controller.disconnect()


def cmd_screenshot(args):
    """Handle the 'screenshot' subcommand."""
    try:
        controller = DP800Controller(args.ip, args.port)
        controller.connect()
        controller.validate_device_id(controller.get_device_id())

        filename = controller.take_screenshot(args.output)
        print(f"Screenshot saved to: {filename}")

    except DP800Error as error_msg:
        print(f"Error: {error_msg}", file=sys.stderr)
        sys.exit(1)
    finally:
        if 'controller' in locals():
            controller.disconnect()


def print_channel_state(state):
    """Print formatted channel state information."""
    channel = state['channel']
    print(f"Channel {channel}:")
    print(f"  Set Voltage:     {state['set_voltage']:>8.3f} V")
    print(f"  Set Current:     {state['set_current']:>8.3f} A")
    print(f"  OVP Value:       {state['ovp_value']:>8.3f} V")
    print(f"  OVP Enabled:     {state['ovp_enabled']}")
    print(f"  OCP Value:       {state['ocp_value']:>8.3f} A")
    print(f"  OCP Enabled:     {state['ocp_enabled']}")


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

    # State command
    state_parser = subparsers.add_parser('state', help='Get channel state information')
    state_parser.add_argument(
        '-c', '--channel',
        type=int,
        choices=[1, 2, 3],
        help='Channel number (1-3). If not specified, shows all channels.'
    )
    state_parser.set_defaults(func=cmd_state)

    # Screenshot command
    screenshot_parser = subparsers.add_parser(
        'screenshot', help='Take a screenshot of the device display'
    )
    screenshot_parser.add_argument(
        '-o', '--output',
        help='Output filename (default: auto-generated with timestamp)'
    )
    screenshot_parser.set_defaults(func=cmd_screenshot)

    # Parse arguments
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    # Execute the command
    args.func(args)


if __name__ == "__main__":
    main()
