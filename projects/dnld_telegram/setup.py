from setuptools import find_packages, setup

setup(
    name="dnld_telegram",
    version="0.1.0",
    description="Enhanced Telegram Media Downloader",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    entry_points={
        "console_scripts": [
            "dnld_telegram=dnld_telegram.__main__:main",
        ],
    },
    install_requires=[
        "rich>=13.0.0",
        "tqdm>=4.66.0",
        "loguru>=0.7.0",
        "telethon>=1.24.0",
        "python-dotenv>=0.19.0",
        "pydantic>=2.0",
        "toml>=0.10.2",
        "aiosqlitepool>=0.1.0",
    ],
)
