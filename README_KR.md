# NetFaultLab

NetFaultLab은 Python과 Containerlab을 이용해 실제 Linux 네트워크 토폴로지를 만들고, 실행 중인 네트워크에 장애를 주입한 뒤 사용자가 직접 원인을 분석하고 복구하도록 만든 네트워크 트러블슈팅 실습 프로젝트입니다.

단순히 장애 정답을 보여주는 시뮬레이터가 아니라, 일반 모드에서는 장애 종류와 잘못된 값을 숨기고 사용자가 IP, 게이트웨이, 라우팅, 인터페이스, ACL, Ping 결과를 직접 확인하면서 문제를 찾도록 설계했습니다.

[English README](README.md)

## 주요 기능

- Seed 기반 랜덤 토폴로지 생성 및 재현
- 실제 Containerlab Linux 노드 사용
- Linux Bridge 기반 스위치 구성
- 다중 라우터 정적 라우팅
- VLAN 10 / 20 / 30 실제 구성
- Client → Server 실제 End-to-End 통신
- 한 번 Lab을 올린 뒤 계속 사용하는 상시 실행 CLI
- 실행 중인 Lab에 직접 설정 변경 가능
- 장애 정답을 바로 노출하지 않는 트러블슈팅 방식
- `lab_state.json`을 통한 NetworkMonitor 연동
- 개발용 상세 로그를 위한 Debug Mode

## 지원 토폴로지

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

현재 VLAN 네트워크:

| VLAN | 네트워크 | 게이트웨이 |
|---|---|---|
| 10 | `192.168.100.0/26` | `192.168.100.1` |
| 20 | `192.168.100.64/26` | `192.168.100.65` |
| 30 | `192.168.100.128/26` | `192.168.100.129` |

Server 네트워크:

```text
172.16.18.0/24
Gateway: 172.16.18.1
```

라우터 간 링크는 `10.0.x.0/30` 대역을 사용합니다.

## 장애 시나리오

현재 지원하는 장애는 5종입니다.

- Interface Down
- Wrong IP Address
- Wrong Default Gateway
- Wrong Static Route
- ACL Block

랜덤 장애 주입:

```text
netfault> inject
```

특정 장애 주입:

```text
netfault> inject ip
netfault> inject gateway
netfault> inject route
netfault> inject interface
netfault> inject acl
```

일반 모드에서는 장애 종류, 대상 장비, 잘못된 설정값을 바로 보여주지 않습니다.

## 트러블슈팅 CLI

Lab이 생성된 뒤 프로그램은 종료되지 않고 `netfault>` 프롬프트에서 계속 명령을 받을 수 있습니다.

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

예시:

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

`configure` 명령을 입력하면 실제 설정 변경 메뉴가 열립니다.

```text
1. IP Address
2. Default Gateway
3. Static Route
4. Interface State
5. ACL Rule
6. Cancel
```

선택한 설정은 실제 실행 중인 Containerlab에 바로 적용됩니다. 잘못된 복구를 시도하면 기존 장애에 새로운 설정 오류가 추가될 수도 있습니다.

## 복구 검증

`verify`는 두 가지를 함께 확인합니다.

- Python 내부 상태가 최초 정상 상태와 동일한지
- 실제 End-to-End 통신이 복구되었는지

정상 복구 시:

```text
Network Recovery Verified
```

가 출력됩니다.

## NetworkMonitor 연동

NetFaultLab은 현재 Lab 구성을 다음 파일로 저장합니다.

```text
lab_state.json
```

이 파일에는 현재 토폴로지, 장비, IP 정보, 링크 정보가 들어갑니다.

장애의 정답 자체는 전달하지 않으며, NetworkMonitor가 실제 실행 중인 Containerlab을 직접 확인하도록 구성했습니다.

## Debug Mode

일반 모드:

```python
debug_mode = False
```

- 장애 종류/대상 숨김
- 긴 Containerlab/명령 출력 숨김
- 문제 해결에 필요한 정보 위주로 사용

개발/디버깅 모드:

```python
debug_mode = True
```

- 상세 장애 정보 확인
- 내부 테스트 및 명령 출력 확인

## 필요 환경

- Linux 또는 WSL2
- Python 3
- Docker Engine
- Containerlab
- Lab 구성 중 Alpine 패키지 설치를 위한 인터넷 연결

## 실행

```bash
python3 main.py
```

Seed를 입력하거나 Enter를 눌러 랜덤 Seed를 사용할 수 있습니다.

```text
Seed (Enter = Random):
```

이후 `netfault>` 프롬프트에서 문제를 풀면 됩니다.

## 재현용 Seed

Seed를 사용하면 같은 랜덤 생성 결과를 다시 테스트하는 데 도움이 됩니다.

개발 중 사용한 예시:

```text
91838   - 다중 라우터 / Static Route 테스트
18594   - Wrong IP 테스트
5133    - Wrong Gateway 테스트
851701  - Interface Down 테스트
327842  - Multi VLAN Gateway 테스트
602168  - Multi VLAN 다중 라우터 테스트
```

코드가 변경되면 동일 Seed의 결과도 달라질 수 있으므로 고정된 API처럼 보장되는 값은 아닙니다.

## 현재 한계

- 실제 Cisco/Juniper 장비 이미지 대신 Linux 컨테이너를 사용합니다.
- 동적 라우팅 프로토콜은 아직 구현하지 않았고 정적 라우팅을 사용합니다.
- 현재 인터페이스는 CLI이며, PuTTY 스타일 터미널 GUI를 추가할 예정입니다.
- 일부 검증 경로에는 내부 테스트용 주소가 남아 있을 수 있습니다.
- NetworkMonitor 연동은 현재 `lab_state.json`과 Docker/Containerlab 직접 확인 방식을 사용합니다.
- 학습 및 포트폴리오용 프로젝트이며 실제 운영망 자동화 도구를 목적으로 하지 않습니다.

## 관련 프로젝트

NetworkMonitor는 NetFaultLab이 만든 실제 Lab을 감시하고 `WARNING`, `DOWN`, `RECOVERED` 상태 변화를 기록하는 companion 프로젝트입니다.
