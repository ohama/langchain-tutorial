"""예제 전체가 공유하는 LLM 설정. 모든 예제는 여기서만 채팅 모델을 만든다."""
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

EXAMPLES_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = EXAMPLES_DIR / ".env"

# ANCHOR: settings
@dataclass(frozen=True)
class Settings:
    base_url: str
    model: str
    api_key: str | None = field(default=None, repr=False)  # repr에 키가 찍히지 않게

def load_settings() -> Settings:
    load_dotenv(ENV_PATH, override=False)  # 이미 설정된 환경변수가 우선
    base_url = os.environ.get("LLM_BASE_URL", "").strip()
    model = os.environ.get("LLM_MODEL", "").strip()
    if not base_url or not model:
        raise RuntimeError(
            "LLM_BASE_URL / LLM_MODEL이 설정되지 않았습니다. "
            "examples/.env.example을 examples/.env로 복사한 뒤 값을 채우세요."
        )
    return Settings(base_url=base_url, model=model,
                    api_key=os.environ.get("LLM_API_KEY", "").strip() or None)
# ANCHOR_END: settings

# ANCHOR: chat_model
def get_chat_model(**overrides) -> ChatOpenAI:
    s = load_settings()
    params = dict(
        base_url=s.base_url,
        model=s.model,
        api_key=s.api_key or "not-needed",  # 인증 없는 로컬 서버는 아무 값이나 허용
        temperature=0,     # 캡처 재현성을 위해 기본 0
        timeout=120,       # 콜드 스타트(첫 요청 수십 초) 대비
        max_retries=1,
    )
    params.update(overrides)
    return ChatOpenAI(**params)
# ANCHOR_END: chat_model

# ANCHOR: structured
def get_structured_model(schema, **overrides):
    # 로컬 서버는 기본 방식(스키마 강제 디코딩)에서 500 에러 → function_calling + strict=False로 통일
    return get_chat_model(**overrides).with_structured_output(
        schema, method="function_calling", strict=False
    )
# ANCHOR_END: structured
