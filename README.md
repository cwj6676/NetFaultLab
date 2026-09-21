# NetFaultLab

> **Network troubleshooting portfolio project**
>
> Builds real Containerlab topologies, injects faults into the live network, and lets the user diagnose and repair them through a CLI.

> 🚧 **This project is currently under active development.**
>
> Core networking and troubleshooting features are implemented, but the UI, testing, documentation, and overall usability are still being improved. Features and behavior may change as development continues.

![Python](https://img.shields.io/badge/Python-3.x-blue)
![Docker](https://img.shields.io/badge/Docker-Containerlab-blue)
![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20WSL2-lightgrey)
![Status](https://img.shields.io/badge/Status-In%20Development-yellow)

## Project at a Glance

| Item | Details |
|---|---|
| Goal | Hands-on network fault diagnosis and recovery |
| Core Stack | Python, Docker, Containerlab, Linux Networking |
| Network Features | Bridge, VLAN, Static Routing, ACL, ICMP |
| Fault Types | Wrong IP, Wrong Gateway, Wrong Route, Interface Down, ACL Block |
| Integration | Live monitoring through NetworkMonitor |

## Demo

> Add a real terminal GIF or screenshot here later for a stronger GitHub portfolio presentation.

```text
netfault> inject
Fault injected

=== Problem ===
PC2 cannot reach the network

netfault> show ip
netfault> show route
netfault> show interface
netfault> ping PC2 Server1
netfault> configure
netfault> verify
```

## Table of Contents

- [Features](#features)
- [Supported Topologies](#supported-topologies)
- [Fault Scenarios](#fault-scenarios)
- [Troubleshooting CLI](#troubleshooting-cli)
- [NetworkMonitor Integration](#networkmonitor-integration)
- [Basic Usage](#basic-usage)
- [Current Limitations](#current-limitations)

NetFaultLab is a Python-based network troubleshooting lab that builds real Linux network topologies with Containerlab, injects faults into the running lab, and lets the user investigate and repair the network through a CLI.

The project is designed as a hands-on troubleshooting environment rather than a simple network simulator. In normal mode, fault details are hidden, so the user must inspect IP addressing, gateways, routes, interfaces, ACLs, and connectivity to determine the cause.

[한국어 README](README_KR.md)

## Features

- Dynamic topology generation with reproducible seeds
- Real Containerlab Linux nodes
- Linux bridge-based switching
- Multi-router static routing
- Multi-VLAN networking with VLAN 10, 20, and 30
- Real client-to-server end-to-end connectivity
- Persistent CLI: deploy once, troubleshoot repeatedly
- Manual configuration changes applied directly to the running lab
- Fault injection without immediately revealing the answer
- NetworkMonitor integration through `lab_state.json`
- Debug mode for detailed internal output

## Supported Topologies

### Small Office

```text
PCs -- Switches -- R1 [-- R2] -- Servers
```

### Branch Network

```text
PCs -- Switches -- R1 -- R2 -- R3 ... -- Servers
```

### Multi VLAN

```text
VLAN 10 Clients --\
VLAN 20 Clients ---- Switches ---- R1 ---- Servers
VLAN 30 Clients --/
```

Current VLAN networks:

| VLAN | Network | Gateway |
|---|---|---|
| 10 | `192.168.100.0/26` | `192.168.100.1` |
| 20 | `192.168.100.64/26` | `192.168.100.65` |
| 30 | `192.168.100.128/26` | `192.168.100.129` |

Server network:

```text
172.16.18.0/24
Gateway: 172.16.18.1
```

Router-to-router links use `/30` networks in the `10.0.x.0/30` range.

## Fault Scenarios

NetFaultLab currently supports five fault types:

- Interface Down
- Wrong IP Address
- Wrong Default Gateway
- Wrong Static Route
- ACL Block

A random fault can be injected with:

```text
netfault> inject
```

A specific fault can also be selected:

```text
netfault> inject ip
netfault> inject gateway
netfault> inject route
netfault> inject interface
netfault> inject acl
```

In normal mode, the exact fault type, target, and wrong value are not displayed.

## Troubleshooting CLI

After the lab is deployed, NetFaultLab stays running and accepts commands from the `netfault>` prompt.

```text
help
status
show problem
show topology
show ip
show route
show interface
ping <source> <target>
inject
configure
verify
destroy
exit
```

Example:

```text
netfault> inject

Fault injected

=== Problem ===
PC2 cannot reach the network

netfault> show ip
netfault> show route
netfault> show interface
netfault> ping PC2 Server1
netfault> configure
netfault> verify
```

`configure` opens a live configuration menu:

```text
1. IP Address
2. Default Gateway
3. Static Route
4. Interface State
5. ACL Rule
6. Cancel
```

Changes are applied directly to the running Containerlab environment. A wrong repair attempt can therefore create an additional problem, requiring further troubleshooting.

## Verification

`verify` checks both:

- whether the Python-side network state matches the original healthy state
- whether real end-to-end connectivity has been restored

A successful result is:

```text
Network Recovery Verified
```

## NetworkMonitor Integration

NetFaultLab exports the current lab configuration to:

```text
lab_state.json
```

The file contains the current topology, devices, IP information, and links. It intentionally does not expose the injected fault as the answer.

NetworkMonitor reads this file and independently checks the real running lab.

## Debug Mode

Normal mode hides internal fault details and long command output.

```python
debug_mode = False
```

For development and troubleshooting:

```python
debug_mode = True
```

Debug mode may show detailed fault information and lower-level command output.

## Requirements

- Linux or WSL2
- Python 3
- Docker Engine
- Containerlab
- Internet access for Alpine package installation during lab setup

## Basic Usage

```bash
python3 main.py
```

Enter a seed or press Enter for a random seed.

```text
Seed (Enter = Random):
```

Then use the `netfault>` CLI.

## Reproducible Seeds

A seed reproduces the generated topology and random selections associated with that run. This is useful for debugging and demonstrations.

Examples used during development include:

```text
91838   - multi-router / static-route test case
18594   - wrong-IP test case
5133    - wrong-gateway test case
851701  - interface test case
327842  - Multi VLAN gateway test case
602168  - Multi VLAN multi-router test case
```

These are development examples, not guaranteed compatibility contracts for future code changes.

## Current Limitations

- Linux containers are used instead of vendor router/switch images.
- Static routing is used; dynamic routing protocols are not implemented.
- The CLI is currently text based. A terminal-style GUI is planned.
- Some internal link-test addressing may still exist for specific validation paths.
- NetworkMonitor integration currently uses a shared JSON state file plus direct Docker/Containerlab checks.
- The project is intended for lab and portfolio use, not production network automation.

## Related Project

NetworkMonitor is the companion monitoring project that observes the live NetFaultLab topology and reports state changes such as `WARNING`, `DOWN`, and `RECOVERED`.
