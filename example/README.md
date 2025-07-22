# Configuration Example

This directory contains example configuration files for the DP800 CLI tool.

## Configuration File

The `dp800config` file in this directory is an example configuration file that shows all available options with their default values and explanations.

## Installation

To use the configuration file, copy it to one of these locations and rename it:

1. **Local configuration** (recommended for project-specific settings):
   ```bash
   cp example/dp800config .dp800config
   ```

2. **User configuration** (for system-wide personal settings):
   ```bash
   cp example/dp800config ~/.dp800config
   ```

## Priority

Configuration sources are used in this order (highest to lowest priority):

1. Command line arguments (e.g., `--ip 192.168.1.100`)
2. Local configuration file (`.dp800config` in current directory)
3. User configuration file (`~/.dp800config` in home directory)
4. Built-in defaults

## Format

The configuration file uses standard INI format with sections and key-value pairs:

```ini
[device]
ip = 192.168.0.55
port = 5555
```

Comments are supported using `#` at the beginning of a line.