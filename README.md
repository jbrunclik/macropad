# Smart Home Macropad

A father-son project: a custom 9-key macropad built to control Xiaomi smart light bulbs.

## About

This project combines hardware tinkering with software reverse-engineering. We built a physical macropad from scratch and attempted to connect it to our smart home ecosystem.

### Hardware

- **Microcontroller**: ESP32/ESP8266 running MicroPython
- **Enclosure**: 3D printed custom case
- **Keys**: 3x3 matrix wiring (9 keys total)
- **Connectivity**: USB (keyboard mode) + Wi-Fi (smart home control)

### The Goal

Control Xiaomi smart light bulbs and desk lamp in my son's room directly from the macropad - no phone or voice assistant needed. Just press a button to toggle lights, adjust brightness, or change colors.

## The Protocol Challenge

Xiaomi smart devices use the proprietary **miIO protocol** for local network communication. Existing Python implementations weren't easily portable to MicroPython's constrained environment, so we decided to write our own.

### What We Figured Out

The miIO protocol works over UDP (port 54321) and uses:

- **AES-128-CBC encryption** for payload protection
- **MD5-derived keys** from the device token
- **PKCS7 padding** for block alignment
- **Binary header** with magic bytes (`0x2131`), device ID, timestamp, and checksum

The `poc.py` file contains our MicroPython-compatible implementation that successfully:
- Connects to Xiaomi devices on the local network
- Encrypts and sends commands (power on/off, brightness, etc.)
- Decrypts and parses responses

## Project Status

**Proof of Concept** - The protocol implementation works, but we didn't finish integrating everything into a polished end product. Life happened, as it does with side projects.

What works:
- The macropad hardware (fully functional USB keyboard)
- Basic miIO protocol communication
- Sending commands to Xiaomi bulbs

What's left to do:
- Configuration file for device list and tokens
- Key mapping to specific light commands
- Error handling and reconnection logic

## Usage

```python
from poc import Device

# Connect to a Xiaomi device
device = Device(ip="192.168.1.xxx", token=b"your_device_token")

# Turn off the light
device.send_command({"id": 1, "method": "set_power", "params": ["off"]})

# Turn on the light
device.send_command({"id": 2, "method": "set_power", "params": ["on"]})

# Get device info
device.send_command({"id": 3, "method": "miIO.info", "params": []})

device.close()
```

## Getting Device Tokens

The hardest part of working with Xiaomi devices locally is obtaining the device token. Options include:
- Extracting from older versions of the Mi Home app
- Using tools like [python-miio](https://github.com/rytilahti/python-miio) on a full Python environment
- Packet sniffing during initial device setup

## Requirements

- MicroPython with `ucryptolib` support
- ESP32 or ESP8266 with Wi-Fi capability
- Xiaomi smart devices on the same local network

## License

MIT
