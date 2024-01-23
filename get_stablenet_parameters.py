#!/usr/bin/python3
import argparse

from factoryproduct import FactoryProductConfiguration
from debug import DBG, set_debug_level

TR = {("IPVPN_SAP", "IPV4_STATIC_ROUTE_<N>"): ["IPV4_STATIC_ROUTES_SUBNETS", "IPV4_STATIC_ROUTES_NEXTHOP_ADDRESSES", "IPV4_STATIC_ROUTES_VRF_NAMES", "IPV4_STATIC_ROUTES_ROUTE_TAGS", "IPV4_STATIC_ROUTES_ADMIN_DISTANCES"],
      ("IPVPN_SAP", "IPV6_STATIC_ROUTE_<N>"): ["IPV6_STATIC_ROUTES_SUBNETS", "IPV6_STATIC_ROUTES_NEXTHOP_ADDRESSES", "IPV6_STATIC_ROUTES_VRF_NAMES", "IPV6_STATIC_ROUTES_ROUTE_TAGS", "IPV6_STATIC_ROUTES_ADMIN_DISTANCES"],
     }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-D', dest='dbglevel', action='store', default=0,    help='Print Debug information')
    parser.add_argument('filename', metavar='<FILENAME>', nargs="+",         help='JSON input files')

    args=parser.parse_args()
    set_debug_level(args.dbglevel)

    for filename in args.filename:
        DBG(10, "Reading json file '{}'".format(filename))
        with open(filename, "r") as fp:
            config = FactoryProductConfiguration.from_file(fp)
            if len(args.filename) > 1:
                print(config.factoryProductName)
                print("="*len(config.factoryProductName))
            parameters = []
            for p in config.input_params + config.cramer_output_params:
                if not p.special and p.name not in parameters: # Avoid adding inputOrReturn parameters twice
                    if (config.factoryProductName, p.name) in TR:
                        parameters += TR[(config.factoryProductName, p.name)]
                    else:
                        parameters.append(p.name)
            #print("\n".join([p.name for p in config.input_params + config.cramer_output_params if not p.special]))
            print("\n".join(parameters))
            if len(args.filename) > 1:
                print()
