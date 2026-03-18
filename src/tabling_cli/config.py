from pydantic_settings import BaseSettings


class TablingConfig(BaseSettings):
    model_config = {"env_prefix": "TABLING_"}

    api_base_url: str = "https://mobile-v2-api.tabling.co.kr"
    auth_token: str = ""  # 공개 조회는 토큰 불필요. waitlist 등 인증 필요 시 사용
