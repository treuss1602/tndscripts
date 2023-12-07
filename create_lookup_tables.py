#!/usr/bin/python3
import argparse
from zipfile import ZipFile
from factoryproduct import FactoryProductConfiguration
from debug import DBG, set_debug_level

def create_zipfile(filename, *tables):
    DBG(10, "Writing Lookup Tables zipfile '{}'".format(filename))
    with ZipFile(filename, "w") as z:
        for table in tables:
            z.writestr(table.name, table.dump())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-D', dest='dbglevel', action='store', default=10,    help='Print Debug information')
    parser.add_argument('-o', dest='outfile', metavar='<OUTPUT_FILE>', help='Name of the output file (overrides default name)')
    parser.add_argument('filename', metavar='<FILENAME>', help='JSON input file')

    args=parser.parse_args()
    set_debug_level(args.dbglevel)

    DBG(10, "Reading json file '{}'".format(args.filename))
    with open(args.filename, "r") as fp:
        config = FactoryProductConfiguration.from_file(fp)
    tables = config.create_lookup_tables()
    for table in tables:
        DBG(30, "Lookup Table dump:\n"+table.debugdump())
    outfile = "{}_{}.zip".format(config.factoryProductName, config.transaction) if args.outfile is None else args.outfile
    create_zipfile(outfile, *tables)
