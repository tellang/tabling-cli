# tabling-cli SKILL.md — AI 에이전트 사용 가이드

> 이 파일은 AI 에이전트(Claude, GPT, Codex 등)가 tabling-cli를 도구로 사용할 때 참조하는 매뉴얼입니다.

## 개요

tabling-cli는 대한민국 맛집 대기 플랫폼 '테이블링'의 비공식 CLI입니다.
매장 검색, 상세 조회, 대기열 관리, 큐레이션, 브랜드 탐색을 지원합니다.

## 설치

```bash
pip install tabling-cli
```

## 환경 변수

| 변수 | 필수 | 설명 |
|------|------|------|
| `TABLING_AUTH_TOKEN` | 대기열 등록/취소 시 | 사용자 인증 토큰 |
| `TABLING_API_BASE_URL` | 아니오 | 기본: `https://mobile-v2-api.tabling.co.kr` |

## 커맨드 목록

### tabling search [KEYWORD]
매장 검색. 키워드, 지역 프리셋, 좌표 기반 검색 지원.

```bash
# 기본 검색
tabling search "스시" --format json

# 지역 프리셋 + 반경 필터
tabling search "카페" --area pangyo --radius 2.0

# 좌표 직접 지정
tabling search --lat 37.394 --lng 127.111 --radius 1.5

# 필드 선택 (토큰 절약)
tabling search "맛집" --fields restaurantName,rating,waitingCount

# Raw payload 전달
tabling search --json-body '{"keyword":"스시","page":1,"pageSize":5}'
```

**지역 프리셋**: pangyo, seohyeon, jeongja, migeun, yatap

### tabling shop info SHOP_ID
매장 상세 정보 조회.

```bash
tabling shop info 12345
tabling shop info 12345 --fields name,rating,address,useRemoteWaiting
```

### tabling waitlist register SHOP_ID
대기열 등록 (모바일 앱 전용 - placeholder).

```bash
tabling waitlist register 12345 --party-size 4 --dry-run
```

### tabling waitlist cancel WAITLIST_ID
대기열 취소 (모바일 앱 전용 - placeholder).

### tabling waitlist info SHOP_ID
매장의 대기/원격대기 상태 조회.

```bash
tabling waitlist info 12345 --fields useWaiting,waitingCount,useRemoteWaiting
```

### tabling curations list
큐레이션 목록 조회.

```bash
tabling curations list --home    # 홈 큐레이션만
tabling curations list --all     # 전체
```

### tabling curations restaurants CURATION_ID
큐레이션 내 매장 목록.

```bash
tabling curations restaurants abc123 --limit 10
```

### tabling brands list
브랜드 목록 조회.

```bash
tabling brands list --page 1 --page-size 20
```

### tabling status WAITLIST_ID
대기 상태 빠른 확인.

### tabling schema show COMMAND
커맨드의 파라미터, 응답 모델, exit code를 JSON 스키마로 반환.

```bash
tabling schema show search
tabling schema show "shop info"
```

### tabling schema list
등록된 모든 커맨드 목록 반환.

### tabling schema all
모든 커맨드의 전체 스키마를 한 번에 JSON으로 반환.

## 공통 플래그

| 플래그 | 설명 |
|--------|------|
| `--format json\|table\|compact` | 출력 형식 (기본: json) |
| `--fields FIELD1,FIELD2,...` | 응답 필드 선택 (토큰 절약) |
| `--dry-run` | API 미호출, 요청 계획만 JSON 반환 |
| `--json-body JSON` | 전체 요청 본문 직접 전달 |
| `--params JSON` | 쿼리 파라미터 오버라이드 |

## 에이전트 사용 패턴

### 1. 스키마 먼저 확인
```bash
tabling schema list                    # 커맨드 목록
tabling schema show search             # search 커맨드 스키마
tabling schema all                     # 전체 스키마 한 번에
```

### 2. dry-run으로 안전하게 미리보기
```bash
tabling search "스시" --area pangyo --dry-run
```

### 3. JSON 파이프라인
```bash
tabling search "카페" --format compact | jq '.list[] | .restaurantName'
```

### 4. 필드 선택으로 컨텍스트 윈도우 절약
```bash
tabling search "맛집" --fields restaurantName,rating,waitingCount --format compact
```

### 5. Raw Payload로 API 직접 제어
```bash
tabling search --json-body '{"keyword":"","page":1,"pageSize":3}' --params '{"sort":"rating"}'
```

## Exit Codes

| 코드 | 의미 |
|------|------|
| 0 | 성공 |
| 1 | API 오류 / 입력 검증 실패 |
| 2 | 필수 인자 부재 (Typer 자동) |

## 출력 규칙

- `--format json` / `--format compact`: **stdout**에 JSON만 출력 (파이프 호환)
- `--format table`: **stderr**에 Rich 테이블 출력
- 에러 메시지: 항상 **stderr**
- 에이전트는 `--format json` (기본값) 사용 권장

## 보안 참고

- 입력은 자동으로 제어문자, 위험 유니코드, 경로 순회, 이중 인코딩 검사됨
- `--dry-run` 출력에서 민감정보(토큰 등)는 마스킹됨
- 대기열 등록/취소는 변경 작업으로 경고 표시
