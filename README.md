# Tabling CLI

테이블링(Tabling) 비공식 CLI — AI 에이전트 친화적 설계 (Agent DX)

맛집 검색, 매장 정보 조회, 줄서기 등록/취소를 터미널에서 수행합니다.

## 설치

```bash
pip install tabling-cli
```

또는 소스에서:

```bash
git clone https://github.com/tellang/tabling-cli.git
cd tabling-cli
pip install -e .
```

Python 3.11 이상이 필요합니다.

## 사용법

```bash
# 매장 검색
tabling search "카페" --location "성수"

# JSON 출력 (에이전트 친화적)
tabling search "스시" --json

# 매장 상세 정보
tabling shop info SHOP_ID

# 줄서기 등록
tabling waitlist register SHOP_ID --party-size 4

# 줄서기 취소
tabling waitlist cancel WAITLIST_ID

# 대기 상태 확인
tabling status WAITLIST_ID

# 스키마 자체검사
tabling schema

# 버전
tabling version
```

## Agent DX 특징

- **스키마 자체검사**: `tabling schema`로 전체 커맨드 스키마 JSON 출력
- **입력 검증**: 잘못된 인자에 대해 구조화된 오류 반환
- **JSON-First 출력**: `--json` 플래그로 머신 파싱 가능한 출력
- **dry-run 지원**: 부작용 없이 요청 미리보기

## 환경 변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `TABLING_API_BASE_URL` | API 엔드포인트 | `https://tabling.co.kr/api` |
| `TABLING_AUTH_TOKEN` | 인증 토큰 | (필수) |

## 라이선스

MIT
