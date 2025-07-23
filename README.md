# DP800CLI - Rigol DP800 Series Power Supply Control

## Overview

DP800CLI is a command-line interface tool for controlling Rigol DP800 series programmable linear DC power supplies over TCP/IP networks using the SCPI (Standard Commands for Programmable Instruments) protocol. This tool provides a convenient way to remotely control your power supply, set voltages and currents, manage channel outputs, capture screenshots, and apply preset configurations without needing to physically interact with the device.

The tool is specifically designed for the DP832A model but should work with other DP800 series devices with minor modifications. It communicates with the power supply via its built-in LAN interface, allowing for automation, remote operation, and integration into test scripts.

Key features:
- Remote control of all channels (voltage, current, output on/off)
- Parameter validation with device-specific limits
- Screenshot capture of the device display
- Preset configuration management
- Multi-channel state monitoring
- Configuration file support for common settings
- Color-coded output for better readability

## Usage

### Installation

1. Ensure Python 3 is installed on your system
2. Install required dependencies:
   ```bash
   pip install pyvisa pyvisa-py
   ```
3. Clone this repository and make the main script executable:
   ```bash
   chmod +x dp800cli.py
   ```

### Basic Commands

The tool uses a subcommand structure. Here are all available commands:

#### Device Identification
```bash
./dp800cli.py id
```
Connects to the device and displays its identification string.

#### Channel State
```bash
./dp800cli.py state              # Show all channels
./dp800cli.py state -c 1          # Show only channel 1
```
Displays detailed state information including voltage, current, OVP/OCP settings, and output status.

#### Setting Channel Parameters
```bash
./dp800cli.py set 1 -v 12.0              # Set channel 1 to 12V
./dp800cli.py set 1 -c 0.5               # Set channel 1 to 0.5A
./dp800cli.py set 1 -v 12.0 -c 0.5       # Set both voltage and current
./dp800cli.py set 1                      # Query current settings for channel 1
```
Sets or queries channel voltage and current. The tool validates parameters against channel limits:
- Channels 1-2: 0-32V, 0-3.2A
- Channel 3: 0-5.3V, 0-3.2A

#### Channel Output Control
```bash
./dp800cli.py on 1               # Turn on channel 1
./dp800cli.py on all             # Turn on all channels
./dp800cli.py off 2              # Turn off channel 2
./dp800cli.py off all            # Turn off all channels
```

#### Preset Management
```bash
./dp800cli.py preset 0            # Apply DEFAULT preset
./dp800cli.py preset 1            # Apply USER1 preset
./dp800cli.py preset 2            # Apply USER2 preset
```
Applies device presets (0=DEFAULT, 1-4=USER1-USER4).

#### Screenshot Capture
```bash
./dp800cli.py screenshot                           # Auto-named file
./dp800cli.py screenshot -o measurement.bmp        # Custom filename
```
Captures a screenshot of the device display and saves it as a BMP file. Can optionally open the image in a configured viewer.

### Global Options

All commands support these global options:
```bash
--ip ADDRESS      # Device IP address (default: from config or 192.168.0.55)
--port PORT       # SCPI port number (default: from config or 5555)
--help, -h        # Show help message
```

Example with global options:
```bash
./dp800cli.py --ip 192.168.1.100 --port 5555 state
```

## Configuration File

The tool supports optional configuration files to store common settings. Configuration files are searched in this order:
1. `.dp800config` in the current directory
2. `~/.dp800config` in your home directory

### Configuration File Format

The configuration file uses INI format with three sections:

```ini
[device]
# IP address of the DP832A power supply
ip = 192.168.0.55

# Port number for SCPI communication
port = 5555

[display]
# Enable color output (true/false, 1/0, on/off)
color = true

[tools]
# Screenshot viewer command
# Use {filename} as placeholder for the screenshot filename
screenshotviewer = eog {filename}

# Enable debug mode for screenshot viewer (true/false, 1/0, on/off)
# When enabled, shows viewer application output on console
screenshotdebug = false
```

### Configuration Options

#### [device] Section
- `ip`: IP address of your DP832A device
- `port`: SCPI communication port (typically 5555 for Rigol devices)

#### [display] Section
- `color`: Enable/disable color output in terminal (useful for scripts or terminals without color support)

#### [tools] Section
- `screenshotviewer`: Command to automatically open screenshots after capture
  - Linux example: `eog {filename}` or `feh {filename}`
  - macOS example: `open {filename}`
  - Windows example: `start {filename}`
- `screenshotdebug`: Show/hide screenshot viewer output (useful for debugging viewer issues)

### Example Configuration

A complete example configuration file is provided in `example/dp800config`. Copy this to one of the configuration locations and modify it for your setup:

```bash
cp example/dp800config ~/.dp800config
# Edit ~/.dp800config with your device's IP address and preferred settings
```

Command-line arguments always override configuration file settings, allowing you to temporarily use different values without modifying the configuration.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2025 Steve deRosier