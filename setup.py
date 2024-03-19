from setuptools import setup, find_packages

setup(
    name='jobsscraper',
    version='0.1.0',
    author="Mickael Grima",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "pydantic>=2.6,<3.0",
        "selenium>=4.18,<5.0",
        "beautifulsoup4>=4.12,<5.0",
        "aiohttp>=3.9,<4.0",
        "lxml>=5.1,<6.0",
    ],
    license='MIT',
    description="A module to scrap all jobs details from different sources into well-structured data models",
    long_description=open('README.md').read(),
)
