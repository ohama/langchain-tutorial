"""check_leaks.py --exclude 단위 테스트. 실제 키는 절대 사용하지 않고 가짜 값만 사용한다."""
import check_leaks


def test_finding_reported_without_exclude(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("LLM_API_KEY", "SUPERSECRET_TEST_VALUE_12345")
    (tmp_path / "vendor.min.js").write_text("SUPERSECRET_TEST_VALUE_12345", encoding="utf-8")

    rc = check_leaks.main([str(tmp_path)])

    out = capsys.readouterr().out
    assert rc == 1
    assert "CLEAN" not in out


def test_excluded_file_is_skipped(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("LLM_API_KEY", "SUPERSECRET_TEST_VALUE_12345")
    (tmp_path / "vendor.min.js").write_text("SUPERSECRET_TEST_VALUE_12345", encoding="utf-8")

    rc = check_leaks.main([str(tmp_path), "--exclude", "*vendor.min.js"])

    out = capsys.readouterr().out
    assert rc == 0
    assert "CLEAN" in out


def test_exclude_does_not_hide_other_files(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("LLM_API_KEY", "SUPERSECRET_TEST_VALUE_12345")
    (tmp_path / "vendor.min.js").write_text("SUPERSECRET_TEST_VALUE_12345", encoding="utf-8")
    (tmp_path / "chapter.md").write_text("SUPERSECRET_TEST_VALUE_12345", encoding="utf-8")

    rc = check_leaks.main([str(tmp_path), "--exclude", "*vendor.min.js"])

    out = capsys.readouterr().out
    assert rc == 1
    assert "chapter.md" in out
    assert "vendor.min.js" not in out
