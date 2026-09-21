import random
import copy
import subprocess

# ===== 출력 설정 =====
# False: 핵심 결과만 출력
# True : Containerlab / 명령어 / 상세 네트워크 정보까지 출력
debug_mode = False


def debug_print(*args, **kwargs):
    if debug_mode:
        print(*args, **kwargs)


def run_command(command, **kwargs):
    """명령을 실행하고, 일반 모드에서는 외부 명령의 긴 출력을 숨긴다."""
    if debug_mode:
        return subprocess.run(command, **kwargs)

    quiet_kwargs = dict(kwargs)

    if "stdout" not in quiet_kwargs:
        quiet_kwargs["stdout"] = subprocess.DEVNULL

    if "stderr" not in quiet_kwargs:
        quiet_kwargs["stderr"] = subprocess.DEVNULL

    return subprocess.run(command, **quiet_kwargs)

# ===== 1. Containerlab / 실제 네트워크 설정 =====
interface_map = {}

# 링크 테스트용 IP
link_test_ips = {}

# 토폴로지 파일 생성
def create_containerlab(links):
    global interface_map

    interface_map = {}
    node_interfaces = {}
    node_lines = ""
    link_lines = ""

    # 노드 만들기
    for link in links:
        device1 = link[0]
        device2 = link[1]

        if device1 not in node_interfaces:
            node_interfaces[device1] = 1
            node_lines += (
                "    " + device1 + ":\n"
                "      kind: linux\n"
                "      image: alpine:latest\n\n"
            )

        if device2 not in node_interfaces:
            node_interfaces[device2] = 1
            node_lines += (
                "    " + device2 + ":\n"
                "      kind: linux\n"
                "      image: alpine:latest\n\n"
            )

    # 링크와 인터페이스 만들기
    for link in links:
        device1 = link[0]
        device2 = link[1]

        interface1 = "eth" + str(node_interfaces[device1])
        interface2 = "eth" + str(node_interfaces[device2])

        interface_map[link] = {
            device1: interface1,
            device2: interface2
        }

        link_lines += (
            '    - endpoints: ["'
            + device1 + ":" + interface1
            + '", "'
            + device2 + ":" + interface2
            + '"]\n'
        )

        node_interfaces[device1] += 1
        node_interfaces[device2] += 1

    lab_config = (
        "name: netfaultlab\n\n"
        "topology:\n"
        "  nodes:\n"
        + node_lines
        + "  links:\n"
        + link_lines
    )

    with open("lab.clab.yml", "w") as file:
        file.write(lab_config)

    debug_print("Containerlab topology created")


