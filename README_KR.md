[English README](README.md)

# NetFaultLab

NetFaultLab은 랜덤한 가상 네트워크 토폴로지를 생성하고, 네트워크 장애를 주입한 뒤 사용자가 직접 원인을 진단하고 복구할 수 있도록 만든 네트워크 트러블슈팅 연습 프로젝트입니다.

처음에는 Python 기반 시뮬레이션으로 시작했으며, 현재는 Docker와 Containerlab을 이용해 실제 Linux 컨테이너 네트워크에 장애를 적용하고 복구 과정을 검증하는 형태로 확장되었습니다.

## 주요 기능

- 랜덤 네트워크 토폴로지 생성
- 여러 네트워크 구조 지원
  - Small Office
  - Branch Network
  - Multi VLAN
- 장비 수와 IP 설정 랜덤 생성
- Seed 기반 시나리오 재현
- Containerlab 토폴로지 자동 생성
- Containerlab 자동 배포
- Docker 기반 Linux 네트워크 노드 구성
- 인터페이스 자동 매핑
- 실제 네트워크 장애 주입
- 실제 복구 작업 수행
- Ping 기반 통신 검증
- 복구 후 내부 네트워크 상태 검증

## 지원 장애 시나리오

현재 NetFaultLab은 다음 장애를 지원합니다.

- Interface Down
- Wrong IP Address
- Wrong Default Gateway
- Wrong Static Route
- ACL Block

각 장애 시나리오는 다음과 같은 트러블슈팅 흐름으로 진행됩니다.

1. 정상 네트워크 상태 생성
2. Containerlab으로 네트워크 배포
3. 정상 통신 확인
4. 네트워크 장애 주입
5. 장애 상태에서 통신 실패 확인
6. 사용자가 원인을 확인하고 복구 값 입력
7. 실제 복구 설정 적용
8. 복구 후 통신 재확인
9. 복구된 상태와 초기 정상 상태 비교

## 실제 장애 주입

### Interface Down

랜덤하게 네트워크 링크를 선택하고 Containerlab 내부의 실제 Linux 인터페이스를 비활성화합니다.

```bash
ip link set eth1 down
```

사용자가 복구 명령을 입력하면 인터페이스를 다시 활성화합니다.

```bash
ip link set eth1 up
```

장애 전, 장애 후, 복구 후에 각각 통신 상태를 확인합니다.

### Wrong IP Address

랜덤으로 클라이언트를 선택하고 실제 Containerlab 노드에 잘못된 IP 주소를 설정합니다.

사용자가 올바른 IP 주소를 입력하면 기존 정상 IP 설정으로 복구합니다.

장애 전, 장애 후, 복구 후에 Ping을 이용해 통신 상태를 검증합니다.

### Wrong Default Gateway

클라이언트의 기본 게이트웨이를 잘못된 값으로 변경합니다.

Containerlab 내부 Linux 라우팅 테이블의 실제 기본 경로를 변경하여 통신 실패를 발생시킵니다.

사용자가 올바른 게이트웨이를 입력하면 실제 기본 경로를 복구하고 통신을 다시 확인합니다.

### Wrong Static Route

라우터의 정적 경로 Next Hop을 잘못된 주소로 변경합니다.

Linux의 `ip route` 명령을 이용해 실제 라우팅 테이블을 수정합니다.

사용자가 올바른 Next Hop을 입력하면 기존 경로로 복구하고 통신 상태를 다시 검증합니다.

### ACL Block

Linux의 `iptables`를 이용해 특정 트래픽을 차단합니다.

ACL 장애가 적용되면 선택된 대상에 대한 통신이 실패하도록 설정합니다.

사용자가 ACL 제거를 선택하면 해당 규칙을 삭제하고 통신을 다시 확인합니다.

## 네트워크 토폴로지

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

라우터, 스위치, 클라이언트, 서버의 개수는 실행할 때마다 생성되는 시나리오에 따라 달라질 수 있습니다.

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

클라이언트는 여러 VLAN에 분배됩니다.

```text
VLAN 10
VLAN 20
VLAN 30
```

프로그램에서 VLAN 네트워크, 게이트웨이, 클라이언트 IP 주소를 자동으로 생성합니다.

## 실행 예시

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

## 사용 기술

- Python
- Linux
- Docker
- Containerlab
- iproute2
- iptables
- Git
- GitHub

## 프로젝트 구조

```text
NetFaultLab/
├── main.py
├── README.md
├── .gitignore
├── lab.clab.yml
└── logs.txt
```

`lab.clab.yml` 파일은 프로그램 실행 과정에서 자동으로 생성됩니다.

로그 파일이나 자동 생성 파일은 환경에 따라 Git에서 제외할 수 있습니다.

## 실행 환경

현재 개발 환경은 다음과 같습니다.

- Ubuntu 22.04
- WSL2
- Python 3
- Docker Engine
- Containerlab

Containerlab을 사용하려면 Docker가 실행 중이어야 합니다.

