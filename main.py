import random

faults = [
    "Interface Down",
    "Wrong IP Address",
    "Wrong Default Gateway",
    "Wrong Static Route",
    "ACL Block"
]

topologies = [
    "Small Office",
    "Branch Network",
    "Multi VLAN"
]

selected_fault = random.choice(faults)
selected_topology = random.choice(topologies)

print("NetFaultLab Started")
print("Selected fault:", selected_fault)
print("Selected topology:", selected_topology)