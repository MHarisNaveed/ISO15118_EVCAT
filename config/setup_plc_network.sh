#!/bin/bash
# network_config.sh - Setup for RPi-to-PLC Link

echo "Configuring Ethernet for Green PHY Communication..."

# 1. Bring the interface down and up to clear old leases
sudo ip link set eth0 down
sudo ip link set eth0 up

# 2. Disable IPv6 temporary addresses (Privacy Extensions) system-wide
# This is the "Fix" for the 'No Route to Host' error
sudo sysctl -w net.ipv6.conf.eth0.use_tempaddr=0
sudo sysctl -w net.ipv6.conf.all.use_tempaddr=0

# 3. Assign the static Link-Local IP
# fe80::1 is the standard 'Gateway' address for many EVSE simulators
sudo ip -6 addr add fe80::1/64 dev eth0

echo "Network Setup Complete. Interface eth0 is ready for ISO 15118."