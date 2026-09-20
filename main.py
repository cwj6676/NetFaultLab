import random
import copy

seed = input("Seed (Enter = Randaom): ")

if seed == "":
    seed = random.randint(1000, 999999)

random.seed(int(seed))

debug_mode = True

# 장애 종류
faults = ["Interface Down", "Wrong IP Address", "Wrong Default Gateway", "Wrong Static Route", "ACL Block"]

# 네트워크 종류
topologies = ["Small Office", "Branch Network", "Multi VLAN"]

selected_fault = random.choice(faults)
selected_topology = random.choice(topologies)

print("NetFaultLab Started")
print("Using Seed:", seed)
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

# 서버 네트워크 분리
server_netwrok = "172.16.18"
server_gateway = server_netwrok + ".1"

server_ips = []

for i in range(len(servers_names)):
    ip = server_netwrok + "." + str(i + 10)
    server_ips.append(ip)

# PC쪽 네트워크
lan_number = random.randint(1, 254)
lan_network = "192.168." + str(lan_number)

client_ips = []
router_lan_ip = lan_network + ".1"
default_gateway = router_lan_ip

for i in range(len(client_names)):
    ip = lan_network + "." + str(i + 10)
    client_ips.append(ip)
client_gateways = []

for i in range(len(client_names)):
    client_gateways.append(default_gateway)

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
# 라우팅 테이블(Static)
routing_tables = {}

for router in router_names:
    routing_tables[router] = []

if len(router_names) > 1:
    for i in range(len(router_names) - 1):
        current_router = router_names[i]
        next_router_ip = router_links[i][3]
    
        routing_tables[current_router].append((server_netwrok + ".0/24", next_router_ip))

if len(router_names) > 1:
    for i in range(1, len(router_names)):
        current_router = router_names[i]
        previous_router_ip = router_links[i - 1][1]

        if selected_topology == "Multi VLAN":
            for vlan_id in vlan_ids:
                routing_tables[current_router].append((vlan_networks[vlan_id], previous_router_ip))

        else:
            routing_tables[current_router].append((lan_network + ".0/24", previous_router_ip))

available_faults = ["Interface Down", "Wrong IP Address", "Wrong Default Gateway", "ACL Block"]

# Static Route가 실제로 있을 때만 추가
possible_route_fault = False

for router in router_names:
    if len(routing_tables[router]) > 0:
        possible_route_fault = True

if possible_route_fault:
    available_faults.append("Wrong Static Route")

selected_fault = random.choice(available_faults)
print("Selected fault:", selected_fault)

# 장애 정보
fault_info = None
down_links = []
acl_rules = []

# 정상 상태 저장
healthy_state = {
    "client_ips": copy.deepcopy(client_ips),
    "client_gateways": copy.deepcopy(client_gateways),
    "vlan_client_ips": copy.deepcopy(vlan_client_ips),
    "routing_tables": copy.deepcopy(routing_tables),
    "down_links": copy.deepcopy(down_links),
    "acl_rules": copy.deepcopy(acl_rules)}

    # Wrong Static Route
if selected_fault == "Wrong Static Route":
    possible_routers = []

    for router in router_names:
        if len(routing_tables[router]) > 0:
            possible_routers.append(router)

    if len(possible_routers) > 0:
        target_router = random.choice(possible_routers)

        route_index = random.randint(0, len(routing_tables[target_router]) - 1 )

        old_route = routing_tables[target_router][route_index]

        destination = old_route[0]
        old_next_hop = old_route[1]
        wrong_next_hop = "10.255.255.254"

        routing_tables[target_router][route_index] = ( destination, wrong_next_hop)

        fault_info = {
            "target": target_router,
            "destination": destination,
            "old_value": old_next_hop,
            "wrong_value": wrong_next_hop}

    # Wrong Default Gateway
elif selected_fault == "Wrong Default Gateway":
    if selected_topology == "Multi VLAN":
        target_client_index = random.randint(0, len(vlan_client_ips) - 1)

        target_client = vlan_client_ips[target_client_index]

        client_name = target_client[0]
        vlan_id = target_client[1]
        client_ip = target_client[2]
        old_gateway = target_client[3]

        wrong_gateway = "192.168.255.254"

        vlan_client_ips[target_client_index] = (client_name, vlan_id, client_ip, wrong_gateway)

    else:
        target_client_index = random.randint( 0,len(client_names) - 1)

        client_name = client_names[target_client_index]

        old_gateway = client_gateways[target_client_index]
        wrong_gateway = lan_network + ".254"

        client_gateways[target_client_index] = wrong_gateway

    fault_info = {
        "target": client_name,
        "old_value": old_gateway,
        "wrong_value": wrong_gateway}
    

    # Wrong IP Address
