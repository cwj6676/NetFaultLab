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
- Connectivity verification using ping
- Internal network state verification after recovery

## Supported Fault Scenarios

NetFaultLab currently supports the following fault scenarios:

- Interface Down
- Wrong IP Address
- Wrong Default Gateway
- Wrong Static Route
- ACL Block

Each fault scenario is designed to simulate a troubleshooting process.

The general flow is:

1. Generate a healthy network state
2. Deploy the network using Containerlab
3. Verify normal connectivity
4. Inject a network fault
5. Verify connectivity failure
6. Ask the user to identify and recover the problem
7. Apply the recovery configuration
8. Verify connectivity again
9. Compare the recovered state with the original healthy state

## Real Fault Injection

### Interface Down

A random network link is selected and the connected Linux interface is disabled.

Example:

```bash
ip link set eth1 down

After the user enters the recovery action, the interface is enabled again.

ip link set eth1 up

Connectivity is tested before the fault, after the fault, and after recovery.

Wrong IP Address

A client is selected and an incorrect IP address is applied to the actual Containerlab node.

The correct IP configuration is restored after the user enters the correct value.

Connectivity is verified using ping tests.

Wrong Default Gateway

A client receives an incorrect default gateway.

NetFaultLab modifies the actual Linux routing table inside the container and verifies that communication fails.

After the correct gateway is entered, the default route is restored and connectivity is tested again.

Wrong Static Route

A router receives an incorrect next-hop address.

The actual Linux routing table is modified using ip route.

The route is restored after the user identifies the correct next hop.

Connectivity is tested before the route fault, during the fault, and after recovery.

ACL Block

An ACL-style traffic block is applied using Linux iptables.

Traffic to the selected test destination is blocked and connectivity failure is verified.

After the user removes the ACL rule, the rule is deleted and connectivity is tested again.

Network Topologies
Small Office
PC
 |
Switch
 |
Router
 |
Server
Branch Network
PC
 |
Switch
 |
R1 --- R2 --- R3
               |
             Server

The exact number of routers, switches, clients, and servers can change depending on the generated scenario.

Multi VLAN
PCs
 |
Switches
 |
Router
 |
Server

Clients are distributed across VLANs such as:

VLAN 10
VLAN 20
VLAN 30

The Python simulation also generates VLAN networks, gateways, and client IP addresses.

Example Workflow
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
Technologies
Python
Linux
Docker
Containerlab
iproute2
iptables
Git
GitHub
Project Structure
NetFaultLab/
├── main.py
├── README.md
├── .gitignore
├── lab.clab.yml
└── logs.txt

lab.clab.yml is generated automatically by the program.

Runtime files such as generated logs or temporary lab files can be excluded from Git depending on the environment.

Requirements

The current implementation is designed to run in a Linux environment.

The development environment used for the project includes:

Ubuntu 22.04 on WSL2
Docker Engine
Containerlab
Python 3

Containerlab requires Docker to be running.

Running NetFaultLab

Clone the repository:

git clone git@github.com:cwj6676/NetFaultLab.git

Move into the project directory:

cd NetFaultLab

Run the program:

python3 main.py

NetFaultLab will generate a random topology, deploy the Containerlab environment, inject a random fault, and start the troubleshooting process.

Seed

NetFaultLab supports random seeds.

Example:

Seed (Enter = Random): 12345

Using the same seed makes it easier to reproduce the same generated scenario during testing and debugging.

Press Enter to use a random seed.

Recovery Verification

NetFaultLab keeps a copy of the healthy network state before fault injection.

After the user performs recovery, the current state is compared with the original healthy state.

Successful recovery:

=== Verification ===
Network Recovery Verified

Failed recovery:

=== Verification ===
Recovery Verification Failed

Real connectivity tests are also performed for supported Containerlab fault scenarios.

Current Status

NetFaultLab has progressed from a Python-only network fault simulator into a Containerlab-based troubleshooting lab.

Current functionality includes:

Dynamic topology generation
Containerlab deployment
Linux container network configuration
Real interface shutdown and recovery
Real IP configuration faults
Real default gateway faults
Real static route faults
Real ACL-based traffic blocking
Ping-based failure and recovery verification
Internal state recovery verification
Limitations

The current project still uses simplified Linux containers for network devices.

Nodes named as switches are currently Linux containers and do not yet behave as full Layer 2 Ethernet switches.

Some test IP addresses are used specifically to verify individual links and fault conditions.

The generated logical network configuration and the Containerlab test network are gradually being integrated into a more realistic end-to-end network environment.

Planned Improvements
Implement more realistic Layer 2 switching
Add Linux bridge configuration
Improve VLAN behavior
Connect generated client IP addresses directly to the real lab network
Connect generated server networks directly to the real lab network
Expand static routing scenarios
Add more fault types
Improve logging and troubleshooting reports
Add difficulty levels
Improve automatic recovery verification
Integrate with NetworkMonitor
Allow NetworkMonitor to monitor NetFaultLab devices automatically
NetworkMonitor Integration

NetFaultLab is planned to work together with the separate NetworkMonitor project.

The intended workflow is:

NetFaultLab
    |
    | Deploy virtual network
    | Inject fault
    v
Containerlab Network
    |
    | Device status / ping
    v
NetworkMonitor
    |
    | Detect WARNING / DOWN
    |
User Troubleshooting
    |
    | Recover network
    v
NetworkMonitor
    |
    | Detect RECOVERED
    v
Recovery Verified

This will allow NetFaultLab to generate troubleshooting scenarios while NetworkMonitor detects and records network failures and recoveries.

Purpose

The goal of NetFaultLab is to build practical experience with:

Network troubleshooting
IP addressing
Default gateways
Static routing
ACL concepts
Linux networking
Docker
Containerlab
Fault isolation
Network recovery verification

The project is being developed as a hands-on networking portfolio project.
