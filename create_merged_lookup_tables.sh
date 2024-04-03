#!/bin/bash

FACTORY_PRODUCTS="PHY_SINGLE_LINK PHY_ILAG IPVPN_CORE IPVPN_SAP ELAN_CORE ELAN_SAP"
COMPONENTS="RBH_RPD RBH_CMTS RBH_CMTS_INET RBH_CMTS_ABR_MC"
CFSES="TN_RBH_RPD_ACCESS TN_RBH_CMTS_ACCESS TN_RBH_CMTS_CORE"
TABLES="LKT_TND_FACTORY_PRODUCT_PARAMETERS LKT_MANDATORY_PARAM_CHECK LKT_TND_ENUM_PARAM_CHECK LKT_TND_CRAMER_COMMAND_VALIDATION LKT_TND_CRAMER_QUERY_SERVICE LKT_TND_CRAMER_IDENTIFY_SERVICE LKT_TND_CRAMER_SUBORDERS LKT_TND_STABLENET LKT_TND_STATIC_PARAM_VALUES LKT_TND_DISPLAY_PARAMETERS"

test -d cicd || mkdir cicd
for fp in $FACTORY_PRODUCTS; do
    ./create_lookup_tables.py -D0 "FP_${fp}.json"
    test -d cicd/$fp || mkdir cicd/$fp
    unzip -d cicd/$fp -o -q "${fp}.zip"
done
for comp in $COMPONENTS; do
    ./create_lookup_tables.py -D0 "Component_${comp}.json"
    test -d cicd/$comp || mkdir cicd/$comp
    unzip -d cicd/$comp -o -q "${comp}.zip"
done
for cfs in $CFSES; do
    ./create_lookup_tables.py -D0 "CFS_${cfs}.json"
    test -d cicd/$cfs || mkdir cicd/$cfs
    unzip -d cicd/$cfs -o -q "${cfs}.zip"
done

for tab in $TABLES; do
    cat cicd/*/$tab >cicd/$tab
done
