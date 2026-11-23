"""Loyiha ichidagi haqiqiy git klonlash menejeri testlari."""

import os
import subprocess
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import clone_manager  # noqa: E402


def _git(cwd, *args):
    subprocess.run(
        ["git", *args], cwd=str(cwd), check=True, capture_output=True, text=True, timeout=30
    )


def _make_source_repo(tmp_path):
    src = tmp_path / "source"
    src.mkdir()
    _git(src, "init", "-q")
    _git(src, "config", "user.email", "test@local")
    _git(src, "config", "user.name", "Test")
    (src / "README.md").write_text("test\n", encoding="utf-8")
    _git(src, "add", "README.md")
    _git(src, "commit", "-qm", "init")
    return src


def test_validate_clone_url_only_https():
    assert clone_manager.validate_clone_url("https://github.com/morluto/rea.git").endswith(".git")
    for bad in ("http://github.com/x.git", "javascript:alert(1)", "git@github.com:x/y.git"):
        try:
            clone_manager.validate_clone_url(bad)
            assert False, bad
        except clone_manager.CloneError:
            pass


def test_clone_refresh_and_delete_real_git_repo(tmp_path, monkeypatch):
    monkeypatch.setattr(clone_manager, "CLONES_ROOT", tmp_path / "clones")
    monkeypatch.setattr(clone_manager, "REGISTRY_FILE", tmp_path / "clones" / "registry.json")
    # Mahalliy test manbasini ishlatamiz; URL tekshiruvi alohida test qilingan.
    monkeypatch.setattr(clone_manager, "validate_clone_url", lambda url: url)

    src = _make_source_repo(tmp_path)
    head1 = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=str(src), check=True, capture_output=True, text=True
    ).stdout.strip()

    result = clone_manager.clone_repository(str(src), name="local")
    assert result["status"] == "ready"
    assert result["head"] == head1
    assert (tmp_path / "clones" / "local" / "README.md").exists()
    assert clone_manager.get_clone("local")["head"] == head1

    (src / "README.md").write_text("changed\n", encoding="utf-8")
    _git(src, "add", "README.md")
    _git(src, "commit", "-qm", "change")
    head2 = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=str(src), check=True, capture_output=True, text=True
    ).stdout.strip()
    refreshed = clone_manager.refresh_clone("local")
    assert refreshed["head"] == head2 != head1

    clone_manager.delete_clone("local")
    assert not (tmp_path / "clones" / "local").exists()
    try:
        clone_manager.get_clone("local")
        assert False, "deleted clone should not be found"
    except clone_manager.CloneError:
        pass


def test_name_traversal_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(clone_manager, "CLONES_ROOT", tmp_path / "clones")
    monkeypatch.setattr(clone_manager, "REGISTRY_FILE", tmp_path / "clones" / "registry.json")
    src = _make_source_repo(tmp_path)
    monkeypatch.setattr(clone_manager, "validate_clone_url", lambda url: url)
    try:
        clone_manager.clone_repository(str(src), name="../evil")
        assert False, "traversal should be rejected"
    except clone_manager.CloneError:
        pass