elif selected_fault == "Wrong IP Address":
    target_client_index = random.randint(0,len(client_names) - 1)

    client_name = client_names[target_client_index]

    if selected_topology == "Multi VLAN":
        target_client = vlan_client_ips[target_client_index]

        vlan_id = target_client[1]
        old_ip = target_client[2]
        gateway = target_client[3]

        wrong_ip = "192.168.250." + str(target_client_index + 10)

        vlan_client_ips[target_client_index] = (client_name,vlan_id,wrong_ip,gateway)

    else:
        old_ip = client_ips[target_client_index]

        wrong_ip = "192.168.250." + str(target_client_index + 10)

        client_ips[target_client_index] = wrong_ip

    fault_info = {
        "target": client_name,
        "old_value": old_ip,
        "wrong_value": wrong_ip}

    # Interface Down
elif selected_fault == "Interface Down":
    target_link_index = random.randint(0,len(links) - 1)

    target_link = links[target_link_index]

    down_links.append(target_link)

    fault_info = {"target": target_link}

    # ACL Block
elif selected_fault == "ACL Block":
    target_client_index = random.randint(0,len(client_names) - 1)

    client_name = client_names[target_client_index]

    if selected_topology == "Multi VLAN":
        client_ip = vlan_client_ips[target_client_index][2]

    else:
        client_ip = client_ips[target_client_index]

    target_server = random.choice(servers_names)

    acl_rules.append(("DENY", client_ip, target_server))

    fault_info = {
        "target": client_name, 
        "client_ip": client_ip,
        "server": target_server}

# 결과 출력
print("\n=== Network Links ===")

for link in links:
    print(link)

print("topology_map:", topology_map)
print("\n=== Router Links ===")

for link in router_links:
    print(link)
print("\n=== Routing Table ===")

for router in router_names:
    print(router)

    for route in routing_tables[router]:
        print(" Destination : ", route[0], "   Next Hop : ", route[1])

print("\n=== Server Network ===")
print("Server Network :", server_netwrok + ".0/24")
print("Server Gateway :", server_gateway)

for i in range(len(servers_names)):
    print(servers_names[i], ":", server_ips[i])

if selected_topology == "Multi VLAN":
    print("\n=== VLAN Clients ===")

    for client in vlan_client_ips:
        print(client)

if selected_topology == "Multi VLAN":
    print("\n=== Router VLAN Interfaces ===")
    
    for vlan_id in vlan_ids:
        print("VLAN", vlan_id,":",vlan_networks[vlan_id],"Gateway :", vlan_gateways[vlan_id])

print("\n=== 장비 갯수 ===")
print("Routers :", routers)
print("Switches :", switches)
print("Clients :", clients)
print("Servers :", servers)
print("\n=== 장비 이름 ===")
print("Routers :", router_names)
print("Switches :", switch_names)
print("Clients :", client_names)
if selected_topology != "Multi VLAN":
    print("\n=== Client Network ===")

    for i in range(len(client_names)):
        print(client_names[i], "IP:", client_ips[i], "Gateway:", client_gateways[i])
print("Servers :", servers_names)
if selected_topology != "Multi VLAN":
    print("Router LAN IP :", router_lan_ip)
    print("Default Gateway :", default_gateway)

# 장애
print("\n=== Problem ===")

if selected_fault == "Wrong IP Address":
    print(fault_info["target"], "cannot reach the network")

elif selected_fault == "Wrong Default Gateway":
    print(fault_info["target"], "cannot reach", random.choice(servers_names))

elif selected_fault == "Wrong Static Route":
    print("Clients cannot reach the Server Network")

elif selected_fault == "Interface Down":
    down_link = fault_info["target"]

    left_device = down_link[0]
    right_device = down_link[1]

    # PC - Switch
    if left_device.startswith("PC"):
        print(left_device, "cannot reach the network")

    # Router - Server
    elif right_device.startswith("Server"):
        print("Clients cannot reach", right_device)

    # Switch - Router
    elif left_device.startswith("SW") and right_device.startswith("R"):
        affected_clients = []

        for link in links:
            if link[0].startswith("PC") and link[1] == left_device:
                affected_clients.append(link[0])

        print("Affected Clients:", affected_clients)
        print("cannot reach the Server Network")

    # Router - Router
    elif left_device.startswith("R") and right_device.startswith("R"):
        print("Network path to the Server Network is unavailable")

    else:
        print("Network connectivity problem detected")

