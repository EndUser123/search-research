from setuptools import find_packages, setup

setup(
    name="log_chunker",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pydantic>=2.0",
        "sentence-transformers>=2.2.0",
        "numpy>=1.24.0",
        "scikit-learn>=1.3.0",
        "hdbscan>=0.8.33",
        "tqdm>=4.65.0",
        "rich>=13.4.2",
        "python-dateutil>=2.8.2",
        "transformers>=4.30.0",
        "torch>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=23.3.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "log-chunker=log_chunker.cli:main",
        ]
    },
)
