#!/usr/bin/python3
import argparse
import functools
from zipfile import ZipFile
from factoryproduct import FactoryProductConfiguration
from lookuptable import LookupTable, LtEntry
from debug import DBG, set_debug_level

def create_zipfile(filename, *tables):
    DBG(10, "Writing Lookup Tables zipfile '{}'".format(filename))
    with ZipFile(filename, "w") as z:
        for table in tables:
            z.writestr(table.name, table.dump())

def joinparams(*paramsets):
    return ";".join(map(lambda x: x.name, functools.reduce(lambda a,b: a+b, paramsets)))+";"

def create_lookup_tables(config, nenameparam="NETWORK_ELEMENT_NAME"):
    ''' Create the lookup Tables '''
    prod = config.factoryProductName
    trans = config.transaction
    lkt1 = LookupTable('LKT_TND_FACTORY_PRODUCT_PARAMETERS')
    lkt1.add(LtEntry(prod+"#"+trans, joinparams(config.input_params)))

    lkt2 = LookupTable.from_validations(prod, trans, *config.cramer_validations)

    lkt3 = LookupTable('LKT_TND_CRAMER_SUBORDERS')
    lkt3.add(LtEntry(prod+"#"+trans+"#SUBORDER_PRODUCT", "TECHPROD_CRAMER_FACT_PROD_"+prod))
    lkt3.add(LtEntry(prod+"#"+trans+"#PARAMETERS", joinparams([p for p in config.input_params if not p.special])))
    lkt3.add(LtEntry(prod+"#"+trans+"#RETURN_PARAMETERS", joinparams(config.cramer_output_params)))
    lkt3.add(LtEntry(prod+"#"+trans+"#GE_PARAMETERS", joinparams([p for p in config.input_params if p.cramerStorage == config.factoryProductName+"_GE"])))

    lkt4 = LookupTable('LKT_TND_STABLENET')
    if config.transaction == "Create":
        lkt4.add(LtEntry(prod+"#"+trans+"#ORDER_DESCRIPTION", "new_rfs"))
    elif config.transaction == "Delete":
        lkt4.add(LtEntry(prod+"#"+trans+"#ORDER_DESCRIPTION", "cease_rfs"))
    else:
        raise ValueError("Action {} not (yet) supported for Stablenet Requests.")
    lkt4.add(LtEntry(prod+"#"+trans+"#TARGET_DEVICE", nenameparam))
    lkt4.add(LtEntry(prod+"#"+trans+"#RFS_NAME", config.factoryProductName+"_RFS_NAME"))
    lkt4.add(LtEntry(prod+"#"+trans+"#PARAMETERS", joinparams([p for p in config.input_params if not p.special], config.cramer_output_params)))

    lkt5 = LookupTable('LKT_TND_ENUM_PARAM_CHECK')
    lkt5.add(LtEntry(prod+"#"+trans+"#ENUM_PARAMS", ";".join(p.name for p in config.input_params if p.valuetype == "enumerated")+";"))
    for p in config.input_params:
        if p.valuetype == "enumerated" or p.valuetype == "enumeration":
            lkt5.add(LtEntry(prod+"#"+trans+"#{}".format(p.name), ";".join(p.enumvalues)+";"))

    lkt6 = LookupTable('LKT_MANDATORY_PARAM_CHECK')
    lkt6.add(LtEntry('FACTORY_PRODUCT_'+prod+"#"+trans, " ".join(p.name for p in config.input_params if p.mandatory)+" ", "ORDER_TYPE IL_REQ_GROUP ORDER_EXTERNAL_ORDER_ID "))

    return (lkt1, lkt2, lkt3, lkt4, lkt5, lkt6)


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
    tables = create_lookup_tables(config)
    for table in tables:
        DBG(30, "Lookup Table dump:\n"+table.debugdump())
    outfile = "{}_{}.zip".format(config.factoryProductName, config.transaction) if args.outfile is None else args.outfile
    create_zipfile(outfile, *tables)
