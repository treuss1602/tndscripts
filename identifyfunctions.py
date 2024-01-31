''' Module for classes for Cramer Identify Functions '''

IdentifyFunctions = {
    "PHY_SINGLE_LINK": { "api": "identifyPHYSingleLink",
                         "inparams" : { "networkElementName": "NETWORK_ELEMENT_NAME", 
                                        "phyIfName": "PHYS_IF_NAME",
                                        "custSnippetName": "CUST_SNIPPET_NAMES"},
                         "outparams" : { "serviceReuse": "SERVICE_FOUND",
                                         "phySingleLinkRfsName": "PHY_SINGLE_LINK_RFS_NAME",
                                         "phyAccessServiceName": "PHY_ACCESS_SERVICE_NAME",
                                         "accessDeviceName": "ACCESS_DEVICE_NAME",
                                         "accessDeviceIfName": "ACCESS_DEVICE_IF_NAME",
                                         "phyIfSpeed": "PHYS_IF_SPEED",
                                         "phyIfType": "PHYS_IF_TYPE",
                                         "phyIfCenterFrequency": "PHYS_IF_CENTER_FREQUENCY",
                                         "phyIfTxPower": "PHYS_IF_TX_POWER"}
                       },
    "IPVPN_CORE": { "api": "identifyIPVPNCore",
                    "inparams" : { "nodeName": "NETWORK_ELEMENT_NAME", 
                                   "l3vpnName": "L3_VPN_NAME",
                                   "vrfName": "VRF_NAME",
                                   "vrfType": "VRF_TYPE", 
                                   "custSnippetName": "CUST_SNIPPET_NAMES"},
                    "outparams" : { "serviceReuse": "SERVICE_FOUND",
                                    "ipvpnCoreName": "IPVPN_CORE_RFS_NAME",
                                    "vrfName": "VRF_NAME",
                                    "ipvpnCoreId": "IPVPN_CORE_ID"}
                  },
    "IPVPN_SAP": { "api": "identifyIPVPNSap",
                   "inparams" : { "nodeName": "NETWORK_ELEMENT_NAME",
                                  # TODO
                                  "custSnippetName": "CUST_SNIPPET_NAMES"},
                   "outparams" : { "serviceReuse": "SERVICE_FOUND",
                                   "ipvpnSapName": "IPVPN_SAP_RFS_NAME"}
                 },
    "ELAN_CORE": { "api": "identifyELANCore",
                   "inparams" : { "nodeName": "NETWORK_ELEMENT_NAME", 
                                  "l2vpnName": "L3_VPN_NAME",
                                  "eviName": "EVI_NAME",
                                  "eviType": "EVI_TYPE", 
                                  "custSnippetName": "CUST_SNIPPET_NAMES"},
                   "outparams" : { "serviceReuse": "SERVICE_FOUND",
                                   "elanCoreName": "ELAN_CORE_RFS_NAME",
                                   "eviNAme": "EVI_NAME"}
                 },
}
