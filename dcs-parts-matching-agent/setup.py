"""Setup script for DCS Parts Matching Agent."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = requirements_file.read_text().strip().split('\n')
    requirements = [r.strip() for r in requirements if r.strip() and not r.startswith('#')]

setup(
    name="dcs-parts-matching-agent",
    version="1.0.0",
    description="AI-powered DCS parts matching system for industrial automation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Company",
    author_email="support@yourcompany.com",
    url="https://github.com/yourcompany/dcs-parts-matching-agent",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.4",
            "pytest-asyncio>=0.23.3",
            "pytest-cov>=4.1.0",
            "black>=24.1.1",
            "flake8>=7.0.0",
            "mypy>=1.8.0",
        ],
        "aws": [
            "boto3>=1.34.34",
        ],
        "azure": [
            "azure-ai-formrecognizer>=3.3.2",
        ],
    },
    entry_points={
        "console_scripts": [
            "dcs-parts-agent=api.main:start_server",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Manufacturing",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="dcs parts matching ai vision nlp industrial-automation",
    project_urls={
        "Bug Reports": "https://github.com/yourcompany/dcs-parts-matching-agent/issues",
        "Source": "https://github.com/yourcompany/dcs-parts-matching-agent",
        "Documentation": "https://github.com/yourcompany/dcs-parts-matching-agent/wiki",
    },
)
