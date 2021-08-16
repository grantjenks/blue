import asyncio
import pathlib
import subprocess

import black
import blue
import pytest

tests_dir = pathlib.Path(__file__).parent.absolute()


@pytest.mark.parametrize(
    'test_dir',
    [
        'config_setup',
        'config_tox',
        'config_blue',
        'config_pyproject',
        'good_cases',
    ],
)
def test_good_dirs(monkeypatch, test_dir):
    test_dir = tests_dir / test_dir
    monkeypatch.chdir(test_dir)
    monkeypatch.setattr('sys.argv', ['blue', '--check', '.'])
    for path in test_dir.rglob('*'):
        path.touch()  # Invalidate file caches in Blue.
    black.find_project_root.cache_clear()
    with pytest.raises(SystemExit) as exc_info:
        asyncio.set_event_loop(asyncio.new_event_loop())
        blue.main()
    assert exc_info.value.code == 0


@pytest.mark.parametrize(
    'test_dir',
    ['bad_cases'],
)
def test_bad_dirs(monkeypatch, test_dir):
    test_dir = tests_dir / test_dir
    monkeypatch.chdir(test_dir)
    monkeypatch.setattr('sys.argv', ['blue', '--check', '.'])
    for path in test_dir.rglob('*'):
        path.touch()  # Invalidate file caches in Blue.
    black.find_project_root.cache_clear()
    with pytest.raises(SystemExit) as exc_info:
        asyncio.set_event_loop(asyncio.new_event_loop())
        blue.main()
    assert exc_info.value.code == 1


def test_main(capsys, monkeypatch):
    monkeypatch.setattr('sys.argv', ['blue', '--version'])
    with pytest.raises(SystemExit) as exc_info:
        import blue.__main__
    assert exc_info.value.code == 0


def test_version(capsys, monkeypatch):
    monkeypatch.setattr('sys.argv', ['blue', '--version'])
    with pytest.raises(SystemExit) as exc_info:
        blue.main()
    assert exc_info.value.code == 0
    out, err = capsys.readouterr()
    version = f'blue, version {blue.__version__}, based on black {black.__version__}\n'
    assert out.endswith(version)
    assert err == ''