# 토폴로지 배포
def deploy_containerlab():
    # 기존 Lab 정리
    run_command([
        "sudo",
        "containerlab",
        "destroy",
        "-t",
        "lab.clab.yml",
        "--cleanup"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
   
    result = run_command([
        "sudo",
        "containerlab",
        "deploy",
        "-t",
        "lab.clab.yml"
    ])

    if result.returncode == 0:
        print("Containerlab deployed")
    else:
        print("Containerlab deploy failed")


# 장비 간 링크 검색
def find_link(device1, device2):
    for link in interface_map:
        if link[0] == device1 and link[1] == device2:
            return link

        if link[0] == device2 and link[1] == device1:
            return link

    return None


# 라우터 간 IP 설정
def configure_router_ips(router_links):
    for router_link in router_links:
        left_router = router_link[0]
        left_ip = router_link[1]
        right_router = router_link[2]
        right_ip = router_link[3]

        link = find_link(left_router, right_router)

        if link == None:
            continue

        left_interface = interface_map[link][left_router]
        right_interface = interface_map[link][right_router]

        run_command([
            "docker", "exec",
            "clab-netfaultlab-" + left_router,
            "ip", "addr", "replace",
            left_ip + "/30",
            "dev", left_interface
        ])

        run_command([
            "docker", "exec",
            "clab-netfaultlab-" + right_router,
            "ip", "addr", "replace",
            right_ip + "/30",
            "dev", right_interface
        ])

        run_command([
            "docker", "exec",
            "clab-netfaultlab-" + left_router,
            "ip", "link", "set",
            left_interface, "up"
        ])

        run_command([
            "docker", "exec",
            "clab-netfaultlab-" + right_router,
            "ip", "link", "set",
            right_interface, "up"
        ])

    debug_print("Router IP configuration completed")


# Interface Down 장애 주입
def inject_interface_down(target_link):
    device2 = target_link[1]
    interface = interface_map[target_link][device2]

    run_command([
        "docker", "exec",
        "clab-netfaultlab-" + device2,
        "ip", "link", "set",
        interface, "down"
    ])

    print("Fault Injected:", device2, interface, "DOWN")


# Interface Down 복구
def recover_interface(target_link):
    device2 = target_link[1]
    interface = interface_map[target_link][device2]

    run_command([
        "docker", "exec",
        "clab-netfaultlab-" + device2,
        "ip", "link", "set",
        interface, "up"
    ])

    print("Recovery:", device2, interface, "UP")

# 링크 테스트 IP 설정
def configure_link_test_ips(links):
    global link_test_ips

    link_test_ips = {}

    for i in range(len(links)):
        link = links[i]

        device1 = link[0]
        device2 = link[1]

        interface1 = interface_map[link][device1]
        interface2 = interface_map[link][device2]

        network_number = i + 1

        ip1 = "10.254." + str(network_number) + ".1"
        ip2 = "10.254." + str(network_number) + ".2"

        link_test_ips[link] = {
            device1: ip1,
            device2: ip2
        }

        run_command([
            "docker", "exec",
            "clab-netfaultlab-" + device1,
            "ip", "addr", "replace",
            ip1 + "/30",
            "dev", interface1
        ])

        run_command([
            "docker", "exec",
            "clab-netfaultlab-" + device2,
            "ip", "addr", "replace",
            ip2 + "/30",
            "dev", interface2
        ])

    debug_print("Link test IP configuration completed")



# 생성된 PC / Server IP 적용
def configure_generated_ips():
    # PC 설정
    for i in range(len(client_names)):
        client_name = client_names[i]
        target_link = None

        for link in links:
            if link[0] == client_name or link[1] == client_name:
                target_link = link
                break

        if target_link == None:
            continue

        interface = interface_map[target_link][client_name]

        if selected_topology == "Multi VLAN":
            client_ip = vlan_client_ips[i][2]
            prefix = "26"

        else:
            client_ip = client_ips[i]
            prefix = "24"

        run_command([
            "docker", "exec",
            "clab-netfaultlab-" + client_name,
            "ip", "addr", "replace",
            client_ip + "/" + prefix,
            "dev", interface
        ])

        run_command([
            "docker", "exec",
            "clab-netfaultlab-" + client_name,
            "ip", "link", "set",
            interface, "up"
        ])

        debug_print(
            "Client IP configured:",
            client_name,
            client_ip + "/" + prefix
        )

    # Server 설정
    for i in range(len(servers_names)):
        server_name = servers_names[i]
        target_link = None

        for link in links:
            if link[0] == server_name or link[1] == server_name:
                target_link = link
                break

        if target_link == None:
            continue

        interface = interface_map[target_link][server_name]
        server_ip = server_ips[i]

        run_command([
            "docker", "exec",
            "clab-netfaultlab-" + server_name,
            "ip", "addr", "replace",
            server_ip + "/24",
            "dev", interface
        ])

        run_command([
            "docker", "exec",
            "clab-netfaultlab-" + server_name,
            "ip", "link", "set",
            interface, "up"
        ])

        debug_print(
            "Server IP configured:",
            server_name,
            server_ip + "/24"
        )

    debug_print("Generated IP configuration completed")


# Linux Bridge 기반 스위치 구성
def configure_switch_bridges():
    for switch_name in switch_names:
        # Alpine 네트워크 도구 준비
        run_command([
            "docker", "exec",
            "clab-netfaultlab-" + switch_name,
            "apk", "add", "--no-cache", "iproute2"
        ])

        # Bridge 초기화
        run_command([
            "docker", "exec",
            "clab-netfaultlab-" + switch_name,
            "ip", "link", "delete", "br0"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if selected_topology == "Multi VLAN":
            # VLAN filtering이 가능한 Linux Bridge 생성
            run_command([
                "docker", "exec",
                "clab-netfaultlab-" + switch_name,
                "ip", "link", "add", "br0",
                "type", "bridge",
                "vlan_filtering", "1"
            ])
        else:
            run_command([
                "docker", "exec",
                "clab-netfaultlab-" + switch_name,
                "ip", "link", "add", "br0",
                "type", "bridge"
            ])

        # 스위치 포트를 Bridge에 연결
        for link in interface_map:
            if switch_name not in interface_map[link]:
                continue

            interface = interface_map[link][switch_name]

            run_command([
                "docker", "exec",
                "clab-netfaultlab-" + switch_name,
                "ip", "addr", "flush",
                "dev", interface
            ])

            run_command([
                "docker", "exec",
                "clab-netfaultlab-" + switch_name,
                "ip", "link", "set",
                interface, "master", "br0"
            ])

            run_command([
                "docker", "exec",
                "clab-netfaultlab-" + switch_name,
                "ip", "link", "set",
                interface, "up"
            ])

            if selected_topology == "Multi VLAN":
                # 기본 VLAN 1 제거
                run_command([
                    "docker", "exec",
                    "clab-netfaultlab-" + switch_name,
                    "bridge", "vlan", "del",
                    "dev", interface,
                    "vid", "1"
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                # PC-Switch 링크는 Access Port
                if len(link) >= 3:
                    vlan_id = link[2]

                    run_command([
                        "docker", "exec",
                        "clab-netfaultlab-" + switch_name,
                        "bridge", "vlan", "add",
                        "dev", interface,
                        "vid", str(vlan_id),
                        "pvid", "untagged"
                    ])

                # Switch-R1 링크는 VLAN Trunk
                elif "R1" in link:
                    for vlan_id in vlan_ids:
                        run_command([
                            "docker", "exec",
                            "clab-netfaultlab-" + switch_name,
                            "bridge", "vlan", "add",
                            "dev", interface,
                            "vid", str(vlan_id)
                        ])

        run_command([
            "docker", "exec",
            "clab-netfaultlab-" + switch_name,
            "ip", "link", "set",
            "br0", "up"
        ])

        # 일반 LAN에서는 기존 링크 테스트 IP 유지
        if selected_topology != "Multi VLAN":
            for link in link_test_ips:
                if switch_name in link_test_ips[link]:
                    switch_test_ip = link_test_ips[link][switch_name]

                    run_command([
                        "docker", "exec",
                        "clab-netfaultlab-" + switch_name,
                        "ip", "addr", "replace",
                        switch_test_ip + "/30",
                        "dev", "br0"
                    ])

        debug_print("Switch Bridge configured:", switch_name)

def test_link_connection(target_link):
    device1 = target_link[0]
    device2 = target_link[1]

    target_ip = link_test_ips[target_link][device2]

    result = run_command([
        "docker", "exec",
        "clab-netfaultlab-" + device1,
        "ping", "-c", "2",
        "-W", "1",
        target_ip
    ])

    if result.returncode == 0:
        print("Link Test: SUCCESS")
        return True

    else:
        print("Link Test: FAILED")
        return False


# Interface Down 전/후 실제 경로 통신 확인
def test_interface_fault_connection(target_link):
    # PC-Switch 링크
    if target_link[0].startswith("PC"):
        client_name = target_link[0]
        target_ip = server_ips[0]

        result = run_command([
            "docker", "exec",
            "clab-netfaultlab-" + client_name,
            "ping", "-c", "2",
            "-W", "1",
            target_ip
        ])

    # Switch-R1 링크
    elif target_link[0].startswith("SW") and target_link[1] == "R1":
        switch_name = target_link[0]
        client_name = None

        for link in links:
            if link[0].startswith("PC") and link[1] == switch_name:
                client_name = link[0]
                break

        if client_name == None:
            print("Interface Test: SKIPPED")
            return False

        result = run_command([
            "docker", "exec",
            "clab-netfaultlab-" + client_name,
            "ping", "-c", "2",
            "-W", "1",
            server_ips[0]
        ])

    # Router-Router 링크
    elif target_link[0].startswith("R") and target_link[1].startswith("R"):
        result = run_command([
            "docker", "exec",
            "clab-netfaultlab-" + client_names[0],
            "ping", "-c", "2",
            "-W", "1",
            server_ips[0]
        ])

    # Router-Server 링크
    elif target_link[0].startswith("R") and target_link[1].startswith("Server"):
        server_name = target_link[1]
        server_index = servers_names.index(server_name)

        result = run_command([
            "docker", "exec",
            "clab-netfaultlab-" + client_names[0],
            "ping", "-c", "2",
            "-W", "1",
            server_ips[server_index]
        ])

    else:
        return test_link_connection(target_link)

    if result.returncode == 0:
        print("Interface Test: SUCCESS")
        return True

    print("Interface Test: FAILED")
    return False


# Wrong IP 장애 주입
def inject_wrong_ip(client_name, wrong_ip):
    target_link = None

    for link in interface_map:
        if link[0] == client_name or link[1] == client_name:
            target_link = link
            break

    if target_link == None:
        print("Client link not found")
        return

    interface = interface_map[target_link][client_name]

    if selected_topology == "Multi VLAN":
        prefix = "26"
    else:
        prefix = "24"

    run_command([
        "docker", "exec",
        "clab-netfaultlab-" + client_name,
        "ip", "addr", "flush",
        "dev", interface
    ])

    run_command([
        "docker", "exec",
        "clab-netfaultlab-" + client_name,
        "ip", "addr", "add",
        wrong_ip + "/" + prefix,
        "dev", interface
    ])

    print("Fault Injected:", client_name, "Wrong IP", wrong_ip)

# LAN Gateway 설정
def configure_server_gateway():
    last_router = router_names[-1]

    # Router에 iproute2 설치
    run_command([
        "docker", "exec",
        "clab-netfaultlab-" + last_router,
        "apk", "add", "--no-cache", "iproute2"
    ])

    # 기존 Server Bridge 제거
    run_command([
        "docker", "exec",
        "clab-netfaultlab-" + last_router,
        "ip", "link", "delete",
        "br-server"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Server Bridge 생성
    run_command([
        "docker", "exec",
        "clab-netfaultlab-" + last_router,
        "ip", "link", "add",
        "br-server",
        "type", "bridge"
    ])

    # Server와 연결된 Router 포트를 Bridge에 연결
    for link in links:
        server_name = None

        if link[0] == last_router and link[1] in servers_names:
            server_name = link[1]

        elif link[1] == last_router and link[0] in servers_names:
            server_name = link[0]

        if server_name == None:
            continue

        router_interface = interface_map[link][last_router]

        run_command([
            "docker", "exec",
            "clab-netfaultlab-" + last_router,
            "ip", "addr", "flush",
            "dev", router_interface
        ])

        run_command([
            "docker", "exec",
            "clab-netfaultlab-" + last_router,
            "ip", "link", "set",
            router_interface,
            "master", "br-server"
        ])

        run_command([
            "docker", "exec",
            "clab-netfaultlab-" + last_router,
            "ip", "link", "set",
            router_interface, "up"
        ])

    # Server Gateway IP 설정
    run_command([
        "docker", "exec",
        "clab-netfaultlab-" + last_router,
        "ip", "addr", "replace",
        server_gateway + "/24",
        "dev", "br-server"
    ])

    run_command([
        "docker", "exec",
        "clab-netfaultlab-" + last_router,
        "ip", "link", "set",
        "br-server", "up"
    ])

    debug_print("Server Gateway configured:", server_gateway)

    # Server 기본 게이트웨이 설정
    for i in range(len(servers_names)):
        server_name = servers_names[i]
        target_link = None

        for link in links:
            if link[0] == server_name or link[1] == server_name:
                target_link = link
                break

        if target_link == None:
            continue

        server_interface = interface_map[target_link][server_name]

        run_command([
            "docker", "exec",
            "clab-netfaultlab-" + server_name,
            "ip", "route", "replace",
            "default",
            "via", server_gateway,
            "dev", server_interface
        ])

        debug_print(
            "Server Gateway configured:",
            server_name,
            server_gateway
        )

# Wrong IP 복구
def recover_wrong_ip(client_name, correct_ip):
    target_link = None

    for link in interface_map:
        if link[0] == client_name or link[1] == client_name:
            target_link = link
            break

    if target_link == None:
        print("Client link not found")
        return

    interface = interface_map[target_link][client_name]

    if selected_topology == "Multi VLAN":
        prefix = "26"
        client_index = client_names.index(client_name)
        correct_gateway = vlan_client_ips[client_index][3]
    else:
        prefix = "24"
        correct_gateway = router_lan_ip

    run_command([
        "docker", "exec",
        "clab-netfaultlab-" + client_name,
        "ip", "addr", "flush",
        "dev", interface
    ])

    # 생성된 정상 IP 복구
    run_command([
        "docker", "exec",
        "clab-netfaultlab-" + client_name,
        "ip", "addr", "add",
        correct_ip + "/" + prefix,
        "dev", interface
    ])

    # 링크 테스트 IP도 함께 복구
    if target_link in link_test_ips:
        if client_name in link_test_ips[target_link]:
            test_ip = link_test_ips[target_link][client_name]

            run_command([
                "docker", "exec",
                "clab-netfaultlab-" + client_name,
                "ip", "addr", "add",
                test_ip + "/30",
                "dev", interface
            ])

    # 기본 게이트웨이 복구
    run_command([
        "docker", "exec",
        "clab-netfaultlab-" + client_name,
        "ip", "route", "replace",
        "default",
        "via", correct_gateway,
        "dev", interface
    ])

    print("Recovery:", client_name, "IP", correct_ip)

def configure_gateway_test(client_name, client_ip, correct_gateway):
    target_link = None

    for link in links:
        if link[0] == client_name or link[1] == client_name:
            target_link = link
            break

    if target_link == None:
        print("Client link not found")
        return None, None

    client_interface = interface_map[target_link][client_name]

    # Gateway 너머 통신 확인용 R1 Loopback IP
    test_ip = "172.31.255.1"

    run_command([
        "docker", "exec",
        "clab-netfaultlab-R1",
        "ip", "addr", "replace",
        test_ip + "/32",
        "dev", "lo"
    ])

    # PC 정상 Gateway 설정
    run_command([
        "docker", "exec",
        "clab-netfaultlab-" + client_name,
        "ip", "route", "replace",
        "default",
        "via", correct_gateway,
        "dev", client_interface
    ])

    print("Gateway test configuration completed")

    return target_link, test_ip

# Wrong Gateway 장애 주입
def inject_wrong_gateway(client_name, target_link, wrong_gateway):
    if target_link == None:
        print("Client link not found")
        return False

    interface = interface_map[target_link][client_name]

    result = run_command([
        "docker", "exec",
        "clab-netfaultlab-" + client_name,
        "ip", "route", "replace",
        "default",
        "via", wrong_gateway,
        "dev", interface,
        "onlink"
    ])

    if result.returncode == 0:
        print(
            "Fault Injected:",
            client_name,
            "Wrong Gateway",
            wrong_gateway
        )
        return True

    print("Wrong Gateway fault injection failed")
    return False


# Gateway 복구
def recover_default_gateway(
    client_name,
    target_link,
    correct_gateway
):
    if target_link == None:
        print("Client link not found")
        return False

    interface = interface_map[target_link][client_name]

    result = run_command([
        "docker", "exec",
        "clab-netfaultlab-" + client_name,
        "ip", "route", "replace",
        "default",
        "via", correct_gateway,
        "dev", interface
    ])

    if result.returncode == 0:
        print(
            "Recovery:",
            client_name,
            "Gateway",
            correct_gateway
        )
        return True

    print("Gateway recovery failed")
    return False


# Gateway 통신 확인
def test_gateway_connection(client_name, target_ip):
    result = run_command([
        "docker", "exec",
        "clab-netfaultlab-" + client_name,
        "ping", "-c", "2",
        "-W", "1",
        target_ip
    ])

    if result.returncode == 0:
        print("Gateway Test: SUCCESS")
        return True

    else:
        print("Gateway Test: FAILED")
        return False




# Static Route 테스트 환경 설정
def configure_static_route_test(target_router, correct_next_hop):
    target_link = None
    neighbor_router = None

    for router_link in router_links:
        left_router = router_link[0]
        left_ip = router_link[1]
        right_router = router_link[2]
        right_ip = router_link[3]

        if target_router == left_router and correct_next_hop == right_ip:
            neighbor_router = right_router
            target_link = find_link(left_router, right_router)
            break

        if target_router == right_router and correct_next_hop == left_ip:
            neighbor_router = left_router
            target_link = find_link(left_router, right_router)
            break

    if target_link == None:
        print("Static route test link not found")
        return None, None

    target_interface = interface_map[target_link][target_router]

    router_number = router_names.index(target_router) + 1
    test_ip = "172.30." + str(router_number) + ".1"

    # 이웃 라우터 loopback에 테스트 목적지 설정
    run_command([
        "docker", "exec",
        "clab-netfaultlab-" + neighbor_router,
        "ip", "addr", "replace",
        test_ip + "/32",
        "dev", "lo"
    ])

    # 정상 정적 경로 설정
    run_command([
        "docker", "exec",
        "clab-netfaultlab-" + target_router,
        "ip", "route", "replace",
        test_ip + "/32",
        "via", correct_next_hop,
        "dev", target_interface
    ])

    print("Static route test configuration completed")

    return target_link, test_ip


# Wrong Static Route 장애 주입
def inject_wrong_static_route(
    target_router,
    target_link,
    test_ip,
    wrong_next_hop
):
    interface = interface_map[target_link][target_router]

    run_command([
        "docker", "exec",
        "clab-netfaultlab-" + target_router,
        "ip", "route", "replace",
        test_ip + "/32",
        "via", wrong_next_hop,
        "dev", interface,
        "onlink"
    ])

    print(
        "Fault Injected:",
        target_router,
        "Wrong Next Hop",
        wrong_next_hop
    )


# Static Route 복구
def recover_static_route(
    target_router,
    target_link,
    test_ip,
    correct_next_hop
):
    interface = interface_map[target_link][target_router]

    run_command([
        "docker", "exec",
        "clab-netfaultlab-" + target_router,
        "ip", "route", "replace",
        test_ip + "/32",
        "via", correct_next_hop,
        "dev", interface
    ])

    print(
        "Recovery:",
        target_router,
        "Next Hop",
        correct_next_hop
    )


# Static Route 통신 확인
def test_static_route_connection(target_router, test_ip):
    result = run_command([
        "docker", "exec",
        "clab-netfaultlab-" + target_router,
        "ping", "-c", "2",
        "-W", "1",
        test_ip
    ])

    if result.returncode == 0:
        print("Static Route Test: SUCCESS")
        return True

    else:
        print("Static Route Test: FAILED")
        return False


# ACL 테스트 준비
def prepare_acl_test(client_name):
    result = run_command([
        "docker", "exec",
        "clab-netfaultlab-" + client_name,
        "sh", "-c",
        "command -v iptables >/dev/null 2>&1 || "
        "apk add --no-cache iptables >/dev/null 2>&1"
    ])

    if result.returncode == 0:
        return True

    print("iptables installation failed")
    return False


# ACL 장애 주입
def inject_acl_block(client_name, target_ip):
    if prepare_acl_test(client_name) == False:
        return False

    result = run_command([
        "docker", "exec",
        "clab-netfaultlab-" + client_name,
        "iptables", "-I", "OUTPUT",
        "-d", target_ip,
        "-j", "DROP"
    ])

    if result.returncode == 0:
        print("Fault Injected:", client_name, "ACL Block", target_ip)
        return True

    print("ACL fault injection failed")
    return False


# ACL 복구
def recover_acl_block(client_name, target_ip):
    result = run_command([
        "docker", "exec",
        "clab-netfaultlab-" + client_name,
        "iptables", "-D", "OUTPUT",
        "-d", target_ip,
        "-j", "DROP"
    ])

    if result.returncode == 0:
        print("Recovery:", client_name, "ACL removed")
        return True

    print("ACL recovery failed")
    return False


# ACL 통신 확인
def test_acl_connection(client_name, target_ip):
    result = run_command([
        "docker", "exec",
        "clab-netfaultlab-" + client_name,
        "ping", "-c", "2",
        "-W", "1",
        target_ip
    ])

    if result.returncode == 0:
        print("ACL Test: SUCCESS")
        return True

    else:
        print("ACL Test: FAILED")
        return False

# LAN Gateway 설정
def configure_lan_gateway():
    # R1에 iproute2 설치
    run_command([
        "docker", "exec",
        "clab-netfaultlab-R1",
        "apk", "add", "--no-cache", "iproute2"
    ])

    # 기존 LAN Bridge 제거
    run_command([
        "docker", "exec",
        "clab-netfaultlab-R1",
        "ip", "link", "delete", "br-lan"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if selected_topology == "Multi VLAN":
        # VLAN filtering이 가능한 R1 LAN Bridge 생성
        run_command([
            "docker", "exec",
            "clab-netfaultlab-R1",
            "ip", "link", "add", "br-lan",
            "type", "bridge",
            "vlan_filtering", "1"
        ])
    else:
        run_command([
            "docker", "exec",
            "clab-netfaultlab-R1",
            "ip", "link", "add", "br-lan",
            "type", "bridge"
        ])

    # Switch와 연결된 R1 포트들을 br-lan에 연결
    for link in links:
        switch_name = None

        if link[0] in switch_names and link[1] == "R1":
            switch_name = link[0]
        elif link[1] in switch_names and link[0] == "R1":
            switch_name = link[1]

        if switch_name == None:
            continue

        router_interface = interface_map[link]["R1"]

        run_command([
            "docker", "exec",
            "clab-netfaultlab-R1",
            "ip", "addr", "flush",
            "dev", router_interface
        ])

        run_command([
            "docker", "exec",
            "clab-netfaultlab-R1",
            "ip", "link", "set",
            router_interface,
            "master", "br-lan"
        ])

        run_command([
            "docker", "exec",
            "clab-netfaultlab-R1",
            "ip", "link", "set",
            router_interface, "up"
        ])

        if selected_topology == "Multi VLAN":
            # R1의 Switch 연결 포트는 Trunk
            run_command([
                "docker", "exec",
                "clab-netfaultlab-R1",
                "bridge", "vlan", "del",
                "dev", router_interface,
                "vid", "1"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            for vlan_id in vlan_ids:
                run_command([
                    "docker", "exec",
                    "clab-netfaultlab-R1",
                    "bridge", "vlan", "add",
                    "dev", router_interface,
                    "vid", str(vlan_id)
                ])

        else:
            # 일반 LAN은 기존 링크 테스트 IP 유지
            if link in link_test_ips and "R1" in link_test_ips[link]:
                test_ip = link_test_ips[link]["R1"]

                run_command([
                    "docker", "exec",
                    "clab-netfaultlab-R1",
                    "ip", "addr", "replace",
                    test_ip + "/30",
                    "dev", "br-lan"
                ])

    run_command([
        "docker", "exec",
        "clab-netfaultlab-R1",
        "ip", "link", "set",
        "br-lan", "up"
    ])

    if selected_topology == "Multi VLAN":
        # R1 Bridge 자체가 VLAN 프레임을 받을 수 있게 설정
        for vlan_id in vlan_ids:
            run_command([
                "docker", "exec",
                "clab-netfaultlab-R1",
                "bridge", "vlan", "add",
                "dev", "br-lan",
                "vid", str(vlan_id),
                "self"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            vlan_interface = "br-lan." + str(vlan_id)

            run_command([
                "docker", "exec",
                "clab-netfaultlab-R1",
                "ip", "link", "delete",
                vlan_interface
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            run_command([
                "docker", "exec",
                "clab-netfaultlab-R1",
                "ip", "link", "add",
                "link", "br-lan",
                "name", vlan_interface,
                "type", "vlan",
                "id", str(vlan_id)
            ])

            run_command([
                "docker", "exec",
                "clab-netfaultlab-R1",
                "ip", "addr", "replace",
                vlan_gateways[vlan_id] + "/26",
                "dev", vlan_interface
            ])

            run_command([
                "docker", "exec",
                "clab-netfaultlab-R1",
                "ip", "link", "set",
                vlan_interface, "up"
            ])

            debug_print(
                "R1 VLAN Gateway configured:",
                "VLAN", vlan_id,
                vlan_gateways[vlan_id]
            )

        # 각 PC에 자기 VLAN Gateway 설정
        for i in range(len(vlan_client_ips)):
            client_name = vlan_client_ips[i][0]
            gateway = vlan_client_ips[i][3]
            target_client_link = None

            for link in links:
                if link[0] == client_name or link[1] == client_name:
                    target_client_link = link
                    break

            if target_client_link == None:
                continue

            client_interface = interface_map[target_client_link][client_name]

            run_command([
                "docker", "exec",
                "clab-netfaultlab-" + client_name,
                "ip", "route", "replace",
                "default",
                "via", gateway,
                "dev", client_interface
            ])

            debug_print(
                "VLAN Gateway configured:",
                client_name,
                gateway
            )

        return

    # 일반 LAN Gateway IP 설정
    run_command([
        "docker", "exec",
        "clab-netfaultlab-R1",
        "ip", "addr", "replace",
        router_lan_ip + "/24",
        "dev", "br-lan"
    ])

    debug_print("R1 LAN Gateway configured:", router_lan_ip)

    # 각 PC 기본 게이트웨이 설정
    for i in range(len(client_names)):
        client_name = client_names[i]
        target_client_link = None

        for link in links:
            if link[0] == client_name or link[1] == client_name:
                target_client_link = link
                break

        if target_client_link == None:
            continue

        client_interface = interface_map[target_client_link][client_name]

        run_command([
            "docker", "exec",
            "clab-netfaultlab-" + client_name,
            "ip", "route", "replace",
            "default",
            "via", router_lan_ip,
            "dev", client_interface
        ])

        debug_print(
            "Default Gateway configured:",
            client_name,
            router_lan_ip
        )

def configure_real_routing():
    # 모든 Router에서 IP Forwarding 활성화
    for router in router_names:
        run_command([
            "docker", "exec",
            "clab-netfaultlab-" + router,
            "sysctl", "-w",
            "net.ipv4.ip_forward=1"
        ])

    # Python에서 생성된 Routing Table 적용
    for router in router_names:
        for route in routing_tables[router]:
            destination = route[0]
            next_hop = route[1]

            run_command([
                "docker", "exec",
                "clab-netfaultlab-" + router,
                "ip", "route", "replace",
                destination,
                "via", next_hop
            ])

    debug_print("Real routing configuration completed")

# PC → Server 통신 확인
# PC -> Server 실제 통신 확인
def test_pc_to_server():
    server_name = servers_names[0]
    target_ip = server_ips[0]
    all_success = True

    if selected_topology == "Multi VLAN":
        for i in range(len(client_names)):
            client_name = client_names[i]
            vlan_id = vlan_client_ips[i][1]

            debug_print(
                "PC -> Server:",
                client_name,
                "VLAN", vlan_id,
                "->",
                server_name,
                target_ip
            )

            result = run_command([
                "docker", "exec",
                "clab-netfaultlab-" + client_name,
                "ping", "-c", "2",
                "-W", "1",
                target_ip
            ])

            if result.returncode != 0:
                all_success = False

    else:
        client_name = client_names[0]

        debug_print(
            "PC -> Server:",
            client_name,
            "->",
            server_name,
            target_ip
        )

        result = run_command([
            "docker", "exec",
            "clab-netfaultlab-" + client_name,
            "ping", "-c", "2",
            "-W", "1",
            target_ip
        ])

        if result.returncode != 0:
            all_success = False

    if all_success:
        print("Initial End-to-End Test: SUCCESS")
    else:
        print("Initial End-to-End Test: FAILED")

    return all_success


# 다중 라우터 실제 경로 확인
# 다중 라우터 실제 경로 확인
def test_multi_router_path():
    if len(router_names) <= 1:
        return True

    all_success = True

    # Router-Router 직접 연결 확인
    for router_link in router_links:
        left_router = router_link[0]
        right_router = router_link[2]
        right_ip = router_link[3]

        debug_print(
            "Router Hop:",
            left_router,
            "->",
            right_router,
            right_ip
        )

        result = run_command([
            "docker", "exec",
            "clab-netfaultlab-" + left_router,
            "ping", "-c", "2",
            "-W", "1",
            right_ip
        ])

        if result.returncode != 0:
            all_success = False

    # PC -> Server 전체 경로 확인
    client_name = client_names[0]
    server_ip = server_ips[0]

    result = run_command([
        "docker", "exec",
        "clab-netfaultlab-" + client_name,
        "ping", "-c", "2",
        "-W", "1",
        server_ip
    ])

    if result.returncode != 0:
        all_success = False

    if all_success:
        print("Multi Router Path Test: SUCCESS")
    else:
        print("Multi Router Path Test: FAILED")

    return all_success


# Seed 설정
seed = input("Seed (Enter = Random): ")

if seed == "":
    seed = random.randint(1000, 999999)

random.seed(int(seed))


# 네트워크 종류
topologies = ["Small Office", "Branch Network", "Multi VLAN"]
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

# 서버 네트워크
server_netwrok = "172.16.18"
server_gateway = server_netwrok + ".1"

server_ips = []

for i in range(len(servers_names)):
    ip = server_netwrok + "." + str(i + 10)
    server_ips.append(ip)

# PC 네트워크
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

        vlan_client_ips.append(
            (client_names[i], vlan_id, ip, vlan_gateways[vlan_id])
        )

    for vlan_id in vlan_ids:
        router_vlan_interfaces.append(
            ("R1", vlan_id, vlan_gateways[vlan_id])
        )

# 라우터 사이 IP
router_links = []

for i in range(len(router_names) - 1):
    network_number = i + 1

    left_ip = "10.0." + str(network_number) + ".1"
    right_ip = "10.0." + str(network_number) + ".2"

    router_links.append(
        (router_names[i], left_ip, router_names[i + 1], right_ip)
    )

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
    for i in range(len(client_names)):
        vlan_index = i % len(vlan_ids)
        switch_index = i % len(switch_names)

        vlan_id = vlan_ids[vlan_index]

        links.append(
            (client_names[i], switch_names[switch_index], vlan_id)
        )

    for switch in switch_names:
        links.append((switch, "R1"))

    for i in range(len(router_names) - 1):
        links.append((router_names[i], router_names[i + 1]))

    for server in servers_names:
        links.append((router_names[-1], server))

# ===== 2. Lab 배포 및 네트워크 적용 =====
create_containerlab(links)
deploy_containerlab()

configure_router_ips(router_links)
configure_link_test_ips(links)
configure_switch_bridges()
configure_generated_ips()
configure_lan_gateway()
configure_server_gateway()

# 라우팅 테이블
routing_tables = {}

for router in router_names:
    routing_tables[router] = []

if len(router_names) > 1:
    for i in range(len(router_names) - 1):
        current_router = router_names[i]
        next_router_ip = router_links[i][3]

        routing_tables[current_router].append(
            (server_netwrok + ".0/24", next_router_ip)
        )

if len(router_names) > 1:
    for i in range(1, len(router_names)):
        current_router = router_names[i]
        previous_router_ip = router_links[i - 1][1]

        if selected_topology == "Multi VLAN":
            for vlan_id in vlan_ids:
                routing_tables[current_router].append(
                    (vlan_networks[vlan_id], previous_router_ip)
                )

        else:
            routing_tables[current_router].append(
                (lan_network + ".0/24", previous_router_ip)
            )

# 실제 Routing 설정
configure_real_routing()

# 전체 PC -> Server 통신 확인
test_pc_to_server()

# Router가 2대 이상이면 Hop / End-to-End 추가 확인
test_multi_router_path()

# ===== 3. 장애 시나리오 선택 =====
# 가능한 장애 종류
available_faults = [
    "Interface Down",
    "Wrong IP Address",
    "Wrong Default Gateway",
    "ACL Block"
]

# Static Route가 있을 때만 추가
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
    "acl_rules": copy.deepcopy(acl_rules)
}

# ===== 4. 장애 주입 및 통신 확인 =====
# 장애 주입
if selected_fault == "Wrong Static Route":
    possible_routers = []

    for router in router_names:
        if len(routing_tables[router]) > 0:
            possible_routers.append(router)

    if len(possible_routers) > 0:
        target_router = random.choice(possible_routers)
        route_index = random.randint(
            0,
            len(routing_tables[target_router]) - 1
        )

        old_route = routing_tables[target_router][route_index]

        destination = old_route[0]
        old_next_hop = old_route[1]
        wrong_next_hop = "10.255.255.254"

        routing_tables[target_router][route_index] = (
            destination,
            wrong_next_hop
        )

        # Static Route 테스트 환경 설정
        target_link, route_test_ip = configure_static_route_test(
            target_router,
            old_next_hop
        )

        fault_info = {
            "target": target_router,
            "destination": destination,
            "old_value": old_next_hop,
            "wrong_value": wrong_next_hop,
            "link": target_link,
            "test_ip": route_test_ip
        }

        # 장애 전 통신 확인
        print("\n=== Healthy Static Route Test ===")
        test_static_route_connection(
            target_router,
            route_test_ip
        )

        # Wrong Static Route 장애 주입
        inject_wrong_static_route(
            target_router,
            target_link,
            route_test_ip,
            wrong_next_hop
        )

        # 장애 후 통신 확인
        print("\n=== Fault Static Route Test ===")
        test_static_route_connection(
            target_router,
            route_test_ip
        )

elif selected_fault == "Wrong Default Gateway":
    if selected_topology == "Multi VLAN":
        target_client_index = random.randint(
            0,
            len(vlan_client_ips) - 1
        )

        target_client = vlan_client_ips[target_client_index]

        client_name = target_client[0]
        vlan_id = target_client[1]
        client_ip = target_client[2]
        old_gateway = target_client[3]

        wrong_gateway = "192.168.255.254"

        vlan_client_ips[target_client_index] = (
            client_name,
            vlan_id,
            client_ip,
            wrong_gateway
        )

    else:
        target_client_index = random.randint(
            0,
            len(client_names) - 1
        )

        client_name = client_names[target_client_index]
        client_ip = client_ips[target_client_index]

        old_gateway = client_gateways[target_client_index]
        wrong_gateway = lan_network + ".254"

        client_gateways[target_client_index] = wrong_gateway

    # Gateway 테스트 환경 설정
    target_link, gateway_test_ip = configure_gateway_test(
        client_name,
        client_ip,
        old_gateway
    )

    fault_info = {
        "target": client_name,
        "old_value": old_gateway,
        "wrong_value": wrong_gateway,
        "link": target_link,
        "test_ip": gateway_test_ip
    }

    # 장애 전 통신 확인
    print("\n=== Healthy Gateway Test ===")
    test_gateway_connection(client_name, gateway_test_ip)

    # Wrong Gateway 장애 주입
    inject_wrong_gateway(
        client_name,
        target_link,
        wrong_gateway
    )

    # 장애 후 통신 확인
    print("\n=== Fault Gateway Test ===")
    test_gateway_connection(client_name, gateway_test_ip)

elif selected_fault == "Wrong IP Address":
    target_client_index = random.randint(
        0,
        len(client_names) - 1
    )

    client_name = client_names[target_client_index]

    if selected_topology == "Multi VLAN":
        target_client = vlan_client_ips[target_client_index]

        vlan_id = target_client[1]
        old_ip = target_client[2]
        gateway = target_client[3]

        wrong_ip = "192.168.250." + str(target_client_index + 10)

        vlan_client_ips[target_client_index] = (
            client_name,
            vlan_id,
            wrong_ip,
            gateway
        )

    else:
        old_ip = client_ips[target_client_index]
        wrong_ip = "192.168.250." + str(target_client_index + 10)

        client_ips[target_client_index] = wrong_ip

    # 대상 PC 링크 찾기
    target_link = None

    for link in links:
        if link[0] == client_name or link[1] == client_name:
            target_link = link
            break

    fault_info = {
        "target": client_name,
        "old_value": old_ip,
        "wrong_value": wrong_ip,
        "link": target_link
    }

    # 장애 전 통신 확인
    print("\n=== Healthy IP Test ===")

    if selected_topology == "Multi VLAN":
        test_gateway_connection(
            client_name,
            gateway
        )
    else:
        test_gateway_connection(
            client_name,
            router_lan_ip
        )

    # Wrong IP 장애 주입
    inject_wrong_ip(client_name, wrong_ip)

    # 장애 후 통신 확인
    print("\n=== Fault IP Test ===")

    if selected_topology == "Multi VLAN":
        test_gateway_connection(
            client_name,
            gateway
        )
    else:
        test_gateway_connection(
            client_name,
            router_lan_ip
        )

elif selected_fault == "Interface Down":
    target_link_index = random.randint(0, len(links) - 1)
    target_link = links[target_link_index]

    down_links.append(target_link)

    fault_info = {
        "target": target_link
    }

    # 장애 전 통신 확인
    print("\n=== Healthy Interface Test ===")
    test_interface_fault_connection(target_link)

    # Interface Down 장애 주입
    inject_interface_down(target_link)

    # 장애 후 통신 확인
    print("\n=== Fault Interface Test ===")
    test_interface_fault_connection(target_link)

elif selected_fault == "ACL Block":
    target_client_index = random.randint(
        0,
        len(client_names) - 1
    )

    client_name = client_names[target_client_index]

    if selected_topology == "Multi VLAN":
        client_ip = vlan_client_ips[target_client_index][2]

    else:
        client_ip = client_ips[target_client_index]

    target_server = random.choice(servers_names)

    # 대상 PC 링크 찾기
    target_link = None

    for link in links:
        if link[0] == client_name or link[1] == client_name:
            target_link = link
            break

    # ACL은 실제 Server IP 통신을 차단
    target_server_index = servers_names.index(target_server)
    acl_test_ip = server_ips[target_server_index]

    acl_rules.append(
        ("DENY", client_ip, target_server)
    )

    fault_info = {
        "target": client_name,
        "client_ip": client_ip,
        "server": target_server,
        "link": target_link,
        "test_ip": acl_test_ip
    }

    # 장애 전 통신 확인
    print("\n=== Healthy ACL Test ===")
    test_acl_connection(
        client_name,
        acl_test_ip
    )

    # ACL 장애 주입
    inject_acl_block(
        client_name,
        acl_test_ip
    )

    # 장애 후 통신 확인
    print("\n=== Fault ACL Test ===")
    test_acl_connection(
        client_name,
        acl_test_ip
    )

# 네트워크 상세 정보 출력
if debug_mode:
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
            print(
                " Destination :",
                route[0],
                " Next Hop :",
                route[1]
            )

    print("\n=== Server Network ===")
    print("Server Network :", server_netwrok + ".0/24")
    print("Server Gateway :", server_gateway)

    for i in range(len(servers_names)):
        print(servers_names[i], ":", server_ips[i])

    if selected_topology == "Multi VLAN":
        print("\n=== VLAN Clients ===")

        for client in vlan_client_ips:
            print(client)

        print("\n=== Router VLAN Interfaces ===")

        for vlan_id in vlan_ids:
            print(
                "VLAN",
                vlan_id,
                ":",
                vlan_networks[vlan_id],
                "Gateway :",
                vlan_gateways[vlan_id]
            )

    print("\n=== 장비 갯수 ===")
    print("Routers :", routers)
    print("Switches :", switches)
    print("Clients :", clients)
    print("Servers :", servers)

    print("\n=== 장비 이름 ===")
    print("Routers :", router_names)
    print("Switches :", switch_names)
    print("Clients :", client_names)
    print("Servers :", servers_names)

    if selected_topology != "Multi VLAN":
        print("\n=== Client Network ===")

        for i in range(len(client_names)):
            print(
                client_names[i],
                "IP:",
                client_ips[i],
                "Gateway:",
                client_gateways[i]
            )

        print("Router LAN IP :", router_lan_ip)
        print("Default Gateway :", default_gateway)

# 장애 증상 출력
print("\n=== Problem ===")

if selected_fault == "Wrong IP Address":
    print(
        fault_info["target"],
        "cannot reach the network"
    )

elif selected_fault == "Wrong Default Gateway":
    print(
        fault_info["target"],
        "cannot reach",
        random.choice(servers_names)
    )

elif selected_fault == "Wrong Static Route":
    print("Clients cannot reach the Server Network")

elif selected_fault == "Interface Down":
    down_link = fault_info["target"]

    left_device = down_link[0]
    right_device = down_link[1]

    if left_device.startswith("PC"):
        print(
            left_device,
            "cannot reach the network"
        )

    elif right_device.startswith("Server"):
        print(
            "Clients cannot reach",
            right_device
        )

    elif left_device.startswith("SW") and right_device.startswith("R"):
        affected_clients = []

        for link in links:
            if link[0].startswith("PC") and link[1] == left_device:
                affected_clients.append(link[0])

        print("Affected Clients:", affected_clients)
        print("cannot reach the Server Network")

    elif left_device.startswith("R") and right_device.startswith("R"):
        print("Network path to the Server Network is unavailable")

    else:
        print("Network connectivity problem detected")

elif selected_fault == "ACL Block":
    print(
        fault_info["target"],
        "cannot reach",
        fault_info["server"]
    )

# ===== 5. 사용자 복구 및 검증 =====
print("\n=== Recovery Check ===")

if selected_fault == "Wrong Static Route":
    user_answer = input("Correct Next Hop: ")

    if user_answer == fault_info["old_value"]:
        target_router = fault_info["target"]

        for i in range(len(routing_tables[target_router])):
            route = routing_tables[target_router][i]

            if route[0] == fault_info["destination"]:
                routing_tables[target_router][i] = (
                    fault_info["destination"],
                    fault_info["old_value"]
                )

        # Static Route 복구
        recover_static_route(
            target_router,
            fault_info["link"],
            fault_info["test_ip"],
            fault_info["old_value"]
        )

        # 복구 후 통신 확인
        print("\n=== Recovery Static Route Test ===")
        recovery_result = test_static_route_connection(
            target_router,
            fault_info["test_ip"]
        )

        if recovery_result == True:
            print("Recovery Successful")
        else:
            print("Recovery Failed")

    else:
        print("Recovery Failed")

elif selected_fault == "Wrong Default Gateway":
    user_answer = input("Correct Gateway: ")

    if user_answer == fault_info["old_value"]:
        target_client = fault_info["target"]
        target_index = client_names.index(target_client)

        if selected_topology == "Multi VLAN":
            old_client = vlan_client_ips[target_index]

            vlan_client_ips[target_index] = (
                old_client[0],
                old_client[1],
                old_client[2],
                fault_info["old_value"]
            )

        else:
            client_gateways[target_index] = fault_info["old_value"]

        # Gateway 복구
        recover_default_gateway(
            target_client,
            fault_info["link"],
            fault_info["old_value"]
        )

        # 복구 후 통신 확인
        print("\n=== Recovery Gateway Test ===")
        recovery_result = test_gateway_connection(
            target_client,
            fault_info["test_ip"]
        )

        if recovery_result == True:
            print("Recovery Successful")
        else:
            print("Recovery Failed")

    else:
        print("Recovery Failed")

elif selected_fault == "Wrong IP Address":
    user_answer = input("Correct IP Address: ")

    if user_answer == fault_info["old_value"]:
        target_client = fault_info["target"]
        target_index = client_names.index(target_client)

        if selected_topology == "Multi VLAN":
            old_client = vlan_client_ips[target_index]

            vlan_client_ips[target_index] = (
                old_client[0],
                old_client[1],
                fault_info["old_value"],
                old_client[3]
            )

        else:
            client_ips[target_index] = fault_info["old_value"]

        # Wrong IP 복구
        recover_wrong_ip(
            target_client,
            fault_info["old_value"]
        )

        # 복구 후 통신 확인
        print("\n=== Recovery IP Test ===")

        if selected_topology == "Multi VLAN":
            target_index = client_names.index(target_client)
            recovery_gateway = vlan_client_ips[target_index][3]

            recovery_result = test_gateway_connection(
                target_client,
                recovery_gateway
            )
        else:
            recovery_result = test_gateway_connection(
                target_client,
                router_lan_ip
            )

        if recovery_result == True:
            print("Recovery Successful")
        else:
            print("Recovery Failed")

    else:
        print("Recovery Failed")

elif selected_fault == "Interface Down":
    user_answer = input("Interface State (up/down): ")

    if user_answer.lower() == "up":
        target_link = fault_info["target"]

        if target_link in down_links:
            down_links.remove(target_link)

        # Interface Down 복구
        recover_interface(target_link)

        # Router-Router 링크는 인터페이스가 내려가면서
        # 커널의 정적 경로가 함께 사라질 수 있으므로 다시 적용
        if (
            target_link[0].startswith("R")
            and target_link[1].startswith("R")
        ):
            configure_router_ips(router_links)
            configure_real_routing()

        # 복구 후 실제 통신 확인
        print("\n=== Recovery Interface Test ===")
        recovery_result = test_interface_fault_connection(
            target_link
        )

        if recovery_result == True:
            print("Recovery Successful")
        else:
            print("Recovery Failed")

    else:
        print("Recovery Failed")

elif selected_fault == "ACL Block":
    user_answer = input("ACL Action (remove/keep): ")

    if user_answer.lower() == "remove":
        target_rule = (
            "DENY",
            fault_info["client_ip"],
            fault_info["server"]
        )

        if target_rule in acl_rules:
            acl_rules.remove(target_rule)

        # ACL 복구
        recover_acl_block(
            fault_info["target"],
            fault_info["test_ip"]
        )

        # 복구 후 통신 확인
        print("\n=== Recovery ACL Test ===")
        recovery_result = test_acl_connection(
            fault_info["target"],
            fault_info["test_ip"]
        )

        if recovery_result == True:
            print("Recovery Successful")
        else:
            print("Recovery Failed")

    else:
        print("Recovery Failed")

# ===== 디버그 정보 =====
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

# ===== 6. 최종 상태 검증 =====
current_state = {
    "client_ips": copy.deepcopy(client_ips),
    "client_gateways": copy.deepcopy(client_gateways),
    "vlan_client_ips": copy.deepcopy(vlan_client_ips),
    "routing_tables": copy.deepcopy(routing_tables),
    "down_links": copy.deepcopy(down_links),
    "acl_rules": copy.deepcopy(acl_rules)
}

# 복구 검증
print("\n=== Verification ===")

if current_state == healthy_state:
    print("Network Recovery Verified")

else:
    print("Recovery Verification Failed")
