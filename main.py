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

if selected_topology == "Small Office":
    topology_map = "PC - Switch - Router - Server"
    routers = random.randint(1, 2)
    switches = random.randint(1, 2)
    clients = random.randint(2, 6)
    servers = random.randint(1,2)

elif selected_topology == "Branch Network":
    topology_map = "PC = Switch - R1 - R2 - R3 - Server"
    routers = random.randint(3, 5)
    switches = random.randint(1, 3)
    clients = random.randint(2, 8)
    servers = random.randint(1,2)

elif selected_topology == "Multi VLAN":
    topology_map = "PC1/PC2/PC3 - Switch - Router - Server"
    routers = random.randint(1, 2)
    switches = random.randint(2, 4)
    clients = random.randint(4, 12)
    servers = random.randint(1,3)

router_names = []
for i in range(1, routers + 1):
    router_names.append("R" + str(i))

client_names = []
for i in range(1, clients + 1):
    client_names.append("PC" + str(i))

switch_names = []
for i in range(1, switches + 1):
    switch_names.append("SW" + str(i))

servers_names = []
for i in range(1, servers + 1):
    servers_names.append("Server" + str(i))

print("topology_map:", topology_map)
print("Routers :", routers)
print("Switches :", switches)
print("Clients :", clients)
print("servers :", servers)
print("Routers :", router_names)
print("Switches :", switch_names)
print("Clients :", client_names)
print("Servers :", servers_names)

