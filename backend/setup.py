# ABOUTME: Setup configuration for backend Python package
# ABOUTME: Defines package metadata and dependencies

from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="aws-computer-use-backend",
    version="0.1.0",
    description="Backend services for AWS Computer Use Demo",
    author="Maddy Ravipati",
    packages=find_packages(),
    install_requires=requirements,
    python_requires=">=3.12",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.12",
    ],
)