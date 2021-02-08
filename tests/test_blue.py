import pathlib
import subprocess

import blue
import pytest

tests_dir = pathlib.Path(__file__).parent.absolute()


def test_version():
    assert blue.__version__


@pytest.mark.parametrize(
    'config_dir',
    ['config_setup', 'config_tox', 'config_blue', 'config_pyproject'],
)
def test_configs(monkeypatch, config_dir):
    config_dir = tests_dir / config_dir
    monkeypatch.chdir(config_dir)
    proc = subprocess.run(f'blue --check .', shell=True)
    assert proc.returncode == 0
