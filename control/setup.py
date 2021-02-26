import sys
from setuptools import setup, find_packages
import versioneer

install_requires = [
    'odin>=1.0.0',
    'pyzmq>=22.0',
    'msgpack>=1.0'
]

extras_require = {
    'test': [
        'pytest', 'pytest-cov', 'requests', 'tox'
    ]
}

if sys.version_info[0] == 2:
    extras_require['test'].append('mock')
else:
    extras_require['test'].append('pytest-asyncio')

setup(
    name="mercury",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description='MERCURY detector system control',
    url='https://github.com/stfc-aeg/mercury-detector',
    author='Tim Nicholls',
    author_email='tim.nicholls@stfc.ac.uk',
    packages=find_packages('src'),
    package_dir={'':'src'},
    install_requires=install_requires,
    extras_require=extras_require,
)