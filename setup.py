"""
FortiManager API client setup script.
"""

from setuptools import setup, find_packages

setup(
    name="fmg-batch",
    version="0.1.0",
    description="FortiManager API client",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "requests>=2.25.0",
        "python-dotenv>=0.15.0",
        "tqdm>=4.50.0",
    ],
    entry_points={
        "console_scripts": [
            "fmg-batch=fortimanager.cli.commands:main",
        ],
    },
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
