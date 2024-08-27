#!/bin/bash

source tndcomponents.sh

if [ $# -ne 1 ]; then
	echo "Usage: recreate_all_jsons.sh <XLS-FILE>"
	exit 1
fi
XLS=$1
if [ ! -f "$XLS" ]; then
	echo "No such file: $XLS"
	exit 1
fi
for fp in $FACTORY_PRODUCTS; do
    python ./excel2json.py -t $fp "$XLS"
done
for com in $COMPONENTS $CFSES; do
    python ./extract_cfs_param_table.py "$XLS" $com
done
