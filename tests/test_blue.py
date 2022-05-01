import asyncio
import pathlib
import subprocess
import sys

import black
import blue
import pytest

from contextlib import ExitStack
from shutil import copy
from tempfile import TemporaryDirectory


tests_dir = pathlib.Path(__file__).parent.absolute()


@pytest.mark.parametrize(
    'test_dir',
    [
        ## 'config_setup',
        ## 'config_tox',
        ## 'config_blue',
        ## 'config_pyproject',
        'good_cases',
    ],
)
def test_good_dirs(monkeypatch, capsys, test_dir):
    src_dir = tests_dir / test_dir
    monkeypatch.setattr('sys.argv', ['blue', '--check', '.'])
    with TemporaryDirectory() as dst_dir:
        # warsaw(2022-05-01): we can't use shutil.copytree() here until we
        # drop Python 3.7 support because we need dirs_exist_ok and that was
        # added in Python 3.8
        for path in src_dir.rglob('*'):
            copy(src_dir / path, dst_dir)
        monkeypatch.chdir(dst_dir)
        black.find_project_root.cache_clear()
        with pytest.raises(SystemExit) as exc_info:
            asyncio.set_event_loop(asyncio.new_event_loop())
            blue.main()
        check_exit = exc_info.value.code
        if check_exit != 0:
            out, err = capsys.readouterr()
            sys.stdout.write(out)
            sys.stdout.write(err)
            # Try again, this time with --diff
            monkeypatch.setattr('sys.argv', ['blue', '--diff', '.'])
        with pytest.raises(SystemExit) as exc_info:
            asyncio.set_event_loop(asyncio.new_event_loop())
            blue.main()
        diff_exit = exc_info.value.code
        assert diff_exit == 0
        assert diff_exit == check_exit


@pytest.mark.parametrize(
    'test_dir',
    ['bad_cases'],
)
def test_bad_dirs(monkeypatch, capsys, test_dir):
    src_dir = tests_dir / test_dir
    monkeypatch.setattr('sys.argv', ['blue', '--check', '.'])
    with ExitStack() as resources:
        dst_dir = resources.enter_context(TemporaryDirectory())
        # warsaw(2022-05-01): we can't use shutil.copytree() here until we
        # drop Python 3.7 support because we need dirs_exist_ok and that was
        # added in Python 3.8
        for path in src_dir.rglob('*'):
            copy(src_dir / path, dst_dir)
        monkeypatch.chdir(dst_dir)
        black.find_project_root.cache_clear()
        exc_info = resources.enter_context(pytest.raises(SystemExit))
        asyncio.set_event_loop(asyncio.new_event_loop())
        blue.main()
        check_exit = exc_info.value.code
        if check_exit != 0:
            out, err = capsys.readouterr()
            sys.stdout.write(out)
            sys.stdout.write(err)
            # Try again, this time with --diff
            monkeypatch.setattr('sys.argv', ['blue', '--diff', '.'])
        with pytest.raises(SystemExit) as exc_info:
            asyncio.set_event_loop(asyncio.new_event_loop())
            blue.main()
        diff_exit = exc_info.value.code
        assert diff_exit == 1
        assert diff_exit == check_exit


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
