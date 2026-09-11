"""예제 전체가 공유하는 모델 설정. 모든 예제는 여기서만 채팅 모델과 임베딩 모델을 만든다."""
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

# ANCHOR: embeddings
def get_embeddings(**overrides):
    load_dotenv(ENV_PATH, override=False)  # EMBEDDING_* 값도 .env에서 읽는다
    # 진행 표시줄·로그가 출력에 섞이지 않도록 라이브러리를 import하기 "전에" 설정한다
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")  # 함께 쓰는 Chroma의 익명 통계 전송 끄기

    # 무거운 라이브러리(torch 등)는 임베딩이 필요할 때만 불러온다 — 1·2부 예제는 영향 없음
    import torch
    from langchain_huggingface import HuggingFaceEmbeddings

    model_name = os.environ.get("EMBEDDING_MODEL", "").strip() or "BAAI/bge-m3"
    device = os.environ.get("EMBEDDING_DEVICE", "").strip()
    if not device:  # 비워 두면 mps를 쓸 수 있으면 mps, 아니면 cpu
        device = "mps" if torch.backends.mps.is_available() else "cpu"

    params = dict(
        model_name=model_name,
        model_kwargs={"device": device},
        encode_kwargs={"normalize_embeddings": True},  # 길이 1로 정규화 → 내적 = 코사인 유사도
    )
    params.update(overrides)
    return HuggingFaceEmbeddings(**params)
# ANCHOR_END: embeddings
