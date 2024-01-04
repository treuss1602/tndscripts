#!/usr/bin/python3
import argparse

from factoryproduct import FactoryProductConfiguration
from debug import DBG, set_debug_level

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-D', dest='dbglevel', action='store', default=0,     help='Print Debug information')
    parser.add_argument('-s', dest='separator', action='store', default='\n', help='Print parameters on a single line with separator in between')
    parser.add_argument('filename', metavar='<FILENAME>',                     help='JSON input files')

    args=parser.parse_args()
    set_debug_level(args.dbglevel)

    DBG(10, "Reading json file '{}'".format(args.filename))
    with open(args.filename, "r") as fp:
        config = FactoryProductConfiguration.from_file(fp)
        print(args.separator.join([p.name for p in config.input_params if p.cramerStorage == config.factoryProductName+"_GE"]))
