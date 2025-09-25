from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="openai-billing-monitor",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A Python library for monitoring and controlling OpenAI API costs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lemonhall/openai-billing-monitor",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "openai>=1.0.0",
        "pydantic>=2.0.0",
        "pyyaml>=6.0",
        "tiktoken>=0.4.0",
    ],
    extras_require={
        "gui": ["tkinter"],
        "dev": ["pytest", "black", "flake8", "mypy"],
    },
    entry_points={
        "console_scripts": [
            "openai-billing-gui=openai_billing.gui.main:main",
        ],
    },
)
