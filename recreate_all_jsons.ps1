$FACTORY_PRODUCTS=("PHY_SINGLE_LINK", "PHY_ILAG", "IPVPN_CORE", "IPVPN_SAP", "ELAN_CORE", "ELAN_SAP", "PHY_ESILAG")
$COMPONENTS=("RBH_RPD", "RBH_CMTS", "RBH_CMTS_INET", "RBH_CMTS_ABR_MC", "RTL_PROV", "RTL_MGT", "RTL_INET", "RTL_VOIP", "INF_DHCPTRAFFIC", "INF_MGT", "RTL_IPTV", "RTL_CGN")
$CFSES=("TN_RBH_RPD_ACCESS", "TN_RBH_CMTS_ACCESS", "TN_RBH_CMTS_CORE", "TN_B2C_OLT_ACCESS", "TN_B2C_XDSLAM_ACCESS", "TN_CMTS_ACCESS")
$TABLES=("LKT_TND_FACTORY_PRODUCT_PARAMETERS", "LKT_MANDATORY_PARAM_CHECK", "LKT_TND_ENUM_PARAM_CHECK", "LKT_TND_CRAMER_COMMAND_VALIDATION", "LKT_TND_CRAMER_QUERY_SERVICE", "LKT_TND_CRAMER_IDENTIFY_SERVICE", "LKT_TND_CRAMER_SUBORDERS", "LKT_TND_STABLENET")

if ($args.length -ne 1) {
	Write-Warning "Argument <EXCEL-FILE> expected."
	exit 1
}
$XLS=$args[0]
if (!(Test-Path "$XLS")) {
	Write-Warning "No such file: '$XLS'"
} else {
	foreach ($fp in $FACTORY_PRODUCTS) {python ./excel2json.py -t $fp "$XLS"}
	foreach ($com in $COMPONENTS) {python ./extract_cfs_param_table.py "$XLS" $com}
	foreach ($cfs in $CFSES) {python ./extract_cfs_param_table.py "$XLS" $cfs}
}
