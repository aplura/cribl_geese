#!/bin/bash
#bumpversion --allow-dirty patch
rm -rf dist/geese-*
cp README.md geese/README.md
cp LICENSE.txt geese/LICENSE.txt
python3 setup.py sdist
pip3 install --upgrade dist/geese-*