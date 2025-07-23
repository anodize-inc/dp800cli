#!/usr/bin/env python3
"""Library for SCPI communication with Rigol DP832A power supply."""

import time
from datetime import datetime

import pyvisa


class DP800Error(Exception):
    """Custom exception for DP800 operations."""


class DP800Controller:
    """Controller class for Rigol DP832A power supply SCPI operations."""

    # Valid device identifiers for DP832A
    VALID_DEVICE_MODELS = {'DP832A'}
    VALID_MANUFACTURER = 'RIGOL TECHNOLOGIES'

    # DP832A channel specifications from Table 2-1
    CHANNEL_SPECS = {
        1: {'voltage_min': 0.0, 'voltage_max': 32.0, 'current_min': 0.0, 'current_max': 3.2},
        2: {'voltage_min': 0.0, 'voltage_max': 32.0, 'current_min': 0.0, 'current_max': 3.2},
        3: {'voltage_min': 0.0, 'voltage_max': 5.3, 'current_min': 0.0, 'current_max': 3.2}
    }

    def __init__(self, ip_address='192.168.0.55', port=5555):
        """Initialize the controller with device connection parameters.

        Args:
            ip_address (str): IP address of the device
            port (int): Port number for SCPI communication
        """
        self.ip_address = ip_address
        self.port = port
        self.resource_manager = None
        self.instrument = None
        self.resource_name = f'TCPIP::{ip_address}::{port}::SOCKET'

    def connect(self):
        """Connect to the device and configure communication parameters.

        Raises:
            DP800Error: If connection fails
        """
        try:
            self.resource_manager = pyvisa.ResourceManager('@py')
            self.instrument = self.resource_manager.open_resource(self.resource_name)
            self.instrument.read_termination = '\n'
            self.instrument.write_termination = '\n'
        except pyvisa.errors.VisaIOError as error_msg:
            raise DP800Error(
                f"Failed to connect to device at {self.resource_name}: {error_msg}"
            ) from error_msg

    def disconnect(self):
        """Disconnect from the device and clean up resources."""
        if self.instrument:
            try:
                self.instrument.close()
            except (pyvisa.errors.VisaIOError, AttributeError):
                pass  # Ignore errors during cleanup
            finally:
                self.instrument = None

        if self.resource_manager:
            try:
                self.resource_manager.close()
            except (pyvisa.errors.VisaIOError, AttributeError):
                pass  # Ignore errors during cleanup
            finally:
                self.resource_manager = None

    def get_device_id(self):
        """Query device identification using *IDN? SCPI command.

        Returns:
            str: Device identification string

        Raises:
            DP800Error: If device is not connected or query fails
        """
        if not self.instrument:
            raise DP800Error("Device not connected. Call connect() first.")

        try:
            device_id = self.instrument.query('*IDN?').strip()
            return device_id
        except pyvisa.errors.VisaIOError as error_msg:
            raise DP800Error(
                f"Failed to query device identification: {error_msg}"
            ) from error_msg

    def validate_device_id(self, device_id):
        """Validate that the device ID corresponds to a supported DP832A.

        Args:
            device_id (str): Device identification string from *IDN? query

        Raises:
            DP800Error: If device is not a supported model
        """
        if not device_id:
            raise DP800Error("Empty device identification string")

        # Parse IDN response: "RIGOL TECHNOLOGIES,DP832A,DP8B264501878,00.01.19"
        # Only validate manufacturer and model (first 2 parts), ignore serial and firmware
        parts = device_id.split(',')
        if len(parts) < 2:
            raise DP800Error(f"Invalid device identification format: {device_id}")

        manufacturer = parts[0].strip()
        model = parts[1].strip()

        if manufacturer != self.VALID_MANUFACTURER:
            raise DP800Error(
                f"Unsupported manufacturer '{manufacturer}'. "
                f"Expected '{self.VALID_MANUFACTURER}'. Device ID: {device_id}"
            )

        if model not in self.VALID_DEVICE_MODELS:
            raise DP800Error(
                f"Unsupported device model '{model}'. "
                f"Expected one of {self.VALID_DEVICE_MODELS}. Device ID: {device_id}"
            )

    def get_channel_state(self, channel):
        """Get complete state information for a specific channel.

        Args:
            channel (int): Channel number (1-3 for DP832A)

        Returns:
            dict: Channel state with voltage, current, OVP, OCP settings and status

        Raises:
            DP800Error: If device is not connected or query fails
        """
        if not self.instrument:
            raise DP800Error("Device not connected. Call connect() first.")

        if not 1 <= channel <= 3:
            raise DP800Error(f"Invalid channel {channel}. Must be 1-3 for DP832A.")

        try:
            # Query all channel state parameters
            set_voltage = float(self.instrument.query(f':SOUR{channel}:VOLT?').strip())
            set_current = float(self.instrument.query(f':SOUR{channel}:CURR?').strip())
            ovp_value = float(self.instrument.query(f':SOUR{channel}:VOLT:PROT?').strip())
            ocp_value = float(self.instrument.query(f':SOUR{channel}:CURR:PROT?').strip())
            ovp_status = self.instrument.query(f':SOUR{channel}:VOLT:PROT:STAT?').strip()
            ocp_status = self.instrument.query(f':SOUR{channel}:CURR:PROT:STAT?').strip()
            ovp_enabled = ovp_status.upper() == 'ON'
            ocp_enabled = ocp_status.upper() == 'ON'
            output_enabled = self.get_output_state(channel)

            return {
                'channel': channel,
                'set_voltage': set_voltage,
                'set_current': set_current,
                'ovp_value': ovp_value,
                'ocp_value': ocp_value,
                'ovp_enabled': ovp_enabled,
                'ocp_enabled': ocp_enabled,
                'output_enabled': output_enabled
            }

        except (pyvisa.errors.VisaIOError, ValueError) as error_msg:
            raise DP800Error(
                f"Failed to query channel {channel} state: {error_msg}"
            ) from error_msg

    def get_all_channels_state(self):
        """Get state information for all channels (1-3).

        Returns:
            list: List of channel state dictionaries

        Raises:
            DP800Error: If device is not connected or query fails
        """
        return [self.get_channel_state(channel) for channel in range(1, 4)]

    def take_screenshot(self, filename=None):
        """Take a screenshot of the device display and save as BMP file.

        Args:
            filename (str, optional): Output filename. If None, generates timestamp-based name.

        Returns:
            str: The filename of the saved screenshot

        Raises:
            DP800Error: If device is not connected or screenshot fails
        """
        if not self.instrument:
            raise DP800Error("Device not connected. Call connect() first.")

        if filename is None:
            timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            filename = f"screenshot_{self.ip_address}_{timestamp}.bmp"

        try:
            # Send screenshot command and get binary response
            self.instrument.write(':SYSTem:PRINT? BMP')

            # Read raw binary data
            raw_data = self.instrument.read_raw()

            # Parse TMC header to find actual image data
            # TMC format: '#' + length_of_length + length + data
            if raw_data[0:1] != b'#':
                raise DP800Error("Invalid TMC header in screenshot data")

            # Get the length of the length field
            length_of_header = int(chr(raw_data[1]))

            # Skip TMC header to get to actual BMP data
            header_size = 2 + length_of_header
            bmp_data = raw_data[header_size:]

            # Write BMP data to file
            with open(filename, 'wb') as file:
                file.write(bmp_data)

            return filename

        except (pyvisa.errors.VisaIOError, IOError, ValueError) as error_msg:
            raise DP800Error(f"Failed to take screenshot: {error_msg}") from error_msg

    def set_output_state(self, channel, state):
        """Turn a channel output on or off.

        Args:
            channel (int): Channel number (1-3 for DP832A)
            state (bool): True to turn on, False to turn off

        Raises:
            DP800Error: If device is not connected or command fails
        """
        if not self.instrument:
            raise DP800Error("Device not connected. Call connect() first.")

        if not 1 <= channel <= 3:
            raise DP800Error(f"Invalid channel {channel}. Must be 1-3 for DP832A.")

        try:
            state_cmd = "ON" if state else "OFF"
            self.instrument.write(f':OUTP CH{channel},{state_cmd}')
        except pyvisa.errors.VisaIOError as error_msg:
            action = "enable" if state else "disable"
            raise DP800Error(
                f"Failed to {action} channel {channel} output: {error_msg}"
            ) from error_msg

    def set_all_outputs_state(self, state):
        """Turn all channel outputs on or off.

        Args:
            state (bool): True to turn on, False to turn off

        Raises:
            DP800Error: If device is not connected or command fails
        """
        for channel in range(1, 4):
            self.set_output_state(channel, state)

    def get_output_state(self, channel):
        """Get the output state for a specific channel.

        Args:
            channel (int): Channel number (1-3 for DP832A)

        Returns:
            bool: True if output is on, False if off

        Raises:
            DP800Error: If device is not connected or query fails
        """
        if not self.instrument:
            raise DP800Error("Device not connected. Call connect() first.")

        if not 1 <= channel <= 3:
            raise DP800Error(f"Invalid channel {channel}. Must be 1-3 for DP832A.")

        try:
            response = self.instrument.query(f':OUTP? CH{channel}').strip()
            return response.upper() == 'ON'
        except pyvisa.errors.VisaIOError as error_msg:
            raise DP800Error(
                f"Failed to query channel {channel} output state: {error_msg}"
            ) from error_msg

    def _validate_channel_parameters(self, channel, voltage, current):
        """Validate channel parameters against specifications.

        Args:
            channel (int): Channel number (1-3 for DP832A)
            voltage (float, optional): Voltage to validate
            current (float, optional): Current to validate

        Raises:
            DP800Error: If parameters are out of range
        """
        specs = self.CHANNEL_SPECS[channel]

        if voltage is not None:
            if not specs['voltage_min'] <= voltage <= specs['voltage_max']:
                raise DP800Error(
                    f"Voltage {voltage}V out of range for channel {channel}. "
                    f"Valid range: {specs['voltage_min']}V to {specs['voltage_max']}V"
                )

        if current is not None:
            if not specs['current_min'] <= current <= specs['current_max']:
                raise DP800Error(
                    f"Current {current}A out of range for channel {channel}. "
                    f"Valid range: {specs['current_min']}A to {specs['current_max']}A"
                )

    def _verify_channel_settings(self, channel, voltage, current):
        """Verify that channel settings were applied correctly.

        Args:
            channel (int): Channel number (1-3 for DP832A)
            voltage (float, optional): Expected voltage value
            current (float, optional): Expected current value

        Raises:
            DP800Error: If verification fails
        """
        if voltage is not None:
            actual_voltage = float(self.instrument.query(f':SOUR{channel}:VOLT?').strip())
            if abs(actual_voltage - voltage) > 0.001:  # Allow small floating point differences
                raise DP800Error(
                    f"Verification failed: Set voltage {voltage}V "
                    f"but device reports {actual_voltage}V"
                )

        if current is not None:
            actual_current = float(self.instrument.query(f':SOUR{channel}:CURR?').strip())
            if abs(actual_current - current) > 0.0001:  # Allow small floating point differences
                raise DP800Error(
                    f"Verification failed: Set current {current}A "
                    f"but device reports {actual_current}A"
                )

    def set_channel_parameters(self, channel, voltage=None, current=None):
        """Set channel voltage and/or current using :SOURce commands.

        Args:
            channel (int): Channel number (1-3 for DP832A)
            voltage (float, optional): Voltage to set in volts
            current (float, optional): Current to set in amps

        Raises:
            DP800Error: If device is not connected or command fails
        """
        if not self.instrument:
            raise DP800Error("Device not connected. Call connect() first.")

        if not 1 <= channel <= 3:
            raise DP800Error(f"Invalid channel {channel}. Must be 1-3 for DP832A.")

        if voltage is None and current is None:
            raise DP800Error("Must specify at least one of voltage or current")

        # Validate parameters against channel specifications
        self._validate_channel_parameters(channel, voltage, current)

        try:
            if voltage is not None:
                self.instrument.write(f':SOUR{channel}:VOLT {voltage}')

            if current is not None:
                self.instrument.write(f':SOUR{channel}:CURR {current}')

            # Allow time for device to process the settings
            time.sleep(0.5)  # 500 milliseconds

            # Verify the settings were applied correctly
            self._verify_channel_settings(channel, voltage, current)

        except pyvisa.errors.VisaIOError as error_msg:
            raise DP800Error(
                f"Failed to set channel {channel} parameters: {error_msg}"
            ) from error_msg

    def get_channel_parameters(self, channel):
        """Get current channel parameters using :APPL? command.

        Args:
            channel (int): Channel number (1-3 for DP832A)

        Returns:
            str: Channel parameters information from device

        Raises:
            DP800Error: If device is not connected or query fails
        """
        if not self.instrument:
            raise DP800Error("Device not connected. Call connect() first.")

        if not 1 <= channel <= 3:
            raise DP800Error(f"Invalid channel {channel}. Must be 1-3 for DP832A.")

        try:
            response = self.instrument.query(f':APPL? CH{channel}').strip()
            return response
        except pyvisa.errors.VisaIOError as error_msg:
            raise DP800Error(
                f"Failed to query channel {channel} parameters: {error_msg}"
            ) from error_msg

    def apply_preset(self, preset_value):
        """Apply a preset configuration to the device.

        Args:
            preset_value (int): Preset number (0=DEFAULT, 1-4=USER1-USER4)

        Raises:
            DP800Error: If device is not connected or command fails
        """
        if not self.instrument:
            raise DP800Error("Device not connected. Call connect() first.")

        if not 0 <= preset_value <= 4:
            raise DP800Error(f"Invalid preset value {preset_value}. Must be 0-4.")

        # Map preset values to command strings
        preset_map = {
            0: 'DEFAULT',
            1: 'USER1',
            2: 'USER2',
            3: 'USER3',
            4: 'USER4'
        }

        preset_name = preset_map[preset_value]

        try:
            # Step 1: Set the preset key
            self.instrument.write(f':PRES:KEY {preset_name}')

            # Step 2: Allow time for command processing
            time.sleep(0.1)  # 100 milliseconds

            # Step 3: Apply the preset
            self.instrument.write(':PRES')

        except pyvisa.errors.VisaIOError as error_msg:
            raise DP800Error(
                f"Failed to apply preset {preset_value} ({preset_name}): {error_msg}"
            ) from error_msg
