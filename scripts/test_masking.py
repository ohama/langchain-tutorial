"""masking.py 단위 테스트. 실제 키는 절대 사용하지 않고 가짜 값만 사용한다."""
from masking import collect_secrets, find_leaks, mask_text


def test_short_secret_masked_everywhere():
    secret = "q7Zx2"
    text = f"key={secret} and again key={secret} here"
    masked = mask_text(text, [secret])
    assert secret not in masked
    assert masked.count("***MASKED_API_KEY***") == 2


def test_longest_first_ordering_prefix_secret():
    short = "abc"
    long = "abcdef"
    text = "value: abcdef"
    masked = mask_text(text, [short, long])
    # The longer secret must be masked as a whole, not leaving "def" dangling
    assert "abcdef" not in masked
    assert "def" not in masked
    assert masked.count("***MASKED_API_KEY***") == 1


def test_sk_token_masked():
    text = "token is sk-abcdefghijklmnop in the log"
    masked = mask_text(text, [])
    assert "sk-abcdefghijklmnop" not in masked
    assert "sk-***MASKED***" in masked


def test_bearer_token_masked():
    text = "Authorization: Bearer abcdefgh12345678"
    masked = mask_text(text, [])
    assert "abcdefgh12345678" not in masked
    assert "Bearer ***MASKED***" in masked


def test_home_path_masked_with_explicit_home():
    text = "/Users/alice/projs/x.py"
    masked = mask_text(text, [], home="/Users/alice")
    assert masked == "~/projs/x.py"


def test_generic_users_path_masked():
    text = "see /Users/bob/tmp for details"
    masked = mask_text(text, [])
    assert "/Users/bob" not in masked
    assert "~" in masked


def test_generic_home_path_masked():
    text = "see /home/carol/tmp for details"
    masked = mask_text(text, [])
    assert "/home/carol" not in masked
    assert "~" in masked


def test_korean_and_prose_unchanged():
    text = "스크럼 task-list 정리"
    masked = mask_text(text, [])
    assert masked == text


def test_find_leaks_nonempty_before_and_empty_after_masking_all_cases():
    secret = "q7Zx2"
    home = "/Users/alice"
    text = (
        f"key={secret}\n"
        "sk-abcdefghijklmnop\n"
        "Authorization: Bearer abcdefgh12345678\n"
        f"{home}/projs/x.py\n"
        "/Users/bob/tmp\n"
        "/home/carol/tmp\n"
    )
    leaks_before = find_leaks(text, [secret], home=home)
    assert leaks_before != []

    masked = mask_text(text, [secret], home=home)
    leaks_after = find_leaks(masked, [secret], home=home)
    assert leaks_after == []


def test_find_leaks_output_never_contains_secret():
    secret = "q7Zx2-real-value"
    text = f"leaked: {secret}"
    leaks = find_leaks(text, [secret])
    for kind in leaks:
        assert secret not in kind


def test_find_leaks_kinds_are_labels_only():
    text = "sk-abcdefghijklmnop"
    leaks = find_leaks(text, [])
    assert leaks == ["sk-token"]


def test_collect_secrets_reads_env_and_ignores_empty(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "fake-llm-key")
    monkeypatch.setenv("LITELLM_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "fake-openai-key")
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)

    secrets = collect_secrets()

    assert "fake-llm-key" in secrets
    assert "fake-openai-key" in secrets
    assert "" not in secrets


def test_collect_secrets_includes_extra_and_dedupes(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "shared-value")
    monkeypatch.delenv("LITELLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)

    secrets = collect_secrets(extra=["shared-value", "another-one", ""])

    assert secrets.count("shared-value") == 1
    assert "another-one" in secrets


def test_collect_secrets_sorted_longest_first(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "short")
    monkeypatch.delenv("LITELLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)

    secrets = collect_secrets(extra=["muchlongervalue"])

    assert secrets[0] == "muchlongervalue"


def test_masking_does_not_permanently_flag_mask_token_substring():
    # A secret that happens to look like part of the mask token itself
    # should not cause find_leaks to report a leak after masking.
    secret = "MASKED"
    text = f"value {secret} here"
    masked = mask_text(text, [secret])
    assert find_leaks(masked, [secret]) == []
