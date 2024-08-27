#!/bin/bash

source tndcomponents.sh

TABLES="LKT_TND_FACTORY_PRODUCT_PARAMETERS LKT_MANDATORY_PARAM_CHECK LKT_TND_ENUM_PARAM_CHECK LKT_TND_CRAMER_COMMAND_VALIDATION LKT_TND_CRAMER_QUERY_SERVICE LKT_TND_CRAMER_IDENTIFY_SERVICE LKT_TND_CRAMER_SUBORDERS LKT_TND_STABLENET LKT_TND_STATIC_PARAM_VALUES LKT_TND_DISPLAY_PARAMETERS"
TARGETDIR=cicd


if [ -d $TARGETDIR ]; then
        echo "Cleaning all files from directory $TARGETDIR"
        rm -f $TARGETDIR/LKT*
else
        echo "Cleaning all files from directory $TARGETDIR"
        mkdir $TARGETDIR
fi

for fp in $FACTORY_PRODUCTS; do
    ./create_lookup_tables.py -D10 "FP_${fp}.json" -d $TARGETDIR
done
for comp in $COMPONENTS; do
    ./create_lookup_tables.py -D10 "Component_${comp}.json" -d $TARGETDIR
done
for cfs in $CFSES; do
    ./create_lookup_tables.py -D10 "CFS_${cfs}.json" -d $TARGETDIR
done
