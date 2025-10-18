from setuptools import setup, find_packages

setup(
    name="hackaging-processor",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "transformers==4.35.2",
        "torch==2.8.0",
        "pytorch-lightning==2.5.5",
        "nltk==3.8.1",
        "openai>=1.0.0",
        "scikit-learn>=1.3.0",
        "numpy>=1.24.0",
        "scipy>=1.11.0",
        "rich>=13.0.0",
    ],
    python_requires=">=3.8",
)

