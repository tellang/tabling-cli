# Tabling CLI (테이블링 비공식 CLI)

[![PyPI version](https://img.shields.io/pypi/v/tabling-cli?color=blue)](https://pypi.org/project/tabling-cli/)
[![Python Version](https://img.shields.io/pypi/pyversions/tabling-cli)](https://pypi.org/project/tabling-cli/)
[![Agent DX](https://img.shields.io/badge/Agent%20DX-70%2F70-success)](https://github.com/topics/agent-dx)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Tabling CLI**는 대한민국 1등 맛집 대기 플랫폼 '테이블링'의 비공식 명령줄 도구입니다. AI 에이전트가 자동화를 수행하거나 파워 유저가 터미널에서 빠르게 대기열을 관리할 수 있도록 **Agent DX(Developer Experience) 7대 원칙**을 준수하여 설계되었습니다.

> [!IMPORTANT]
> 이 도구는 비공식 구현체이며, 서비스 제공업체의 정책에 따라 사용에 제한이 있을 수 있습니다.

---

## 설치 방법

Python 3.11 이상 환경에서 `pip`를 통해 설치할 수 있습니다.

```bash
pip install tabling-cli
```

또는 소스에서:

```bash
git clone https://github.com/tellang/tabling-cli.git
cd tabling-cli
pip install -e .
```

---

## 빠른 시작 (Quick Start)

### 1. 매장 검색 및 정보 조회

```bash
# 기본 검색 (JSON 출력)
tabling search "성수동 맛집"

# 지역 및 키워드 조합 검색
tabling search "스시" --location "강남" --format table

# 매장 상세 정보 조회
tabling shop info <SHOP_ID>

# 매장 리뷰 조회
tabling shop reviews <SHOP_ID>
```

### 2. 대기열(Waitlist) 관리

```bash
# 원격 줄서기 등록
tabling waitlist register <SHOP_ID> --party-size 2

# 대기 상태 확인
tabling waitlist status <WAITLIST_ID>

# 줄서기 취소
tabling waitlist cancel <WAITLIST_ID>
```

### 3. 큐레이션 및 브랜드

```bash
# 테이블링 추천 큐레이션 목록
tabling curations

# 브랜드 목록
tabling brands

# 특정 브랜드 소속 매장 조회
tabling brands shops <BRAND_ID>
```

---

## Agent DX 기능 (Agent-First Design)

본 CLI는 LLM 에이전트가 도구로 사용하기에 최적화된 인터페이스를 제공합니다.

| 원칙 | 명령어/플래그 | 설명 |
| :--- | :--- | :--- |
| **JSON-First Output** | `--format json\|table\|compact\|ndjson` | 기본값은 `json`. 에이전트 파싱에 최적화 |
| **Raw Payload Passthrough** | `--json-body`, `--params` | upstream API 요청을 그대로 전달 |
| **Runtime Schema Introspection** | `tabling schema` | 전체 명령어와 인자 구조를 JSON 스키마로 출력 |
| **Input Hardening** | 자동 적용 | 제어문자/유니코드/이중인코딩 방어 |
| **Context Discipline** | `--fields`, `--page`, `--page-size` | 필요한 데이터만 선택하여 토큰 절약 |
| **Safety Rails** | `--dry-run` | 실제 API 호출 없이 요청 계획만 반환. 민감정보 마스킹 |
| **Skill Files** | `SKILL.md` | 에이전트가 CLI 사용법을 자동 학습 |

---

## 에이전트 사용 패턴 (Workflow)

### 파이프라인 및 jq 조합

JSON 출력을 기본으로 하므로 `jq`와 조합하여 강력한 자동화 스크립트를 작성할 수 있습니다.

```bash
# 대기 팀이 5팀 미만인 매장만 필터링하여 이름 출력
tabling search "카페" --fields shopId,shopName,waitingCount | \
  jq '.[] | select(.waitingCount < 5) | .shopName'

# dry-run으로 요청 미리보기 후 실행
tabling waitlist register SHOP_ID --party-size 2 --dry-run
```

### 필드 선택으로 토큰 절약

```bash
# 이름과 대기 수만 가져오기
tabling search "홍대 맛집" --fields shopName,waitingCount --format compact
```

---

## 환경 변수 (Configuration)

설정 파일 없이 환경 변수만으로 동작을 제어할 수 있습니다.

| 변수명 | 설명 | 비고 |
| :--- | :--- | :--- |
| `TABLING_AUTH_TOKEN` | 테이블링 사용자 인증 토큰 | **필수** |
| `TABLING_API_BASE_URL` | 기본 API 엔드포인트 주소 | 기본값: `https://tabling.co.kr/api` |
| `TABLING_LOG_LEVEL` | 로그 레벨 (`DEBUG`, `INFO`, `ERROR`) | 기본값: `ERROR` |

---

## Exit Codes

에이전트가 실행 결과를 명확히 판단할 수 있도록 표준화된 종료 코드를 사용합니다.

| 코드 | 의미 | 설명 |
| :---: | :--- | :--- |
| **0** | 성공 | 정상 완료 |
| **1** | 일반 오류 | 내부 오류 또는 네트워크 실패 |
| **2** | 입력 오류 | 인자 유효성 검사 실패 |

---

## License

이 프로젝트는 [MIT License](LICENSE)에 따라 배포됩니다.

---

## 조각 사유 (Purpose & Motivation)

본 프로젝트는 테이블링(Tabling)의 공식 API 또는 SDK가 부재한 환경에서, **AI 에이전트 친화적 CLI 설계(Agent DX) 연구** 및 개인 생산성 향상을 목적으로 개발되었습니다.

- 공식 API/SDK 부재로 인한 CLI 기반 자동화 수요 충족
- Agent DX(Developer Experience for Agents) 7대 원칙 검증을 위한 실험적 구현체
- 개인 학습 및 연구 목적의 비상업적 프로젝트

## 면책사항 (Disclaimer & Legal Notice)

> **이 프로젝트를 사용하기 전에 반드시 아래 내용을 숙지하십시오.**

### 비공식 도구

본 프로젝트는 **테이블링(Tabling) 및 주식회사 테이블매니저와 어떠한 제휴, 후원, 보증, 공식적 관계도 없는 독립적인 비공식 도구**입니다. "테이블링", "Tabling" 및 관련 상표는 주식회사 테이블매니저의 자산이며, 본 프로젝트에서의 사용은 식별 목적에 한합니다.

### 이용약관 준수 책임

본 도구의 사용은 **전적으로 사용자의 책임**입니다. 사용자는 테이블링 서비스 이용약관(Terms of Service)을 반드시 확인하고 준수해야 합니다. 본 도구의 사용이 서비스 이용약관에 위반될 수 있으며, 이로 인한 **계정 정지, IP 차단, 법적 조치 등 모든 결과에 대한 책임은 전적으로 사용자에게 있습니다.**

### 무보증 (AS-IS)

본 소프트웨어는 **"있는 그대로(AS-IS)" 제공**되며, 명시적이든 묵시적이든 어떠한 종류의 보증도 하지 않습니다. 여기에는 상품성, 특정 목적에의 적합성, 비침해에 대한 묵시적 보증이 포함되나 이에 한정되지 않습니다.

### 서비스 변경 및 중단

본 도구는 비공식 API 엔드포인트에 의존하므로, **테이블링의 API 변경, 보안 정책 강화, 서비스 구조 변경 등에 의해 언제든지 작동이 중단될 수 있습니다.** 이에 대한 지속적인 유지보수나 호환성을 보장하지 않습니다.

### 과도한 사용 금지

과도한 요청(rate limit 초과, 대량 크롤링, 자동화된 반복 요청 등)은 서비스 장애를 유발할 수 있습니다. **이로 인한 서비스 차단, 법적 책임, 제3자 피해에 대한 모든 책임은 사용자에게 있습니다.** 합리적인 사용 범위 내에서만 사용하십시오.

### 데이터 및 개인정보

본 도구를 통해 수집되는 데이터의 저장, 처리, 공유에 대한 책임은 전적으로 사용자에게 있습니다. 개인정보보호법 등 관련 법규를 준수해야 하며, 수집 데이터의 상업적 이용은 관련 법률 및 서비스 이용약관에 따라 제한될 수 있습니다.

### 손해배상 면책

본 프로젝트의 개발자는 본 도구의 사용 또는 사용 불가능으로 인해 발생하는 **직접적, 간접적, 부수적, 특별, 결과적 또는 징벌적 손해**에 대해 어떠한 경우에도 책임지지 않습니다. 이는 데이터 손실, 이익 손실, 사업 중단, 계정 정지, 서비스 차단 등을 포함하나 이에 한정되지 않습니다.

### 용도 제한

본 도구는 **개인적인 연구, 학습, 생산성 향상 목적**으로만 제작되었습니다. 상업적 목적의 대량 데이터 수집, 서비스 방해, 경쟁 서비스 구축, 또는 테이블링의 비즈니스에 손해를 끼치는 용도로 사용하는 것을 금합니다.
