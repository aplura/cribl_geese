#!/bin/bash
#bumpversion --allow-dirty patch
rm -rf dist/geese-*
python3 setup.py sdist
pip3 install --upgrade dist/geese-*