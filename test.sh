#!/bin/bash

geese export --all-objects --export-dir cribl/tst
geese export --all-objects --export-dir cribl/tst_ns --use-namespace
geese export --all-objects --export-dir cribl/tst_ns_split --use-namespace --export-split
geese export --all-objects --export-dir cribl/tst_split --export-split