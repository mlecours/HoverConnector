import pathlib

import pkg_resources
from setuptools import find_packages, setup
from datetime import datetime

with pathlib.Path('requirements.txt').open() as requirements_txt:
    install_requires = [
        str(requirement) for requirement in pkg_resources.parse_requirements(requirements_txt)
    ]

setup(
    name='hoverconnector',
    author='Maxime Lecours',
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    version=datetime.utcnow().strftime("%Y%m%d.%H%M"),
    description='Hover interaction library (hover.com private API)',
    install_requires=install_requires,
    license='MIT',
)
