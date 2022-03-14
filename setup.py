import pathlib
import re

from setuptools import setup
from setuptools.command.test import test as TestCommand


class Tox(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import tox

        errno = tox.cmdline(self.test_args)
        exit(errno)


with open('README.rst') as reader:
    readme = reader.read()

blue_init = (pathlib.Path('blue') / '__init__.py').read_text()
match = re.search(r"^__version__ = '(.+)'$", blue_init, re.MULTILINE)
version = match.group(1)

setup(
    name='blue',
    version=version,
    description='Blue -- Some folks like black but I prefer blue.',
    long_description=readme,
    author='Grant Jenks',
    author_email='contact@grantjenks.com',
    url='https://blue.readthedocs.io/',
    license='Apache 2.0',
    packages=['blue'],
    tests_require=['tox'],
    cmdclass={'test': Tox},
    install_requires=['black==22.1.0', 'flake8>=3.8'],
    project_urls={
        'Documentation': 'https://blue.readthedocs.io/en/latest',
        'Source': 'https://github.com/grantjenks/blue.git',
        'Tracker': 'https://github.com/grantjenks/blue/issues',
    },
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
    entry_points={
        'console_scripts': [
            'blue=blue:main',
        ]
    },
)
