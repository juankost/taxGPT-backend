from setuptools import setup, find_packages

# Read requirements.txt and use it for the install_requires option
with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="taxgpt-backend",
    version="0.1",
    packages=find_packages(),
    install_requires=requirements,
    # Additional metadata and dependencies
)
