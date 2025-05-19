"""
Topology Manager module for AutoNetLab.

This module provides classes for defining, loading, and validating
network lab topologies.
"""

import os
import json
from typing import Dict, List, Any, Optional, Set, Tuple

import yaml

from ..utils.logger import setup_logger


class TopologyValidationError(Exception):
    """Exception raised for topology validation errors."""
    pass


class TopologyManager:
    """
    Class for managing network topology definitions.
    
    This class provides methods for loading, validating, and working with
    network lab topology definitions.
    """
    
    def __init__(self, logger=None):
        """
        Initialize a TopologyManager instance.
        
        Args:
            logger (logging.Logger, optional): Logger instance. If None, a new logger will be created.
        """
        self.logger = logger or setup_logger("topology_manager")
        self.topology = None
    
    def load_topology(self, topology_file: str) -> Dict[str, Any]:
        """
        Load a topology definition from a file (YAML or JSON).
        
        Args:
            topology_file (str): Path to the topology definition file.
            
        Returns:
            dict: The loaded topology definition.
            
        Raises:
            FileNotFoundError: If the topology file doesn't exist.
            ValueError: If the file format is not supported.
        """
        self.logger.info(f"Loading topology from {topology_file}")
        
        # Check if file exists
        if not os.path.isfile(topology_file):
            error_msg = f"Topology file not found: {topology_file}"
            self.logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        # Determine file type based on extension
        file_extension = os.path.splitext(topology_file)[1].lower()
        
        try:
            # Parse YAML file
            if file_extension in ['.yaml', '.yml']:
                with open(topology_file, 'r') as file:
                    self.topology = yaml.safe_load(file)
            
            # Parse JSON file
            elif file_extension == '.json':
                with open(topology_file, 'r') as file:
                    self.topology = json.load(file)
            
            else:
                error_msg = f"Unsupported file format: {file_extension}. Use YAML or JSON."
                self.logger.error(error_msg)
                raise ValueError(error_msg)
            
            self.logger.info(f"Successfully loaded topology with {len(self.topology.get('devices', []))} devices")
            return self.topology
            
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            error_msg = f"Error parsing topology file: {str(e)}"
            self.logger.error(error_msg)
            raise
    
    def validate_topology(self) -> bool:
        """
        Validate the loaded topology for required elements and logical consistency.
        
        Returns:
            bool: True if the topology is valid, False otherwise.
            
        Raises:
            TopologyValidationError: If the topology is invalid.
            ValueError: If no topology has been loaded.
        """
        if not self.topology:
            error_msg = "No topology loaded. Call load_topology() first."
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        self.logger.info("Validating topology...")
        
        try:
            # Check for required top-level keys
            required_keys = ['name', 'devices', 'connections']
            missing_keys = [key for key in required_keys if key not in self.topology]
            if missing_keys:
                error_msg = f"Missing required topology keys: {missing_keys}"
                self.logger.error(error_msg)
                raise TopologyValidationError(error_msg)
            
            # Validate devices
            if not isinstance(self.topology['devices'], dict):
                error_msg = "'devices' must be a dictionary mapping device names to configurations"
                self.logger.error(error_msg)
                raise TopologyValidationError(error_msg)
            
            # Check that all devices have the required properties
            for device_name, device_config in self.topology['devices'].items():
                required_device_props = ['type', 'management']
                missing_props = [prop for prop in required_device_props if prop not in device_config]
                if missing_props:
                    error_msg = f"Device '{device_name}' is missing required properties: {missing_props}"
                    self.logger.error(error_msg)
                    raise TopologyValidationError(error_msg)
            
            # Validate connections
            if not isinstance(self.topology['connections'], list):
                error_msg = "'connections' must be a list of connection definitions"
                self.logger.error(error_msg)
                raise TopologyValidationError(error_msg)
            
            # Check that all connections reference valid devices
            device_names = set(self.topology['devices'].keys())
            for i, connection in enumerate(self.topology['connections']):
                if not isinstance(connection, dict):
                    error_msg = f"Connection #{i} must be a dictionary"
                    self.logger.error(error_msg)
                    raise TopologyValidationError(error_msg)
                
                if 'endpoints' not in connection:
                    error_msg = f"Connection #{i} is missing 'endpoints'"
                    self.logger.error(error_msg)
                    raise TopologyValidationError(error_msg)
                
                # Validate endpoints
                for endpoint in connection['endpoints']:
                    if 'device' not in endpoint:
                        error_msg = f"Endpoint in connection #{i} is missing 'device'"
                        self.logger.error(error_msg)
                        raise TopologyValidationError(error_msg)
                    
                    if endpoint['device'] not in device_names:
                        error_msg = f"Connection #{i} references non-existent device: {endpoint['device']}"
                        self.logger.error(error_msg)
                        raise TopologyValidationError(error_msg)
            
            self.logger.info("Topology validation successful")
            return True
            
        except Exception as e:
            if not isinstance(e, TopologyValidationError):
                error_msg = f"Unexpected error during topology validation: {str(e)}"
                self.logger.error(error_msg)
                raise TopologyValidationError(error_msg) from e
            raise
    
    def get_device_connections(self, device_name: str) -> List[Dict[str, Any]]:
        """
        Get all connections for a specific device.
        
        Args:
            device_name (str): The name of the device.
            
        Returns:
            list: List of connection definitions that include the device.
            
        Raises:
            ValueError: If no topology has been loaded or the device doesn't exist.
        """
        if not self.topology:
            error_msg = "No topology loaded. Call load_topology() first."
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        if device_name not in self.topology.get('devices', {}):
            error_msg = f"Device '{device_name}' not found in the topology"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        device_connections = []
        for connection in self.topology.get('connections', []):
            # Check if this device is in the connection endpoints
            if any(endpoint.get('device') == device_name for endpoint in connection.get('endpoints', [])):
                device_connections.append(connection)
        
        self.logger.info(f"Found {len(device_connections)} connections for device '{device_name}'")
        return device_connections
    
    def get_connected_devices(self, device_name: str) -> List[str]:
        """
        Get all devices directly connected to the specified device.
        
        Args:
            device_name (str): The name of the device.
            
        Returns:
            list: List of device names that are directly connected to the specified device.
            
        Raises:
            ValueError: If no topology has been loaded or the device doesn't exist.
        """
        # Get all connections for this device
        connections = self.get_device_connections(device_name)
        
        connected_devices = set()
        for connection in connections:
            for endpoint in connection.get('endpoints', []):
                endpoint_device = endpoint.get('device')
                if endpoint_device and endpoint_device != device_name:
                    connected_devices.add(endpoint_device)
        
        self.logger.info(f"Device '{device_name}' is directly connected to {len(connected_devices)} devices")
        return list(connected_devices)
    
    def verify_connectivity_path(self, source_device: str, target_device: str) -> Tuple[bool, List[str]]:
        """
        Verify if there is a connectivity path between two devices in the topology.
        
        Args:
            source_device (str): The name of the source device.
            target_device (str): The name of the target device.
            
        Returns:
            tuple: A tuple containing (success, path), where:
                success (bool): True if a path exists, False otherwise.
                path (list): List of device names forming the path from source to target.
                
        Raises:
            ValueError: If no topology has been loaded or devices don't exist.
        """
        if not self.topology:
            error_msg = "No topology loaded. Call load_topology() first."
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Verify both devices exist in the topology
        device_names = set(self.topology.get('devices', {}).keys())
        if source_device not in device_names:
            error_msg = f"Source device '{source_device}' not found in the topology"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        if target_device not in device_names:
            error_msg = f"Target device '{target_device}' not found in the topology"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        # If source and target are the same, return immediately
        if source_device == target_device:
            self.logger.info(f"Source and target are the same device: {source_device}")
            return True, [source_device]
        
        # Perform breadth-first search to find the shortest path
        self.logger.info(f"Finding connectivity path from '{source_device}' to '{target_device}'")
        
        # Set up for BFS
        queue = [(source_device, [source_device])]  # (current device, path so far)
        visited = {source_device}
        
        while queue:
            current_device, path = queue.pop(0)
            
            # Get all directly connected devices
            connected_devices = self.get_connected_devices(current_device)
            
            for next_device in connected_devices:
                if next_device == target_device:
                    # Found the target device
                    full_path = path + [next_device]
                    self.logger.info(f"Found connectivity path: {' -> '.join(full_path)}")
                    return True, full_path
                
                if next_device not in visited:
                    visited.add(next_device)
                    queue.append((next_device, path + [next_device]))
        
        # If we've exhausted all possibilities without finding the target
        self.logger.warning(f"No connectivity path found from '{source_device}' to '{target_device}'")
        return False, []
    
    def export_topology(self, output_file: str, format_type: str = 'yaml') -> None:
        """
        Export the current topology to a file.
        
        Args:
            output_file (str): Path to the output file.
            format_type (str): Format to export ('yaml' or 'json').
            
        Raises:
            ValueError: If no topology has been loaded or format_type is unsupported.
        """
        if not self.topology:
            error_msg = "No topology loaded. Call load_topology() first."
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        self.logger.info(f"Exporting topology to {output_file} in {format_type} format")
        
        try:
            # Create directory if it doesn't exist
            output_dir = os.path.dirname(output_file)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            if format_type.lower() == 'yaml':
                with open(output_file, 'w') as file:
                    yaml.dump(self.topology, file, default_flow_style=False)
            elif format_type.lower() == 'json':
                with open(output_file, 'w') as file:
                    json.dump(self.topology, file, indent=2)
            else:
                error_msg = f"Unsupported format: {format_type}. Use 'yaml' or 'json'."
                self.logger.error(error_msg)
                raise ValueError(error_msg)
                
            self.logger.info(f"Topology exported successfully to {output_file}")
            
        except Exception as e:
            error_msg = f"Error exporting topology: {str(e)}"
            self.logger.error(error_msg)
            raise

