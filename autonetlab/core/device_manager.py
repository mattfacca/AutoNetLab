"""
Device Manager module for AutoNetLab.

This module provides classes for managing connections to network devices
and performing configuration operations on them.
"""

import time
from typing import Dict, List, Optional, Union, Any

import netmiko
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException

from ..utils.logger import setup_logger


class DeviceConnectionError(Exception):
    """Exception raised for device connection errors."""
    pass


class DeviceManager:
    """
    Class for managing network device connections and configurations.
    
    This class handles connections to network devices using Netmiko,
    and provides methods for configuring and validating device status.
    """
    
    def __init__(self, logger=None):
        """
        Initialize a DeviceManager instance.
        
        Args:
            logger (logging.Logger, optional): Logger instance. If None, a new logger will be created.
        """
        self.logger = logger or setup_logger("device_manager")
        self.connections = {}  # Store active connections
    
    def connect(self, device_params: Dict[str, Any]) -> netmiko.BaseConnection:
        """
        Connect to a network device using the provided parameters.
        
        Args:
            device_params (dict): Dictionary containing device connection parameters.
                Must include 'device_type', 'host', 'username', and 'password'.
                
        Returns:
            netmiko.BaseConnection: Connected device object.
            
        Raises:
            DeviceConnectionError: If connection to the device fails.
        """
        device_name = device_params.get('host', 'unknown')
        self.logger.info(f"Connecting to device: {device_name}")
        
        # Ensure required parameters are present
        required_params = ['device_type', 'host', 'username', 'password']
        for param in required_params:
            if param not in device_params:
                raise ValueError(f"Missing required parameter: {param}")
        
        try:
            # Attempt to connect to the device
            connection = ConnectHandler(**device_params)
            self.logger.info(f"Successfully connected to {device_name}")
            
            # Store the connection for future use
            self.connections[device_name] = connection
            return connection
            
        except NetmikoTimeoutException:
            error_msg = f"Connection to {device_name} timed out"
            self.logger.error(error_msg)
            raise DeviceConnectionError(error_msg)
            
        except NetmikoAuthenticationException:
            error_msg = f"Authentication failed for {device_name}"
            self.logger.error(error_msg)
            raise DeviceConnectionError(error_msg)
            
        except Exception as e:
            error_msg = f"Failed to connect to {device_name}: {str(e)}"
            self.logger.error(error_msg)
            raise DeviceConnectionError(error_msg)
    
    def get_connection(self, device_name: str) -> Optional[netmiko.BaseConnection]:
        """
        Get an existing connection to a device.
        
        Args:
            device_name (str): The name or IP of the device.
            
        Returns:
            netmiko.BaseConnection or None: The connection object if it exists, else None.
        """
        connection = self.connections.get(device_name)
        if not connection:
            self.logger.warning(f"No existing connection found for {device_name}")
        return connection
    
    def configure(self, device_name: str, commands: List[str], config_type: str = "commands") -> str:
        """
        Configure a device with the provided commands.
        
        Args:
            device_name (str): The name or IP of the device to configure.
            commands (list): List of configuration commands to execute.
            config_type (str): Type of configuration ('commands' or 'file').
                
        Returns:
            str: Output from the configuration commands.
            
        Raises:
            DeviceConnectionError: If no connection exists for the device.
            ValueError: If an invalid config_type is provided.
        """
        connection = self.get_connection(device_name)
        if not connection:
            raise DeviceConnectionError(f"No connection exists for {device_name}")
        
        self.logger.info(f"Configuring device {device_name} with {len(commands)} commands")
        
        try:
            if config_type == "commands":
                output = connection.send_config_set(commands)
            elif config_type == "file":
                output = connection.send_config_from_file(commands[0])  # First element should be the filename
            else:
                raise ValueError(f"Invalid config_type: {config_type}. Must be 'commands' or 'file'")
            
            self.logger.info(f"Configuration successful for {device_name}")
            return output
            
        except Exception as e:
            error_msg = f"Error configuring {device_name}: {str(e)}"
            self.logger.error(error_msg)
            raise
    
    def execute_command(self, device_name: str, command: str) -> str:
        """
        Execute a single command on the device.
        
        Args:
            device_name (str): The name or IP of the device.
            command (str): Command to execute.
                
        Returns:
            str: Output from the command.
            
        Raises:
            DeviceConnectionError: If no connection exists for the device.
        """
        connection = self.get_connection(device_name)
        if not connection:
            raise DeviceConnectionError(f"No connection exists for {device_name}")
        
        self.logger.info(f"Executing command on {device_name}: {command}")
        
        try:
            output = connection.send_command(command)
            return output
        except Exception as e:
            error_msg = f"Error executing command on {device_name}: {str(e)}"
            self.logger.error(error_msg)
            raise
    
    def validate_connectivity(self, device_name: str, target_ip: str) -> bool:
        """
        Validate connectivity from the device to a target IP.
        
        Args:
            device_name (str): The name or IP of the device to check from.
            target_ip (str): The target IP address to ping.
                
        Returns:
            bool: True if the ping is successful, False otherwise.
        """
        try:
            # Execute ping command on the device
            output = self.execute_command(device_name, f"ping {target_ip}")
            
            # Check if ping was successful (this may need adjusting based on device OS)
            if "Success rate is 0" in output or "0 packets received" in output:
                self.logger.warning(f"Ping from {device_name} to {target_ip} failed")
                return False
            else:
                self.logger.info(f"Ping from {device_name} to {target_ip} successful")
                return True
                
        except Exception as e:
            self.logger.error(f"Error validating connectivity: {str(e)}")
            return False
    
    def disconnect(self, device_name: str = None) -> None:
        """
        Disconnect from a device or all devices if no name specified.
        
        Args:
            device_name (str, optional): Name of the device to disconnect from.
                If None, disconnect from all devices.
        """
        if device_name is not None:
            # Disconnect from a specific device
            connection = self.connections.pop(device_name, None)
            if connection:
                self.logger.info(f"Disconnecting from {device_name}")
                try:
                    connection.disconnect()
                except Exception as e:
                    self.logger.warning(f"Error while disconnecting from {device_name}: {str(e)}")
            else:
                self.logger.warning(f"No connection found for {device_name}")
        else:
            # Disconnect from all devices
            self.logger.info("Disconnecting from all devices")
            for device, connection in list(self.connections.items()):
                try:
                    connection.disconnect()
                    self.logger.info(f"Disconnected from {device}")
                except Exception as e:
                    self.logger.warning(f"Error while disconnecting from {device}: {str(e)}")
            self.connections.clear()

