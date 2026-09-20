import random

# 장애 종류
faults = [
    "Interface Down",
    "Wrong IP Address",
    "Wrong Default Gateway",
    "Wrong Static Route",
    "ACL Block"
]

# 네트워크 종류
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

# 토폴로지별 장비 수
if selected_topology == "Small Office":
    topology_map = "PC - Switch - Router - Server"
    routers = random.randint(1, 2)
    switches = random.randint(1, 2)
    clients = random.randint(2, 6)
    servers = random.randint(1, 2)

elif selected_topology == "Branch Network":
    topology_map = "PC - Switch - R1 - R2 - R3 - Server"
    routers = random.randint(3, 5)
    switches = random.randint(1, 3)
    clients = random.randint(2, 8)
    servers = random.randint(1, 2)

elif selected_topology == "Multi VLAN":
    topology_map = "PC1/PC2/PC3 - Switch - Router - Server"
    routers = random.randint(1, 2)
    switches = random.randint(2, 4)
    clients = random.randint(4, 12)
    servers = random.randint(1, 3)

# 장비 이름 생성
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

# PC쪽 네트워크
lan_number = random.randint(1, 254)
lan_network = "192.168." + str(lan_number)

client_ips = []
router_lan_ip = lan_network + ".1"
default_gateway = router_lan_ip

for i in range(len(client_names)):
    ip = lan_network + "." + str(i + 10)
    client_ips.append(ip)

# Multi VLAN 서브네팅
vlan_ids = [10, 20, 30]
vlan_client_ips = []
vlan_gateways = {}
vlan_networks = {}
router_vlan_interfaces = []

if selected_topology == "Multi VLAN":
    base_network = "192.168.100."

    for i in range(len(vlan_ids)):
        vlan_id = vlan_ids[i]
        network_start = i * 64

        vlan_networks[vlan_id] = base_network + str(network_start) + "/26"
        vlan_gateways[vlan_id] = base_network + str(network_start + 1)
    
    for i in range(len(client_names)):
        vlan_id = vlan_ids[i % len(vlan_ids)]
        vlan_index = vlan_ids.index(vlan_id)

        network_start = vlan_index * 64
        host_number = network_start + 10 + (i // len(vlan_ids))

        ip = base_network + str(host_number)

        vlan_client_ips.append((client_names[i], vlan_id, ip, vlan_gateways[vlan_id]))
    
    for vlan_id in vlan_ids:
        router_vlan_interfaces.append(("R1", vlan_id, vlan_gateways[vlan_id]))

# 라우터 사이 IP

router_links = []

for i in range(len(router_names) - 1):
    network_number = i + 1

    left_ip = "10.0." + str(network_number) + ".1"
    right_ip = "10.0." + str(network_number) + ".2"

    router_links.append((router_names[i], left_ip, router_names[i + 1], right_ip))

# 장비 연결
links = []

if selected_topology == "Small Office":
    for i in range(len(client_names)):
        switch_index = i % len(switch_names)
        links.append((client_names[i], switch_names[switch_index]))

    for switch in switch_names:
        links.append((switch, "R1"))

    for i in range(len(router_names) - 1):
        links.append((router_names[i], router_names[i + 1]))

    for server in servers_names:
        links.append((router_names[-1], server))

elif selected_topology == "Branch Network":
    for i in range(len(client_names)):
        switch_index = i % len(switch_names)
        links.append((client_names[i], switch_names[switch_index]))

    for switch in switch_names:
        links.append((switch, "R1"))

    for i in range(len(router_names) - 1):
        links.append((router_names[i], router_names[i + 1]))

    for server in servers_names:
        links.append((router_names[-1], server))

elif selected_topology == "Multi VLAN":
    vlan_ids = [10, 20, 30]

    for i in range(len(client_names)):
        vlan_index = i % len(vlan_ids)
        switch_index = i % len(switch_names)

        vlan_id = vlan_ids[vlan_index]

        links.append((client_names[i], switch_names[switch_index], vlan_id))

    for switch in switch_names:
        links.append((switch, "R1"))

    for i in range(len(router_names) - 1):
        links.append((router_names[i], router_names[i + 1]))

    for server in servers_names:
        links.append((router_names[-1], server))

# 결과 출력
print("\n=== Network Links ===")

for link in links:
    print(link)

print("topology_map:", topology_map)
print("\n=== Router Links ===")

for link in router_links:
    print(link)

if selected_topology == "Multi VLAN":
    print("\n=== VLAN Clients ===")

    for client in vlan_client_ips:
        print(client)

print("Routers :", routers)
if selected_topology == "Multi VLAN":
    print("\n=== Router VLAN Interfaces ===")
    
    for vlan_id in vlan_ids:
        print("VLAN", vlan_id,":",vlan_networks[vlan_id],"Gateway :", vlan_gateways[vlan_id])

print("Switches :", switches)
print("Clients :", clients)
print("servers :", servers)
print("Routers :", router_names)
print("Switches :", switch_names)
print("Clients :", client_names)
print("Client IPs:", client_ips)
print("Servers :", servers_names)
print("Router LAN IP :", router_lan_ip)
print("Default Gateway :", default_gateway)