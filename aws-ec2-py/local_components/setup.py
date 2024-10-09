from setuptools import setup, find_packages
# List of requirements
requirements = []  # This could be retrieved from requirements.txt
# Package (minimal) configuration
setup(
    name="demo_components",
    version="0.0.1",
    description="component resources",
    py_modules=["network"],
    install_requires=requirements
)