#!/usr/bin/python3
import argparse
import functools
import json
from zipfile import ZipFile
from factoryproduct import FactoryProductConfiguration
from lookuptable import LookupTable, LtEntry
from cramerapis import CramerAPIs
from debug import DBG, set_debug_level

def create_zipfile(filename, *tables):
    DBG(10, "Writing Lookup Tables zipfile '{}'".format(filename))
    with ZipFile(filename, "w") as z:
        for table in tables:
            if table:
                z.writestr(table.name, table.dump())

def joinparams(*paramsets):
    return ";".join(map(lambda x: x.name, functools.reduce(lambda a,b: a+b, paramsets)))+";"

def create_lookup_tables_for_factory_product(config, nenameparam="NETWORK_ELEMENT_NAME"):
    ''' Create the lookup Tables '''
    prod = config.factoryProductName
    trans = config.transaction

    # LKT_TND_FACTORY_PRODUCT_PARAMETERS
    lkt1 = LookupTable('LKT_TND_FACTORY_PRODUCT_PARAMETERS')
    lkt1.add(LtEntry(prod+"#"+trans, joinparams(config.input_params), joinparams([p for p in config.input_params if p.dynamically_mapped])))

    # LKT_MANDATORY_PARAM_CHECK
    lkt2 = LookupTable('LKT_MANDATORY_PARAM_CHECK')
    lkt2.add(LtEntry('FACTORY_PRODUCT_'+prod+"#"+trans, " ".join(p.name for p in config.input_params if p.mandatory)+" ", "ORDER_TYPE IL_REQ_GROUP ORDER_EXTERNAL_ORDER_ID "))

    # LKT_TND_ENUM_PARAM_CHECK
    lkt3 = LookupTable('LKT_TND_ENUM_PARAM_CHECK')
    lkt3.add(LtEntry(prod+"#"+trans+"#ENUM_PARAMS", ";".join(p.name for p in config.input_params if p.valuetype == "enumerated" or p.valuetype == "boolean")+";"))
    for p in config.input_params:
        if p.valuetype == "enumerated":
            lkt3.add(LtEntry(prod+"#"+trans+"#{}".format(p.name), ";".join(p.enumvalues)+";"))
        elif p.valuetype == "boolean":
            lkt3.add(LtEntry(prod+"#"+trans+"#{}".format(p.name), "true;false;"))

    # LKT_TND_CRAMER_COMMAND_VALIDATION
    lkt4 = LookupTable.from_validations(prod, trans, *config.cramer_validations)

    # LKT_LKT_TND_CRAMER_IDENTIFY_SERVICE
    api = CramerAPIs[prod][1]
    if api:
        lkt5 = LookupTable('LKT_TND_CRAMER_IDENTIFY_SERVICE')
        lkt5.add(LtEntry(prod+"#"+trans+"#API_NAME", api))
        inputparams = {p.jsonname: p.name for p in config.input_params if p.jsonname is not None}
        DBG(30, "Input parameters for identify API are: {}".format(inputparams))
        lkt5.add(LtEntry(prod+"#"+trans+"#PARAMETERS", ";".join("{}={}".format(*it) for it in inputparams.items())+";"))
        lkt5.add(LtEntry(prod+"#"+trans+"#GE_PARAMETERS", joinparams([p for p in config.input_params if p.cramerStorage == config.factoryProductName+"_GE"])))
        returnparams = {"serviceFound": "SERVICE_FOUND"} | {p.jsonname: p.name for p in config.cramer_output_params if p.jsonname is not None}
        DBG(30, "Return parameters for identify API are: {}".format(returnparams))
        lkt5.add(LtEntry(prod+"#"+trans+"#RETURN_PARAMETERS", ",".join("{}:{}".format(*it) for it in returnparams.items())))
    else:
        print("No identify function defined for product {}".format(prod))
        lkt5 = None

    # LKT_TND_CRAMER_SUBORDERS
    lkt6 = LookupTable('LKT_TND_CRAMER_SUBORDERS')
    lkt6.add(LtEntry(prod+"#"+trans+"#SUBORDER_PRODUCT", "TECHPROD_CRAMER_FACT_PROD_"+prod))
    lkt6.add(LtEntry(prod+"#"+trans+"#PARAMETERS", joinparams([p for p in config.input_params if not p.special])))
    lkt6.add(LtEntry(prod+"#"+trans+"#RETURN_PARAMETERS", joinparams(config.cramer_output_params)))
    lkt6.add(LtEntry(prod+"#"+trans+"#GE_PARAMETERS", joinparams([p for p in config.input_params if p.cramerStorage == config.factoryProductName+"_GE"])))

    # LKT_TND_STABLENET
    lkt7 = LookupTable('LKT_TND_STABLENET')
    if config.transaction == "Create":
        lkt7.add(LtEntry(prod+"#"+trans+"#ORDER_DESCRIPTION", "new_rfs"))
    elif config.transaction == "Delete":
        lkt7.add(LtEntry(prod+"#"+trans+"#ORDER_DESCRIPTION", "cease_rfs"))
    else:
        raise ValueError("Action {} not (yet) supported for Stablenet Requests.")
    lkt7.add(LtEntry(prod+"#"+trans+"#TARGET_DEVICE", nenameparam))
    lkt7.add(LtEntry(prod+"#"+trans+"#RFS_NAME", config.factoryProductName+"_RFS_NAME"))
    parameters = [p for p in config.input_params if not p.special]
    parameters += [p for p in config.cramer_output_params if p.name not in config.input_param_names()]
    lkt7.add(LtEntry(prod+"#"+trans+"#PARAMETERS", joinparams(parameters)))

    return (lkt1, lkt2, lkt3, lkt4, lkt5, lkt6, lkt7)

