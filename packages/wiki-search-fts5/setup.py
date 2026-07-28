from setuptools import setup

setup(
    name="wiki-search-qmd-compat",
    version="1.0.0",
    description="FTS5 wiki search — qmd-compatible CLI entry point",
    py_modules=["qmd_entry"],
    entry_points={
        "console_scripts": [
            "qmd = qmd_entry:main",
        ],
    },
    python_requires=">=3.9",
)
