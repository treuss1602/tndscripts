''' Module for classes for Cramer Identify Functions '''

#              Factory Product      Query API                  Identify API (if applicable)
CramerAPIs = { "PHY_SINGLE_LINK": ("getPHYSingleLinkDetails", "identifyPHYSingleLink"),
               "PHY_ILAG":        ("getPHYILAGDetails",       "identifyPHYILAG"),
               "IPVPN_CORE":      ("getIPVPNCoreDetails",     "identifyIPVPNCore"),
               "IPVPN_SAP":       ("getIPVPNSAPDetails",      "identifyIPVPNSap"),
               "ELAN_CORE":       ("getELANCoreDetails",      "identifyELANCore"),
               "ELAN_SAP":        ("getELANSAPDetails",       None),
}
