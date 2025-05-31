from setuptools import find_packages, setup

# Use setuptools-scm to get version from git tags
setup(
    packages=find_packages(where="src"),
    package_dir={"": "src"},
)
