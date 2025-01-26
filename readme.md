# Goat - Pico Network Manager

A library to help you connect to wireless networks and manage network connections.

[GitHub Repository](https://github.com/CodeGoat-dev/Pico-Network-Manager)

## Table of Contents
1. [Overview](#overview)
2. [Features](#features)
3. [Getting Started](#getting-started)  
   - [Requirements](#requirements)  
4. [Setup Instructions](#setup-instructions)  
   - [Software Setup](#1-software-setup)  
   - [Network Configuration](#2-network-configuration)  
   - [Web Interface](#3-web-interface)  
5. [Usage](#usage)  
   - [Basic Implementation](#basic-implementation)  
   - [Customizing Parameters](#customizing-parameters)  
   - [Extended Customisation](#extended-customisation)  
6. [Security Considerations](#security-considerations)  
7. [Usage Scenarios](#usage-scenarios)  
   - [Portable Devices](#portable-devices)  
   - [Home Automation](#home-automation)  
   - [IoT Devices](#iot-devices)  
8. [Future Enhancements](#future-enhancements)  
9. [Contributing](#contributing)  
10. [License](#license)  
11. [Support](#support)

---

## Overview

**Goat - Pico Network Manager** is a Micropython library for the Raspberry Pi Pico W series of microcontrollers. Perfect for all your networking needs, this library comes with a captive portal for initial network setup and can even manage a web server when connected.

With features like access point with captive portal, automatic network reconnection and access point fallback, Pico Network Manager ensures a professional IOT networking experience.

With its open source nature, Pico Network Manager can be adapted to your specific needs. Whether you want to adjust default settings or extend the manager with more advanced functionality, Pico Network Manager provides a good starting point for all your networking needs.

---

## Features

Pico Network Manager comes packed with the following features:

- **Access Point**  
  Used for initial setup to provide the captive portal for network connection.

- **Captive Portal**  
  Connect to a network or reconnect if your connection was dropped and could not be re-established.

- **DNS Redirection**  
  Automatic DNS redirection in AP mode to redirect to the captive portal.

- **Connection Monitoring**  
  Automatic network connection monitoring with reconnection and AP fallback.

- **Web Interface**  
  Configure a web interface for your firmware to be used when connected to a network.

- **Time Synchronisation**  
  Automatic time synchronisation from World Time API when connected to wi-fi.

---

## Getting Started

### Requirements

To deploy Goat - Pico Network Manager and use it in your firmware, you will need:

1. **Hardware Components**:
   - Microcontroller (e.g., Raspberry Pi Pico W for wireless connectivity)

2. **Software**:
   - MicroPython or CircuitPython
   - Required Python libraries (all native to the Pico Network Manager library distribution)

---

## Setup Instructions

### 1. Software Setup
- Extend your device firmware with the Pico Network Manager library. Instructions are provided.
- Flash the microcontroller with MicroPython/CircuitPython firmware.
- Upload your device firmware along with the Pico Network Manager library and dependencies to the microcontroller.

### 2. Network Configuration
- Connect to the device's hotspot to access the captive portal.
- Note: The password is ***"password"*** by default and can be modified in your code.
- Connect to the captive portal. If not automatically redirected, visit [http://192.168.4.1](http://192.168.4.1).
- Scan for wireless networks and enter your Wi-Fi credentials to establish network connectivity.

### 3. Web Interface
- Use a network scanner to locate the new device on your network and make a note of the IP address.
- If you defined a web interface, access it using the device's IP address to configure and customize settings.
- If you are unable to obtain the IP address, try connecting using the default hostname ***"PicoW"***.

---

## Usage

### Basic Implementation
The library is easy to integrate into your existing project.

1. **Import and Initialize**:
   ```python
   from NetworkManager import NetworkManager
   import uasyncio as asyncio

   network_manager = NetworkManager()
   asyncio.create_task(network_manager.run())
   ```

2. **Customizing Parameters**: Customize settings by passing parameters during instantiation:
   ```python
   from WebServer import WebServer

   web_server = WebServer()
   network_manager = NetworkManager(
       ap_ssid="My Access Point",
       ap_password="MyPassword",
       ap_dns_server=True,
       hostname="MyPicoW",
       sta_web_server=web_server
   )
   ```
   - Your optional web server must implement `run()` and `stop_server()` methods which the Network Manager will use.

3. **Extended Customisation**: Customize settings by passing parameters after instantiation:
   ```python
   from WebServer import WebServer

   web_server = WebServer()
   network_manager = NetworkManager(
       ap_ssid="My Access Point",
       ap_password="MyPassword",
       ap_dns_server=True,
       hostname="MyPicoW",
       sta_web_server=web_server
   )

        # Access point settings
   network_manager.ap_ssid = "My Access Point"
   network_manager.ap_password = "MyPassword"
   network_manager.ap_dns_server = True
   network_manager.captive_portal_http_port = 80
   network_manager.network_connection_timeout = 10

   # Access point IP settings
   network_manager.ap_ip_address = "192.168.4.1"
   network_manager.ap_subnet = "255.255.255.0"
   network_manager.ap_gateway = "192.168.4.1"
   network_manager.ap_dns = "192.168.4.1"

   # DHCP settings
   network_manager.hostname = "PicoW"
   ```
   - Your optional web server must implement `run()` and `stop_server()` methods which the Network Manager will use.

---

## Security Considerations

- **Update Default Passwords**: Change the default AP password (`password`) to secure your setup.
- **Network Safety**: Ensure proper network security to prevent unauthorized access.

---

## Usage Scenarios

- **Portable Devices**: Simplify network reconfiguration for portable IoT devices.
- **Home Automation**: Ensure reliable network connectivity for home automation projects.
- **IoT Devices**: Provide a seamless networking experience for IoT devices in various environments.

---

## Contributing

We welcome contributions! Visit the [GitHub Repository](https://github.com/CodeGoat-dev/Pico-Network-Manager) to report issues, suggest features, or submit pull requests.

---

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT). See the LICENSE file for details.

---

## Support

For questions or support, please create an issue in the [GitHub Repository](https://github.com/CodeGoat-dev/Pico-Network-Manager).

---
