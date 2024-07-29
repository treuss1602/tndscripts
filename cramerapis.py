''' Module for classes for Cramer Identify Functions '''

#              Factory Product      Query API                  Identify API (if applicable)
CramerAPIs = { "PHY_SINGLE_LINK": ("getPHYSingleLinkDetails", "identifyPHYSingleLink"),
               "PHY_ILAG":        ("getPHYILAGDetails",       "identifyPHYILAG"),
               "PHY_ESILAG":      ("getPHYESILAGDetails",     "identifyPHYESILAG"),
               "IPVPN_CORE":      ("getIPVPNCoreDetails",     "identifyIPVPNCore"),
               "IPVPN_SAP":       ("getIPVPNSAPDetails",      "identifyIPVPNSap"),
               "IP_SAP":          ("getIPSAPDetails",         "identifyIPSap"),
               "ELAN_CORE":       ("getELANCoreDetails",      "identifyELANCore"),
               "ELAN_SAP":        ("getELANSAPDetails",       None),
               "ELINE_CORE":      ("getElineCoreDetails",     "identifyElineCore"),
               "ELINE_SAP":       ("getElineSAPDetails",      None),
}
