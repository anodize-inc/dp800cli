#!/usr/bin/env python3
"""Library for SCPI communication with Rigol DP832A power supply."""

import pyvisa


class DP800Error(Exception):
    """Custom exception for DP800 operations."""


class DP800Controller:
    """Controller class for Rigol DP832A power supply SCPI operations."""

    # Valid device identifiers for DP832A
    VALID_DEVICE_MODELS = {'DP832A'}
    VALID_MANUFACTURER = 'RIGOL TECHNOLOGIES'

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