def create_lookup_tables_for_composition(data):
    ''' Create the lookup Tables '''
    if data["compositionType"] == "cfs":
        cfs = data["compositionName"]
        component = ""
    else:
        component = data["compositionName"]
        cfs = ""
    
    lkt = LookupTable('LKT_TND_STATIC_PARAM_VALUES')
    for fpdata in data["paramMapping"]:
        fpname = fpdata["factoryProduct"]
        action = fpdata["action"]
        for paramdata in fpdata["parameters"]:
            pname, ptype = (paramdata[x] for x in ["name", "type"])
            key = "#".join([cfs, component, fpname, action, pname])
            DBG(30, "Key is {}".format(key))
            if ptype == "static":
                values = (paramdata["value"] if paramdata["value"] is not None else "<NULL>", "S")
            elif ptype in ["input", "mapped"]:
                values = (paramdata["from"], "D")
            DBG(30, "Values are {}".format(values))
            lkt.add(LtEntry(key, *values))
    return lkt

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-D', dest='dbglevel', action='store', default=10,    help='Print Debug information')
    parser.add_argument('-o', dest='outfile', metavar='<OUTPUT_FILE>', help='Name of the output file (overrides default name)')
    parser.add_argument('filenames', metavar='<FILENAME>', nargs='+', help='JSON input file(s)')

    args=parser.parse_args()
    set_debug_level(args.dbglevel)

    for filename in args.filenames:
        DBG(10, "Reading json file '{}'".format(filename))
        with open(filename, "r") as fp:
            jsondata = json.load(fp)

        if "factoryProductName" in jsondata:
            config = FactoryProductConfiguration.from_jsondata(jsondata)
            tables = create_lookup_tables_for_factory_product(config)
            for table in tables:
                if table is not None:
                    DBG(30, "Lookup Table dump:\n"+table.debugdump())
                else:
                    DBG(30, "No lookup table")
            outfile = "{}_{}.zip".format(config.factoryProductName, config.transaction) if args.outfile is None else args.outfile
            create_zipfile(outfile, *tables)
            print(outfile)
        elif "compositionName" in jsondata:
            table = create_lookup_tables_for_composition(jsondata)
            DBG(30, "Lookup Table dump:\n"+table.debugdump())
            outfile = "{}.zip".format(jsondata["compositionName"]) if args.outfile is None else args.outfile
            create_zipfile(outfile, table)
            print(outfile)
        
