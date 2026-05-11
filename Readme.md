# EV Charging PLC Bridge

This repository contains the implementation of a High-Level Communication (HLC) bridge 
using Raspberry Pi and devolo Green PHY hardware.

## Physical Setup
- **Controller:** Raspberry Pi 4
- **PLC Modem:** devolo dLAN Green PHY (Qualcomm QCA7000)
- **Interface:** Ethernet-to-PLC Bridging

## Current Progress
- [x] Physical Hardware Integration
- [x] Ethernet Bridge Verification
- [x] ISO 15118-2 Handshake Implementation (In Progress)
- [X] ISO security form TCP to TLS
- [X] Iso 15118-20 implimentation

PKI Certificates: Working.

Handshake: Secure (TLS).

Protocol: ISO 15118-20 AC.

Result: Session Success.

## How to run
- see file Get_it_running
