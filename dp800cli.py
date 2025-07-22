#!/usr/bin/env python3
"""CLI tool for interacting with Rigol DP832A power supply."""

import argparse
import configparser
import os
import subprocess
import sys
from pathlib import Path
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

        # Check if screenshot viewer is configured
        config_values = load_config()
        viewer_cmd = config_values.get('screenshotviewer', '').strip()

        if viewer_cmd:
            # Replace {filename} placeholder with actual filename
            viewer_cmd_final = viewer_cmd.format(filename=filename)
            try:
                # Run the viewer command in background
                subprocess.Popen(viewer_cmd_final, shell=True)  # pylint: disable=consider-using-with
                print(f"Opening screenshot with: {viewer_cmd_final}")
            except (subprocess.SubprocessError, OSError) as error_msg:
                print(f"Warning: Failed to open screenshot viewer: {error_msg}", file=sys.stderr)

    except DP800Error as error_msg:
        print(f"Error: {error_msg}", file=sys.stderr)
        sys.exit(1)
    finally:
        if 'controller' in locals():
            controller.disconnect()


def cmd_on(args):
    """Handle the 'on' subcommand."""
    try:
        controller = DP800Controller(args.ip, args.port)
        controller.connect()
        controller.validate_device_id(controller.get_device_id())

        if args.channel == 'all':
            controller.set_all_outputs_state(True)
            print("All channels turned ON")
        else:
            channel = int(args.channel)
            controller.set_output_state(channel, True)
            print(f"Channel {channel} turned ON")

    except DP800Error as error_msg:
        print(f"Error: {error_msg}", file=sys.stderr)
        sys.exit(1)
    except ValueError:
        print(f"Error: Invalid channel '{args.channel}'. Must be 1-3 or 'all'.", file=sys.stderr)
        sys.exit(1)
    finally:
        if 'controller' in locals():
            controller.disconnect()


def cmd_off(args):
    """Handle the 'off' subcommand."""
    try:
        controller = DP800Controller(args.ip, args.port)
        controller.connect()
        controller.validate_device_id(controller.get_device_id())

        if args.channel == 'all':
            controller.set_all_outputs_state(False)
            print("All channels turned OFF")
        else:
            channel = int(args.channel)
            controller.set_output_state(channel, False)
            print(f"Channel {channel} turned OFF")

    except DP800Error as error_msg:
        print(f"Error: {error_msg}", file=sys.stderr)
        sys.exit(1)
    except ValueError:
        print(f"Error: Invalid channel '{args.channel}'. Must be 1-3 or 'all'.", file=sys.stderr)
        sys.exit(1)
    finally:
        if 'controller' in locals():
            controller.disconnect()


def cmd_set(args):
    """Handle the 'set' subcommand."""
    try:
        controller = DP800Controller(args.ip, args.port)
        controller.connect()
        controller.validate_device_id(controller.get_device_id())

        # If no voltage or current specified, show current parameters
        if args.voltage is None and args.current is None:
            parameters = controller.get_channel_parameters(args.channel)
            print(f"Channel {args.channel} Parameters: {parameters}")
        else:
            # Set the specified parameters
            controller.set_channel_parameters(args.channel, args.voltage, args.current)

            # Build message showing what was set
            set_items = []
            if args.voltage is not None:
                set_items.append(f"voltage to {args.voltage} V")
            if args.current is not None:
                set_items.append(f"current to {args.current} A")

            print(f"Channel {args.channel}: Set {' and '.join(set_items)}")

    except DP800Error as error_msg:
        print(f"Error: {error_msg}", file=sys.stderr)
        sys.exit(1)
    finally:
        if 'controller' in locals():
            controller.disconnect()


def is_color_enabled(config_color_value):
    """Check if color is enabled based on configuration value."""
    if config_color_value is None:
        return True  # Default to enabled

    # Convert to lowercase string and check for true values
    color_str = str(config_color_value).lower().strip()
    return color_str in ['true', '1', 'on']


def supports_color():
    """Check if the terminal supports ANSI color codes and color is enabled."""
    # Load config to check color setting
    config_values = load_config()

    # Check configuration setting first
    if not is_color_enabled(config_values.get('color')):
        return False

    # Check if stdout is a TTY and TERM is set appropriately
    if not sys.stdout.isatty():
        return False

    # Check for NO_COLOR environment variable
    if os.environ.get('NO_COLOR'):
        return False

    # Check TERM environment variable
    term = os.environ.get('TERM', '')
    return 'color' in term or term in ['xterm', 'xterm-256color', 'screen', 'tmux']


