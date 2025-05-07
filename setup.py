from setuptools import setup, find_packages

# Use setuptools-scm to get version from git tags
setup(
    packages=find_packages(where="src"),
    package_dir={"": "src"},
)
