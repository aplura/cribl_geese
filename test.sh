#!/bin/bash

geese export --export-dir cribl/tst
geese export --export-dir cribl/tst_ns --use-namespace
geese export --export-dir cribl/tst_ns_split --use-namespace --export-split
geese export --export-dir cribl/tst_split --export-split