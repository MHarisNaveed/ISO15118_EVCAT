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
- [X] ISO security form TCP to +TLS
- [X] Iso 15118-20 implimentation
- [x] Custom EV Simulator with UI Control (New!)


PKI Certificates: Working.

Handshake: Secure (TLS).

Protocol: ISO 15118-20 AC.

Result: Session Success.

############################
### UI-Controlled EV Simulator (New!)
- **Real-time SOC Control:** Web-based slider interface
- **Live Updates:** Change battery SOC during active charging session
- **File-based Integration:** JSON file communication (no code modification needed)
- **Supported Services:** DC Charging, AC Charging, BPT (V2G ready)
##
cd Simulator_GUI
python ui_server.py

## How to run
- see file Get_it_running
