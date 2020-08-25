import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="servicemock",
    version="0.1.1",
    author="Mika Lackman",
    author_email="mika.lackman@gmail.com",
    description="Mock DSL for requests_mock",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mlackman/urban-lamp",
    packages=setuptools.find_packages(),
    install_requires=open('requirements.txt').readlines(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
