#!/bin/bash

for fp in PHY_SINGLE_LINK PHY_ILAG IPVPN_CORE IPVPN_SAP ELAN_CORE ELAN_SAP; do
    ./create_lookup_tables.py "FP_${fp}_Create.json"
    test -d cicd/$fp || mkdir cicd/$fp
    unzip -d cicd/$fp -o "${fp}_Create.zip"
done
for tab in LKT_MANDATORY_PARAM_CHECK LKT_TND_CRAMER_SUBORDERS LKT_TND_FACTORY_PRODUCT_PARAMETERS LKT_TND_CRAMER_COMMAND_VALIDATION LKT_TND_ENUM_PARAM_CHECK LKT_TND_STABLENET; do
    cat cicd/*/$tab >cicd/$tab
done