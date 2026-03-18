# Tabling CLI (tabling)

테이블링(Tabling) 서비스를 터미널에서 이용할 수 있는 비공식 CLI 도구입니다.
맛집 검색부터 줄서기 등록 및 상태 확인까지 지원합니다.

> **Note:** 현재 Placeholder API를 사용 중입니다. 실제 API 엔드포인트는 RE 후 교체 예정입니다.

## 주요 기능

- **매장 검색 (`search`)**: 지역 및 매장명 기반 맛집 검색
- **매장 상세 (`shop info`)**: 영업시간, 메뉴, 대기 현황 조회
- **줄서기 (`waitlist`)**: 원격 줄서기 등록 및 취소
- **상태 확인 (`status`)**: 현재 대기 순번 및 예상 시간 조회

## 설치

Python 3.11 이상이 필요합니다.

```bash
git clone https://github.com/tellang/tabling-cli.git
cd tabling-cli
pip install -e .
```

## 사용법

```bash
# 매장 검색
tabling search "카페" --location "성수"

# JSON 형식 출력
tabling search "스시" --json

# 매장 상세 정보
tabling shop info SHOP_ID

# 줄서기 등록
tabling waitlist register SHOP_ID --party-size 4

# 줄서기 취소
tabling waitlist cancel WAITLIST_ID

# 대기 상태 확인
tabling status WAITLIST_ID

# 버전 / 개요
tabling version
tabling overview
```

## 환경 변수

`.env` 파일을 프로젝트 루트에 생성하세요.

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `TABLING_API_BASE_URL` | API 엔드포인트 | `https://tabling.co.kr/api` |
| `TABLING_AUTH_TOKEN` | 인증 토큰 | (필수) |

## 프로젝트 구조

```
tabling-cli/
├── src/
│   └── tabling_cli/
│       ├── __init__.py
│       ├── __main__.py      # 패키지 진입점
│       ├── cli.py           # Typer 앱 진입점
│       ├── client.py        # HTTP API 클라이언트
│       ├── config.py        # 환경 변수 설정
│       ├── models.py        # 데이터 모델
│       └── commands/
│           ├── __init__.py
│           ├── search.py    # 검색 커맨드
│           ├── shop.py      # 매장 정보 커맨드
│           └── waitlist.py  # 줄서기 커맨드
├── pyproject.toml
└── README.md
```

## 라이선스

MIT
