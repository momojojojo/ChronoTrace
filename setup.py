from setuptools import setup, find_packages

setup(
    name="chronotrace",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        line.strip() 
        for line in open('requirements.txt').readlines()
        if line.strip() and not line.startswith('#')
    ],
    author="Jolie Yeo",
    author_email="2301178@singaporetech.edu.sg",
    description="ChronoTrace: Temporal Caption Evolution Detection and Provenance Reconstruction Using Parameter-Efficient Multimodal Learning",
    python_requires='>=3.8',
)