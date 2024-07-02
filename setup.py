import os
import setuptools


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setuptools.setup(
    name="geese",
    version="1.1.4",
    author="Aplura, LLC",
    author_email="appsupport@aplura.com",
    description="Cribl Migrator",
    license="MIT",
    license_files=('LICENSE.txt',),
    keywords="aplura cribl migration",
    url="https://www.aplura.com",
    packages=setuptools.find_packages(),
    package_data={"geese": [
        "constants/**/*",
        "configs/**/*",
        "commands/**/*",
        "assets/**/*",
        "constants/*",
        "configs/*",
        "commands/*",
        "assets/*",
        "knowledge/*",
        "knowledge/**/*",
        "utils/*",
        "utils/**/*",
        "*.py",
        "README.md",
        "LICENSE.txt",
    ]},
    long_description=read('README'),
    install_requires=[
        "PyYAML",
        "termcolor",
        "multicommand",
        "deepdiff",
        "deepmerge",
        "urllib3",
        "build"
    ],
    classifiers=[
        "Development Status :: 1 - Alpha",
        "Topic :: Utilities",
        "License :: MIT",
    ],
    entry_points={
        "console_scripts": ["geese = geese:main.main", ],
    }
)
