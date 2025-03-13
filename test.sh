#!/bin/bash

EX=" --all-objects --log-level DEBUG "
# geese export ${EX} --export-dir cribl/tst
# geese export ${EX} --export-dir cribl/tst_ns --use-namespace
# geese export ${EX} --export-dir cribl/tst_ns_split --use-namespace --export-split
# geese export ${EX} --export-dir cribl/tst_split --export-split

# geese simulate ${EX} --import-dir cribl/tst
# geese simulate ${EX} --import-dir cribl/tst_ns --use-namespace
# geese simulate ${EX} --import-dir cribl/tst_ns_split --use-namespace --split
# geese simulate ${EX} --import-dir cribl/tst_split --split

echo "geese validate ${EX} --import-dir cribl/tst"
# geese validate ${EX} --import-dir cribl/tst
# geese validate ${EX} --import-dir cribl/tst_ns --use-namespace
# geese validate ${EX} --import-dir cribl/tst_ns_split --use-namespace --split
# geese validate ${EX} --import-dir cribl/tst_split --split