"""Setup script for depwatch."""

from setuptools import setup, find_packages

setup(
    name="depwatch",
    version="0.1.0",
    description="Lightweight daemon that monitors dependency files and sends alerts "
                "when outdated or vulnerable packages are detected.",
    author="depwatch contributors",
    python_requires=">=3.9",
    packages=find_packages(exclude=["tests*"]),
    install_requires=[
        "requests>=2.28",
        "packaging>=23.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov",
        ]
    },
    entry_points={
        "console_scripts": [
            "depwatch=depwatch.cli:main",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries",
        "Topic :: System :: Monitoring",
    ],
    package_data={
        "depwatch": ["config_example.json"],
    },
)
