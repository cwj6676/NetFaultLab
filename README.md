# NetFaultLab
Network fault injection and troubleshooting lab

## Goal
This project is designed to help users practice troubleshooting by generating faults in a virtual network environment and allowing them to analyze and resolve the root cause themselves.

## Features
- Random network topology generation
  - Small Office
  - Branch Network
  - Multi VLAN

- Random device generation
  - Routers
  - Switches
  - Clients
  - Servers

- Automatic IP configuration
  - Client networks
  - Server network
  - Router-to-router networks

- Multi VLAN support
  - VLAN 10
  - VLAN 20
  - VLAN 30
  - /26 subnetting
  - VLAN gateway generation

- Static routing table generation

- Fault injection
  - Interface Down
  - Wrong IP Address
  - Wrong Default Gateway
  - Wrong Static Route
  - ACL Block

- Topology-aware fault selection
  - Prevents invalid faults when the required network structure does not exist

- Troubleshooting mode
  - Displays network symptoms without revealing the fault
  - Optional debug mode for development

- Recovery verification
  - Stores the healthy network state before fault injection
  - Restores network configuration after troubleshooting
  - Compares the recovered state with the original healthy state

- Reproducible labs using Seed values

- Troubleshooting log generation
  - Seed
  - Topology
  - Fault
  - Target
  - Recovery result
  
## How It Works
NetFaultLab generates a network topology and creates a healthy network state.
A valid fault is randomly selected and injected into the network configuration.
The user receives only the network symptoms and attempts to identify and recover the fault.
After recovery, NetFaultLab compares the current network state with the original healthy state and verifies whether the network was successfully restored.

## Current Status
NetFaultLab is currently a Python-based prototype.
Network topology generation, fault injection, recovery, and verification are currently simulated using Python data structures.
Future versions will integrate Linux, Docker, and Containerlab to create real virtual network environments and verify recovery using actual network traffic such as ping.

## Planned Features
- Linux network namespaces / containers
- Docker integration
- Containerlab topology deployment
- Real interface failure injection
- Real routing configuration
- ACL testing with nftables or iptables
- Automatic ping and connectivity verification
- More complex fault scenarios
- Difficulty levels


