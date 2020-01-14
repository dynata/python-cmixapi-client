import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="python-cmixapi-client",
    version="0.1.2",
    author="Bradley Wogsland",
    author_email="bradley@wogsland.org",
    description="A Python client for the Cmix API.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dynata/python-cmixapi-client",
    packages=setuptools.find_packages(exclude=('tests', )),
    platforms=['Any'],
    install_requires=['requests'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    keywords='cmix api dynata popresearch',
    classifiers=[
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
)