def get_channel_color(channel):
    """Get ANSI color code for a channel."""
    if not supports_color():
        return '', ''

    # ANSI color codes
    colors = {
        1: '\033[33m',  # Yellow
        2: '\033[36m',  # Cyan
        3: '\033[35m',  # Magenta
    }
    reset = '\033[0m'   # Reset to default

    return colors.get(channel, ''), reset


def print_channel_state(state):
    """Print formatted channel state information with color coding."""
    channel = state['channel']
    color_start, color_end = get_channel_color(channel)

    # Bold ANSI codes for highlighting output enabled status
    if supports_color():
        bold_start = '\033[1m'
        bold_end = '\033[22m'  # Turn off bold, preserve other formatting
    else:
        bold_start = bold_end = ''

    print(f"{color_start}Channel {channel}:")
    print(f"  Output Enabled:  {bold_start}{state['output_enabled']}{bold_end}")
    print(f"  Set Voltage:     {state['set_voltage']:>8.3f} V")
    print(f"  Set Current:     {state['set_current']:>8.3f} A")
    print(f"  OVP Value:       {state['ovp_value']:>8.3f} V")
    print(f"  OVP Enabled:     {state['ovp_enabled']}")
    print(f"  OCP Value:       {state['ocp_value']:>8.3f} A")
    print(f"  OCP Enabled:     {state['ocp_enabled']}{color_end}")


def load_config():
    """Load configuration from .dp800config files."""
    config = configparser.ConfigParser()

    # Default values
    defaults = {
        'ip': '192.168.0.55',
        'port': '5555',
        'color': 'true',
        'screenshotviewer': ''
    }

    # Search order: local directory, then home directory
    config_paths = [
        Path('.dp800config'),
        Path.home() / '.dp800config'
    ]

    for config_path in config_paths:
        if config_path.exists():
            try:
                config.read(config_path)
                break
            except configparser.Error:
                # If config file is malformed, continue to next location
                continue

    # Get values from config, falling back to defaults
    if config.has_section('device'):
        device_section = dict(config['device'])
    else:
        device_section = {}

    if config.has_section('display'):
        display_section = dict(config['display'])
    else:
        display_section = {}

    if config.has_section('tools'):
        tools_section = dict(config['tools'])
    else:
        tools_section = {}

    return {
        'ip': device_section.get('ip', defaults['ip']),
        'port': int(device_section.get('port', defaults['port'])),
        'color': display_section.get('color', defaults['color']),
        'screenshotviewer': tools_section.get('screenshotviewer', defaults['screenshotviewer'])
    }


def main():
    """Main CLI entry point."""
    # Load configuration
    config_values = load_config()

    parser = argparse.ArgumentParser(
        description="CLI tool for interacting with Rigol DP832A power supply"
    )

    # Global arguments
    parser.add_argument(
        '--ip',
        default=config_values['ip'],
        help=f'IP address of the DP832A device (default: {config_values["ip"]})'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=config_values['port'],
        help=f'Port number for SCPI communication (default: {config_values["port"]})'
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

    # On command
    on_parser = subparsers.add_parser('on', help='Turn channel output on')
    on_parser.add_argument(
        'channel',
        help='Channel number (1-3) or "all" for all channels'
    )
    on_parser.set_defaults(func=cmd_on)

    # Off command
    off_parser = subparsers.add_parser('off', help='Turn channel output off')
    off_parser.add_argument(
        'channel',
        help='Channel number (1-3) or "all" for all channels'
    )
    off_parser.set_defaults(func=cmd_off)

    # Set command
    set_parser = subparsers.add_parser('set', help='Set channel voltage and/or current')
    set_parser.add_argument(
        'channel',
        type=int,
        choices=[1, 2, 3],
        help='Channel number (1-3)'
    )
    set_parser.add_argument(
        '-v', '--voltage',
        type=float,
        help='Voltage to set in volts'
    )
    set_parser.add_argument(
        '-c', '--current',
        type=float,
        help='Current to set in amps'
    )
    set_parser.set_defaults(func=cmd_set)

    # Parse arguments
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    # Execute the command
    args.func(args)


if __name__ == "__main__":
    main()
