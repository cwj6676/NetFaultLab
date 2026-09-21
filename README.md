# NetFaultLab

NetFaultLab is a network troubleshooting practice project that generates random virtual network topologies, injects network faults, and allows users to diagnose and recover the network.

The project started as a Python-based simulation and has been expanded to use Docker and Containerlab for real Linux network fault injection and recovery testing.

## Features

- Random network topology generation
- Multiple topology types
  - Small Office
  - Branch Network
  - Multi VLAN
- Random device counts and IP configurations
- Seed-based reproducible scenarios
- Automatic Containerlab topology generation
- Automatic Containerlab deployment
- Docker-based Linux network nodes
- Automatic interface mapping
- Real network fault injection
- Real recovery operations
- Ping-based connectivity verification
- Internal network state verification after recovery

## Supported Fault Scenarios

NetFaultLab currently supports:

- Interface Down
- Wrong IP Address
- Wrong Default Gateway
- Wrong Static Route
- ACL Block

Each scenario follows a troubleshooting workflow:

1. Generate a healthy network state
2. Deploy the network using Containerlab
3. Verify normal connectivity
4. Inject a network fault
5. Verify connectivity failure
6. Ask the user to troubleshoot the problem
7. Apply the recovery configuration
8. Verify connectivity after recovery
9. Compare the recovered state with the original healthy state

## Real Fault Injection

### Interface Down

A random network link is selected and an actual Linux interface inside the Containerlab environment is disabled.

```bash
ip link set eth1 down
```

After the user enters the recovery action, the interface is enabled again.

```bash
ip link set eth1 up
```

Connectivity is tested before the fault, after the fault, and after recovery.

### Wrong IP Address

A client is selected and an incorrect IP address is applied to the actual Containerlab node.

The correct IP configuration is restored after the user enters the correct value.

Connectivity is verified before and after the fault and again after recovery.

### Wrong Default Gateway

A client receives an incorrect default gateway.

NetFaultLab modifies the actual Linux routing table inside the container and verifies that communication fails.

After the correct gateway is entered, the default route is restored and connectivity is tested again.

### Wrong Static Route

A router receives an incorrect next-hop address.

The Linux routing table is modified using `ip route`.

After the user enters the correct next hop, the route is restored and connectivity is verified again.

### ACL Block

Traffic is blocked using Linux `iptables`.

The selected traffic is denied and connectivity failure is verified.

After the user removes the ACL rule, the rule is deleted and connectivity is tested again.

## Network Topologies

### Small Office

```text
PC
 |
Switch
 |
Router
 |
Server
```

### Branch Network

```text
PC
 |
Switch
 |
R1 --- R2 --- R3
               |
             Server
```

The exact number of routers, switches, clients, and servers changes depending on the generated scenario.

### Multi VLAN

```text
PCs
 |
Switches
 |
Router
 |
Server
```

Clients are distributed across multiple VLANs:

```text
VLAN 10
VLAN 20
VLAN 30
```

The program generates VLAN networks, gateways, and client IP addresses.

## Example Workflow

```text
NetFaultLab Started
Using Seed: 12345
Selected topology: Small Office

Containerlab topology created
Containerlab deployed
Router IP configuration completed
Link test IP configuration completed

Selected fault: Interface Down

=== Healthy Link Test ===
Link Test: SUCCESS

Fault Injected: SW1 eth4 DOWN

=== Fault Link Test ===
Link Test: FAILED

=== Problem ===
PC4 cannot reach the network

=== Recovery Check ===
Interface State (up/down): up

Recovery: SW1 eth4 UP

=== Recovery Link Test ===
Link Test: SUCCESS

Recovery Successful

=== Verification ===
Network Recovery Verified
```

## Technologies

- Python
- Linux
- Docker
- Containerlab
- iproute2
- iptables
- Git
- GitHub

## Project Structure

```text
NetFaultLab/
├── main.py
├── README.md
├── .gitignore
├── lab.clab.yml
└── logs.txt
```

`lab.clab.yml` is generated automatically by the program.

Runtime files such as logs and generated lab files can be excluded from Git depending on the environment.

## Requirements

Current development environment:

- Ubuntu 22.04
- WSL2
- Python 3
- Docker Engine
- Containerlab

Docker must be running before deploying a Containerlab topology.

## Installation

Clone the repository:

```bash
git clone git@github.com:cwj6676/NetFaultLab.git
```

Move into the project directory:

```bash
cd NetFaultLab
```

Run NetFaultLab:

```bash
python3 main.py
```

The program will generate a random network topology, deploy the Containerlab environment, inject a random fault, and begin the troubleshooting process.

## Seed Support

NetFaultLab supports seeds for reproducible scenarios.

Example:

```text
Seed (Enter = Random): 12345
```

Using the same seed makes generated scenarios easier to reproduce during testing and debugging.

Press Enter to generate a random seed.

## Recovery Verification

Before fault injection, NetFaultLab stores a copy of the healthy network state.

After recovery, the current state is compared with the original state.

Successful recovery:

```text
=== Verification ===
Network Recovery Verified
```

Failed recovery:

```text
=== Verification ===
Recovery Verification Failed
```

Real connectivity tests are also performed for Containerlab-based fault scenarios.

## Current Status

NetFaultLab has progressed from a Python-only network fault simulator into a Containerlab-based troubleshooting lab.

Currently implemented:

- Dynamic topology generation
- Containerlab topology generation
- Automatic Containerlab deployment
- Linux container network configuration
- Automatic interface mapping
- Real interface shutdown and recovery
- Real IP configuration faults
- Real default gateway faults
- Real static route faults
- Real ACL-based traffic blocking
- Ping-based failure verification
- Ping-based recovery verification
- Internal state recovery verification

## Limitations

The current version still uses simplified Linux containers as network devices.

Nodes named as switches are Linux containers and do not yet behave as full Layer 2 Ethernet switches.

Some test IP addresses are currently used specifically for connectivity and fault verification.

The generated logical network configuration and the actual Containerlab network are still being gradually integrated into a more realistic end-to-end network environment.

## Planned Improvements

- Implement more realistic Layer 2 switching
- Add Linux bridge configuration
- Improve VLAN behavior
- Apply generated client IP addresses directly to the real lab
- Apply generated server networks directly to the real lab
- Expand static routing scenarios
- Add additional network fault types
- Improve logging and troubleshooting reports
- Add difficulty levels
- Improve automatic recovery verification
- Integrate with NetworkMonitor
- Allow NetworkMonitor to monitor deployed NetFaultLab devices automatically

## NetworkMonitor Integration

NetFaultLab is planned to work together with the separate NetworkMonitor project.

```text
NetFaultLab
    |
    | Deploy network / Inject fault
    v
Containerlab Network
    |
    | Device status / Ping
    v
NetworkMonitor
    |
    | Detect WARNING / DOWN
    v
User Troubleshooting
    |
    | Recover network
    v
NetworkMonitor
    |
    | Detect RECOVERED
    v
Recovery Verified
```

NetFaultLab will generate troubleshooting scenarios while NetworkMonitor detects and records network failures and recoveries.

## Purpose

The goal of NetFaultLab is to build practical experience with:

- Network troubleshooting
- IP addressing
- Default gateways
- Static routing
- ACL concepts
- Linux networking
- Docker
- Containerlab
- Fault isolation
- Network recovery verification

This project is being developed as a hands-on networking portfolio project.