## 설치 및 실행

저장소를 Clone 합니다.

```bash
git clone git@github.com:cwj6676/NetFaultLab.git
```

프로젝트 폴더로 이동합니다.

```bash
cd NetFaultLab
```

프로그램을 실행합니다.

```bash
python3 main.py
```

프로그램을 실행하면 랜덤 네트워크 토폴로지를 생성하고, Containerlab 환경을 배포한 뒤 랜덤 장애를 주입하여 트러블슈팅 과정을 시작합니다.

## Seed 기능

NetFaultLab은 동일한 시나리오를 다시 생성할 수 있도록 Seed 기능을 지원합니다.

예시:

```text
Seed (Enter = Random): 12345
```

같은 Seed 값을 입력하면 테스트와 디버깅 과정에서 동일한 랜덤 시나리오를 다시 생성하기 쉽습니다.

Enter만 입력하면 랜덤 Seed를 사용합니다.

## 복구 검증

장애를 주입하기 전에 정상 네트워크 상태를 저장합니다.

사용자가 복구 작업을 수행한 뒤 현재 상태와 초기 정상 상태를 비교합니다.

복구 성공:

```text
=== Verification ===
Network Recovery Verified
```

복구 실패:

```text
=== Verification ===
Recovery Verification Failed
```

Containerlab 기반 장애 시나리오에서는 실제 Ping 테스트를 이용한 통신 검증도 함께 수행합니다.

## 현재 구현 상태

NetFaultLab은 Python 내부에서만 동작하던 네트워크 장애 시뮬레이터에서 Containerlab 기반 실제 트러블슈팅 랩으로 확장되었습니다.

현재 구현된 기능:

- 동적 네트워크 토폴로지 생성
- Containerlab 토폴로지 자동 생성
- Containerlab 자동 배포
- Linux 컨테이너 네트워크 설정
- 인터페이스 자동 매핑
- 실제 Interface Down 장애 및 복구
- 실제 IP 주소 장애 및 복구
- 실제 Default Gateway 장애 및 복구
- 실제 Static Route 장애 및 복구
- 실제 ACL 기반 트래픽 차단 및 복구
- Ping 기반 장애 확인
- Ping 기반 복구 확인
- Python 내부 상태 복구 검증

## 현재 한계

현재 버전은 네트워크 장비를 단순화된 Linux 컨테이너로 구성하고 있습니다.

Switch라는 이름을 가진 노드 역시 현재는 일반 Linux 컨테이너이며, 실제 Layer 2 Ethernet Switch와 동일한 동작을 하도록 구현되어 있지는 않습니다.

또한 일부 테스트 IP 주소는 링크 상태와 장애 여부를 확인하기 위한 검증용 주소로 별도로 사용하고 있습니다.

현재 Python에서 생성하는 논리적인 네트워크 설정과 실제 Containerlab 네트워크 환경을 점진적으로 하나의 실제 네트워크 구조로 통합하는 단계입니다.

## 향후 개선 계획

- 실제 Layer 2 Switching 구조 구현
- Linux Bridge 구성
- VLAN 동작 현실화
- 생성된 클라이언트 IP를 실제 Containerlab 네트워크에 직접 적용
- 생성된 서버 네트워크를 실제 Containerlab 환경에 직접 적용
- Static Routing 시나리오 확장
- 추가 장애 유형 구현
- 로그 및 트러블슈팅 리포트 개선
- 난이도 기능 추가
- 자동 복구 검증 기능 개선
- NetworkMonitor와 연동
- NetworkMonitor가 NetFaultLab에서 생성한 장비를 자동으로 모니터링하도록 구현

## NetworkMonitor 연동 계획

NetFaultLab은 별도의 NetworkMonitor 프로젝트와 연동하는 방향으로 개발하고 있습니다.

```text
NetFaultLab
    |
    | 네트워크 배포 / 장애 주입
    v
Containerlab Network
    |
    | 장비 상태 / Ping
    v
NetworkMonitor
    |
    | WARNING / DOWN 감지
    v
사용자 트러블슈팅
    |
    | 네트워크 복구
    v
NetworkMonitor
    |
    | RECOVERED 감지
    v
복구 확인
```

NetFaultLab은 장애가 포함된 네트워크 시나리오를 생성하고, NetworkMonitor는 해당 네트워크의 장애와 복구 상태를 감지하고 기록하는 구조를 목표로 합니다.

## 프로젝트 목적

NetFaultLab의 목적은 다음과 같은 기술을 직접 실습하고 익히는 것입니다.

- 네트워크 트러블슈팅
- IP 주소 설정
- Default Gateway
- Static Routing
- ACL
- Linux Networking
- Docker
- Containerlab
- 장애 원인 분석
- 네트워크 복구 검증

실제 장애를 직접 발생시키고 복구하는 과정을 반복하면서 네트워크 운영 및 트러블슈팅 경험을 쌓기 위한 포트폴리오 프로젝트입니다.
