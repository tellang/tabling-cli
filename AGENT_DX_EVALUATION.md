# Agent DX 8대 원칙 평가 보고서

> 평가 기준: 80점 만점 (각 원칙 10점)
> 평가일: 2026-04-11
> 대상: tabling-cli v0.1.0

---

## 총점: 64/80 (80.0%)

| # | 원칙 | 개선 전 | 개선 후 | 판정 |
|---|------|---------|---------|------|
| 1 | JSON-First Output | 8 | 8 | PASS |
| 2 | Raw Payload Passthrough | 6 | **8** | PASS (개선) |
| 3 | Schema Introspection | 8 | 8 | PASS |
| 4 | Input Hardening | 9 | 9 | PASS |
| 5 | Context Window Discipline | 7 | 7 | PASS |
| 6 | Safety Rails | 8 | 8 | PASS |
| 7 | Skill Files | 2 | **8** | PASS (개선) |
| 8 | Smart Search | 4 | **8** | PASS (개선) |
| | **합계** | **52** | **64** | |

---

## 원칙별 상세 평가

### 1. JSON-First Output — 8/10

**근거:**
- `--format json|table|compact` 지원, 기본값 json (+3)
- stdout/stderr 완전 분리: JSON→stdout, Rich→stderr (+3)
- `print_json()` 유틸리티로 일관된 출력 (+1)
- compact 모드로 토큰 절약 가능 (+1)

**감점 사유:**
- 에러 응답이 구조화된 JSON이 아닌 텍스트 (-1): `err_console.print(f"[red]API 오류: {exc}[/red]")`
- NDJSON(스트리밍) 미지원 (-1)

---

### 2. Raw Payload Passthrough — 8/10 (개선 전 6점)

**근거:**
- `--json-body`로 전체 요청 본문 오버라이드 (+3)
- `--params`로 쿼리 파라미터 오버라이드 (+3)
- 모든 커맨드에서 일관되게 지원 (+2)

**개선 내용:**
- **[수정]** `--params`가 dry-run에서만 사용되고 실제 API 호출 시 무시되던 버그 수정
- shop.py, brands.py, curations.py, search.py 4개 파일에서 `parsed_params`를 `client._request()`에 전달하도록 수정

**감점 사유:**
- `--headers` 오버라이드 미지원 (-1)
- POST 커맨드에서 `--params`와 `--json-body` 동시 사용 시 동작 문서화 부족 (-1)

---

### 3. Schema Introspection — 8/10

**근거:**
- `tabling schema show <command>` — 개별 스키마 조회 (+3)
- `tabling schema list` — 전체 커맨드 목록 (+2)
- Pydantic `model_json_schema()` 기반 응답 모델 스키마 자동생성 (+2)
- 파라미터별 type, description, required, default, enum, min/max 명세 (+1)

**감점 사유:**
- 스키마에 버전 정보 미포함 (-1)
- OpenAPI/JSON Schema $ref 표준과 완전히 호환되지 않음 (-1)

---

### 4. Input Hardening — 9/10

**근거:**
- ASCII 제어문자 거부 (0x00-0x1F, 0x7F) (+2)
- 위험 유니코드 16종 거부 (제로폭 공백, 방향 오버라이드 등) (+2)
- 이중 URL 인코딩 방지 (+1)
- NFC 정규화 자동 적용 (+1)
- 식별자 전용 경로 순회 방어 (`../`, `..\\`, `%2e%2e`) (+2)
- 모든 커맨드에서 일관되게 적용 (+1)

**감점 사유:**
- 길이 제한 미적용 (매우 긴 입력에 대한 방어 없음) (-1)

---

### 5. Context Window Discipline — 7/10

**근거:**
- `--fields` 필드 선택으로 응답 축소 (+3)
- `--page`, `--page-size` 페이지네이션 (+2)
- compact 모드로 최소 출력 (+1)
- `--limit` (curations restaurants) (+1)

**감점 사유:**
- search 결과에 `--limit` 미지원 (-1)
- 응답 크기 추정/경고 없음 (-1)
- 중첩 필드 선택 미지원 (예: `reviews.contents`) (-1)

---

### 6. Safety Rails — 8/10

**근거:**
- `--dry-run` 모든 커맨드에서 지원 (+3)
- 민감정보 재귀적 마스킹 (config.py: auth_token, password 등) (+2)
- 변경 작업(waitlist register/cancel)에 경고 메시지 (+1)
- 명확한 exit code (0/1/2) (+1)
- HTTP 헤더 마스킹 (+1)

**감점 사유:**
- 변경 작업에 `--confirm` 명시적 확인 플래그 없음 (-1)
- rate limiting 없음 (-1)

---

### 7. Skill Files — 8/10 (개선 전 2점)

**근거 (개선 후):**
- **[신규]** SKILL.md 생성: 에이전트용 전체 사용 가이드 (+4)
  - 커맨드별 설명 및 예제
  - 공통 플래그 테이블
  - 에이전트 사용 패턴 5가지
  - Exit code 및 출력 규칙 설명
- README.md에 Agent DX 기능 테이블 (+2)
- 환경 변수 문서화 (+1)
- 보안 참고 사항 포함 (+1)

**감점 사유:**
- CLAUDE.md (Claude Code 전용 가이드) 미생성 (-1)
- SKILL.md에 에러 핸들링 시나리오 미포함 (-1)

---

### 8. Smart Search — 8/10 (개선 전 4점)

**근거 (개선 후):**
- **[신규]** `tabling schema all` — 전체 스키마 단일 호출 덤프 (+3)
- **[신규]** 모든 스키마에 `examples` 필드 추가 (+2)
- 기본 키워드 검색 + 지역 프리셋 5종 (+1)
- Haversine 반경 필터링 (+1)
- `tabling schema list`로 기능 목록 자동 발견 (+1)

**감점 사유:**
- 엔티티 간 통합 검색 미지원 (매장+큐레이션+브랜드) (-1)
- 퍼지 매칭/자동 교정 미지원 (-1)

---

## 개선 구현 요약

### 수정된 파일

| 파일 | 변경 내용 |
|------|-----------|
| `src/tabling_cli/commands/shop.py` | `--params`를 실제 API 호출에 전달 |
| `src/tabling_cli/commands/brands.py` | `--params`를 실제 API 호출에 전달 |
| `src/tabling_cli/commands/curations.py` | `--params`를 실제 API 호출에 전달 |
| `src/tabling_cli/commands/search.py` | `--params`를 실제 API 호출에 전달 |
| `src/tabling_cli/schema.py` | `schema all` 커맨드 추가, 모든 스키마에 `examples` 필드 추가 |
| `SKILL.md` | 신규 생성 — 에이전트 사용 가이드 |
| `AGENT_DX_EVALUATION.md` | 신규 생성 — 본 문서 |

### 향후 개선 권고

| 우선순위 | 항목 | 영향 원칙 |
|----------|------|-----------|
| P1 | 에러 응답을 구조화된 JSON으로 (stderr + exit code) | 1, 6 |
| P1 | CLAUDE.md 생성 (Claude Code 전용) | 7 |
| P2 | 입력 길이 제한 추가 | 4 |
| P2 | 엔티티 간 통합 검색 커맨드 | 8 |
| P3 | NDJSON 스트리밍 출력 | 1 |
| P3 | `--confirm` 플래그 (변경 작업) | 6 |
| P3 | 중첩 필드 선택 (dot notation) | 5 |