elif selected_fault == "ACL Block":
    print(fault_info["target"], "cannot reach", fault_info["server"])

print("\n=== Recovery Check ===")

if selected_fault == "Wrong Static Route":
    user_answer = input("Correct Next Hop: ")

    if user_answer == fault_info["old_value"]:
        target_router = fault_info["target"]

        for i in range(len(routing_tables[target_router])):
            route = routing_tables[target_router][i]

            if route[0] == fault_info["destination"]:
                routing_tables[target_router][i] = (fault_info["destination"],fault_info["old_value"])

        print("Recovery Successful")

    else:
        print("Recovery Failed")

elif selected_fault == "Wrong Default Gateway":
    user_answer = input("Correct Gateway: ")

    if user_answer == fault_info["old_value"]:
        print("Recovery Successful")

        target_client = fault_info["target"]
        target_index = client_names.index(target_client)

        if selected_topology == "Multi VLAN":
            old_client = vlan_client_ips[target_index]

            vlan_client_ips[target_index] = (old_client[0],old_client[1],old_client[2],fault_info["old_value"])

        else:
            client_gateways[target_index] = fault_info["old_value"]

    else:
        print("Recovery Failed")


elif selected_fault == "Wrong IP Address":
    user_answer = input("Correct IP Address: ")

    if user_answer == fault_info["old_value"]:
        target_client = fault_info["target"]
        target_index = client_names.index(target_client)

        if selected_topology == "Multi VLAN":
            old_client = vlan_client_ips[target_index]

            vlan_client_ips[target_index] = (old_client[0],old_client[1],fault_info["old_value"],old_client[3])

        else:
            client_ips[target_index] = fault_info["old_value"]

        print("Recovery Successful")

    else:
        print("Recovery Failed")


elif selected_fault == "Interface Down":
    user_answer = input("Interface State (up/down): ")

    if user_answer.lower() == "up":
        target_link = fault_info["target"]

        if target_link in down_links:
            down_links.remove(target_link)

        print("Recovery Successful")

    else:
        print("Recovery Failed")


elif selected_fault == "ACL Block":
    user_answer = input("ACL Action (remove/keep): ")

    if user_answer.lower() == "remove":
        target_rule = ("DENY",fault_info["client_ip"],fault_info["server"])

        if target_rule in acl_rules:
            acl_rules.remove(target_rule)

        print("Recovery Successful")

    else:
        print("Recovery Failed")

# 장애 확인
if debug_mode == True and fault_info != None:
    print("\n=== DEBUG Fault Info ===")

    if selected_fault == "Wrong Static Route":
        print("Target Router :", fault_info["target"])
        print("Destination   :", fault_info["destination"])
        print("Old Next Hop  :", fault_info["old_value"])
        print("Wrong Next Hop:", fault_info["wrong_value"])

    elif selected_fault == "Wrong Default Gateway":
        print("Target Client :", fault_info["target"])
        print("Old Gateway   :", fault_info["old_value"])
        print("Wrong Gateway :", fault_info["wrong_value"])

    elif selected_fault == "Wrong IP Address":
        print("Target Client :", fault_info["target"])
        print("Old IP        :", fault_info["old_value"])
        print("Wrong IP      :", fault_info["wrong_value"])

    elif selected_fault == "Interface Down":
        print("Down Link     :", fault_info["target"])

    elif selected_fault == "ACL Block":
        print("Blocked Client:", fault_info["target"])
        print("Client IP     :", fault_info["client_ip"])
        print("Target Server :", fault_info["server"])

# 현재 상태 저장
current_state = {
    "client_ips": copy.deepcopy(client_ips),
    "client_gateways": copy.deepcopy(client_gateways),
    "vlan_client_ips": copy.deepcopy(vlan_client_ips),
    "routing_tables": copy.deepcopy(routing_tables),
    "down_links": copy.deepcopy(down_links),
    "acl_rules": copy.deepcopy(acl_rules)}

print("\n=== Verification ===")

if current_state == healthy_state:
    print("Network Recovery Verified")

else:
    print("Recovery Verification Failed")
