# AutoNetLab

AutoNetLab is an automation toolkit designed to simplify the setup and configuration of Cisco network lab environments. It enables network engineers to quickly deploy, configure, and tear down lab scenarios for learning, testing, or demonstration purposes.

## Features

- **Automated Device Configuration**: Easily push configurations to multiple Cisco devices
- **Template-Based Configuration**: Use reusable templates for common networking scenarios
- **Network Topology Management**: Define and validate lab topologies using YAML or JSON
- **State Management**: Track device states and manage the entire lab environment
- **Documentation Generation**: Automatically generate network documentation

## Project Structure

```
AutoNetLab/
├── scripts/        # Python automation scripts
├── templates/      # Configuration templates and example scenarios
├── docs/           # Project documentation
├── tests/          # Automated tests
├── venv/           # Python virtual environment
├── pyproject.toml  # Project configuration and dependencies
└── README.md       # This file
```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/autonetlab.git
   cd autonetlab
   ```

2. Set up the Python virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the package and dependencies:
   ```bash
   pip install -e .
   ```

4. For development, install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## Usage

Basic usage examples:

```python
# Example code will be added as the project develops
```

## Supported Lab Scenarios

- Basic Routing (OSPF, EIGRP)
- VLAN and Trunk Configuration
- Access Control Lists
- Advanced Scenarios (BGP, QoS)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

