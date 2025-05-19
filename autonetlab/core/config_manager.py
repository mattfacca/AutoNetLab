"""
Configuration Manager module for AutoNetLab.

This module provides classes for managing, loading, and rendering
network device configuration templates.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

import yaml

from ..utils.logger import setup_logger


class ConfigValidationError(Exception):
    """Exception raised for configuration validation errors."""
    pass


class ConfigManager:
    """
    Class for managing network device configuration templates.
    
    This class provides methods for loading, rendering, and validating
    configuration templates for network devices.
    """
    
    def __init__(self, template_dir: Optional[str] = None, logger=None):
        """
        Initialize a ConfigManager instance.
        
        Args:
            template_dir (str, optional): Path to the directory containing configuration templates.
                If None, will use default template directory.
            logger (logging.Logger, optional): Logger instance. If None, a new logger will be created.
        """
        self.logger = logger or setup_logger("config_manager")
        
        # Set default template directory if none provided
        if template_dir is None:
            # Try to find templates directory, first in project, then in package
            project_templates = os.path.join(os.getcwd(), "templates")
            package_templates = os.path.join(os.path.dirname(__file__), "..", "templates")
            
            if os.path.isdir(project_templates):
                self.template_dir = project_templates
            elif os.path.isdir(package_templates):
                self.template_dir = package_templates
            else:
                self.template_dir = os.getcwd()
                self.logger.warning(f"No template directory found, using current directory: {self.template_dir}")
        else:
            self.template_dir = template_dir
            
        self.logger.info(f"Using template directory: {self.template_dir}")
    
    def load_yaml_file(self, file_path: str) -> Dict[str, Any]:
        """
        Load and parse a YAML file.
        
        Args:
            file_path (str): Path to the YAML file.
            
        Returns:
            dict: Parsed YAML content.
            
        Raises:
            FileNotFoundError: If the file doesn't exist.
            yaml.YAMLError: If there's an error parsing the YAML file.
        """
        self.logger.info(f"Loading YAML file: {file_path}")
        
        try:
            with open(file_path, 'r') as file:
                content = yaml.safe_load(file)
                return content
        except FileNotFoundError:
            self.logger.error(f"File not found: {file_path}")
            raise
        except yaml.YAMLError as e:
            self.logger.error(f"Error parsing YAML file {file_path}: {str(e)}")
            raise
    
    def load_template(self, template_name: str) -> str:
        """
        Load a configuration template file.
        
        Args:
            template_name (str): Name of the template file.
            
        Returns:
            str: Content of the template file.
            
        Raises:
            FileNotFoundError: If the template file doesn't exist.
        """
        # Handle both with and without .txt extension
        if not template_name.endswith(('.txt', '.j2', '.jinja2')):
            template_name += '.txt'
        
        template_path = os.path.join(self.template_dir, template_name)
        self.logger.info(f"Loading template: {template_path}")
        
        try:
            with open(template_path, 'r') as file:
                content = file.read()
                return content
        except FileNotFoundError:
            self.logger.error(f"Template file not found: {template_path}")
            raise
        except Exception as e:
            self.logger.error(f"Error loading template {template_path}: {str(e)}")
            raise
    
    def render_template(self, template_content: str, variables: Dict[str, Any]) -> str:
        """
        Render a template by replacing variables with their values.
        
        Args:
            template_content (str): The template content to render.
            variables (dict): Dictionary mapping variable names to their values.
            
        Returns:
            str: Rendered template with variables replaced.
        """
        self.logger.info(f"Rendering template with {len(variables)} variables")
        
        # Simple variable replacement (format: {variable_name})
        rendered_content = template_content
        
        try:
            # Replace all variables in the template
            for key, value in variables.items():
                placeholder = "{" + key + "}"
                rendered_content = rendered_content.replace(placeholder, str(value))
            
            # Check if there are any unreplaced variables
            unreplaced_vars = re.findall(r'{([^{}]+)}', rendered_content)
            if unreplaced_vars:
                self.logger.warning(f"Unreplaced variables in template: {unreplaced_vars}")
            
            return rendered_content
            
        except Exception as e:
            self.logger.error(f"Error rendering template: {str(e)}")
            raise
    
    def validate_config(self, config: str, device_type: str = "cisco_ios") -> bool:
        """
        Validate a configuration for syntax and logical errors.
        
        Args:
            config (str): The configuration to validate.
            device_type (str): The type of device the configuration is for.
            
        Returns:
            bool: True if the configuration is valid, False otherwise.
            
        Note:
            This is a basic implementation. For real validation, you might need 
            to use vendor-specific tools or more sophisticated methods.
        """
        self.logger.info(f"Validating configuration for {device_type}")
        
        # Basic validation logic - can be expanded for more comprehensive checks
        common_errors = [
            "Invalid input detected",
            "Incomplete command",
            "Ambiguous command",
            "% Invalid"
        ]
        
        # Check for common syntax errors
        for error in common_errors:
            if error in config:
                self.logger.error(f"Configuration validation failed: {error}")
                return False
        
        # Device-specific validation
        if device_type == "cisco_ios":
            # Check for interfaces without IP addresses (if ip address command exists)
            if "interface" in config and "ip address" not in config:
                self.logger.warning("Interface configuration might be missing IP address")
        
        # More validation rules can be added here
        
        self.logger.info("Configuration validation passed")
        return True
    
    def save_config(self, config: str, filename: str, output_dir: Optional[str] = None) -> str:
        """
        Save a rendered configuration to a file.
        
        Args:
            config (str): The configuration content to save.
            filename (str): The name of the file to save to.
            output_dir (str, optional): Directory to save the file to. 
                If None, will save to current directory.
            
        Returns:
            str: Path to the saved file.
            
        Raises:
            IOError: If there's an error writing to the file.
        """
        if output_dir is None:
            output_dir = os.getcwd()
        
        # Make sure the filename has a .txt extension
        if not filename.endswith('.txt'):
            filename += '.txt'
        
        file_path = os.path.join(output_dir, filename)
        self.logger.info(f"Saving configuration to {file_path}")
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Write configuration to file
            with open(file_path, 'w') as file:
                file.write(config)
                
            self.logger.info(f"Configuration saved successfully to {file_path}")
            return file_path
            
        except IOError as e:
            self.logger.error(f"Error saving configuration: {str(e)}")
            raise
    
    def generate_config_from_template(self, template_name: str, variables: Dict[str, Any], 
                                      save_to_file: bool = False, filename: Optional[str] = None) -> str:
        """
        Generate a configuration by loading a template and rendering it with variables.
        
        Args:
            template_name (str): Name of the template file.
            variables (dict): Variables to use for rendering the template.
            save_to_file (bool, optional): Whether to save the rendered config to a file.
            filename (str, optional): Name of the file to save to if save_to_file is True.
                If None and save_to_file is True, will use template_name as filename.
            
        Returns:
            str: The rendered configuration.
            
        Raises:
            FileNotFoundError: If the template file doesn't exist.
            ConfigValidationError: If the rendered configuration is invalid.
        """
        # Load the template
        template_content = self.load_template(template_name)
        
        # Render the template with variables
        rendered_config = self.render_template(template_content, variables)
        
        # Validate the rendered configuration
        if not self.validate_config(rendered_config):
            self.logger.warning("Generated configuration may contain errors")
        
        # Save to file if requested
        if save_to_file:
            if filename is None:
                # Use template name as filename (without extension)
                base_name = os.path.basename(template_name)
                filename = os.path.splitext(base_name)[0] + "_rendered.txt"
            
            self.save_config(rendered_config, filename)
        
        return rendered_config

