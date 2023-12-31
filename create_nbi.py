#!/usr/bin/python3
import argparse

from factoryproduct import FactoryProductConfiguration
from debug import DBG, set_debug_level

def create_confluence_table(productconfig : FactoryProductConfiguration, headers=True):
    if headers:
        print("h2. Factory Product {}".format(productconfig.factoryProductName))
        print("h3. {}".format(productconfig.transaction))
    print("||Parameter name (without prefix)||Section||Description||Example Value||M/O/C||")
    print("|EXTERNAL_ORDER_ID|General|Reference to the order number. Generated by the northbound system.|O00324572912|M|")
    for param in productconfig.input_params:
        print("|{}|Order Line|{}|{}|{}|".format(param.name, param.desc, param.examplevalue, "M" if param.mandatory else "O"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-D', dest='dbglevel', action='store', default=0,    help='Print Debug information')
    parser.add_argument('-H', dest='headers', action='store_true',           help='Include headers (default if multiple files are given)')
    parser.add_argument('filename', metavar='<FILENAME>', nargs="*",         help='JSON input files')

    args=parser.parse_args()
    set_debug_level(args.dbglevel)

    for f in args.filename:
        DBG(10, "Reading json file '{}'".format(f))
        with open(f, "r") as fp:
            config = FactoryProductConfiguration.from_file(fp)
        create_confluence_table(config, args.headers or len(args.filename) > 1)
