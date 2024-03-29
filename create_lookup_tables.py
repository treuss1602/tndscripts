#!/usr/bin/python3
import argparse
import functools
import json
import re
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

def create_lookup_tables_for_factory_product(config : FactoryProductConfiguration, nenameparam : str="NETWORK_ELEMENT_NAME"):
    ''' Create the lookup Tables '''
    prod = config.factoryProductName
    tables = []

    # LKT_TND_FACTORY_PRODUCT_PARAMETERS
    lkt = LookupTable('LKT_TND_FACTORY_PRODUCT_PARAMETERS')
    lkt.add(LtEntry(prod+"#Create",
                     joinparams(config.input_params), 
                     joinparams([p for p in config.input_params if p.dynamically_mapped]), 
                     ";".join(config.key_params)+";"))
    lkt.add(LtEntry(prod+"#Delete", "{}_RFS_NAME;".format(prod), ";", ";".join(config.key_params)+";"))
    tables.append(lkt)

    # LKT_MANDATORY_PARAM_CHECK
    lkt = LookupTable('LKT_MANDATORY_PARAM_CHECK')
    lkt.add(LtEntry('FACTORY_PRODUCT_'+prod+"#Create", "PAUSE_AFTER_PREPARE "+" ".join(p.name.replace('_<N>','_1') for p in config.input_params if p.mandatory)+" ", "ORDER_TYPE IL_REQ_GROUP ORDER_EXTERNAL_ORDER_ID "))
    lkt.add(LtEntry('FACTORY_PRODUCT_'+prod+"#Delete", "PAUSE_AFTER_PREPARE {}_RFS_NAME ".format(prod), "ORDER_TYPE IL_REQ_GROUP ORDER_EXTERNAL_ORDER_ID "))
    lkt.add(LtEntry('FACTORY_PRODUCT_'+prod+"#Modify", "PAUSE_AFTER_PREPARE {}_RFS_NAME ".format(prod), "ORDER_TYPE IL_REQ_GROUP ORDER_EXTERNAL_ORDER_ID "))
    tables.append(lkt)

    # LKT_TND_ENUM_PARAM_CHECK
    lkt = LookupTable('LKT_TND_ENUM_PARAM_CHECK')
    lkt.add(LtEntry(prod+"#Create#ENUM_PARAMS", ";".join(p.name for p in config.input_params if p.valuetype == "enumerated" or p.valuetype == "boolean")+";"))
    for p in config.input_params:
        if p.valuetype == "enumerated":
            lkt.add(LtEntry(prod+"#Create#{}".format(p.name), ";".join(p.enumvalues)+";"))
        elif p.valuetype == "boolean":
            lkt.add(LtEntry(prod+"#Create#{}".format(p.name), "true;false;"))
    tables.append(lkt)

    # LKT_TND_CRAMER_COMMAND_VALIDATION
    tables.append(LookupTable.from_validations(prod, "Create", *config.cramer_validations))

    # LKT_TND_CRAMER_QUERY_SERVICE
    api = CramerAPIs[prod][0]
    if api:
        lkt = LookupTable('LKT_TND_CRAMER_QUERY_SERVICE')
        for trans in ["Create", "Delete", "Modify"]:
            lkt.add(LtEntry(prod+"#"+trans+"#API_NAME", api))
            rfsparam = config.find_return_param('{}_RFS_NAME'.format(prod))
            inputparams = {rfsparam.jsonname: rfsparam.name}
            DBG(30, "Input parameters for query API are: {}".format(inputparams))
            lkt.add(LtEntry(prod+"#"+trans+"#PARAMETERS", ";".join("{}={}".format(*it) for it in inputparams.items())+";"))
            returnparams = {p.jsonname: p.name for p in config.input_params + config.cramer_output_params if p.jsonname is not None}
            DBG(30, "Return parameters for query API are: {}".format(returnparams))
            lkt.add(LtEntry(prod+"#"+trans+"#RETURN_PARAMETERS", ",".join("{}:{}".format(k, re.sub(r'\<N\>$','',v)) for k,v in returnparams.items())))
            gereturnparams =  set(p.name for p in config.input_params + config.cramer_output_params if p.cramerStorage == config.factoryProductName+"_GE")
            DBG(30, "Return GE parameters for query API are: {}".format(gereturnparams))
            lkt.add(LtEntry(prod+"#"+trans+"#RETURN_GE_PARAMETERS", ";".join(gereturnparams)+";"))

    else:
        print("No query function defined for product {}".format(prod))
        lkt = None
    tables.append(lkt)

    # LKT_TND_CRAMER_IDENTIFY_SERVICE
    api = CramerAPIs[prod][1]
    if api:
        lkt = LookupTable('LKT_TND_CRAMER_IDENTIFY_SERVICE')
        lkt.add(LtEntry(prod+"#Create#API_NAME", api))
        inputparams = {p.jsonname: p.name for p in config.input_params if p.jsonname is not None}
        DBG(30, "Input parameters for identify API are: {}".format(inputparams))
        lkt.add(LtEntry(prod+"#Create#PARAMETERS", ";".join("{}={}".format(*it) for it in inputparams.items())+";"))
        lkt.add(LtEntry(prod+"#Create#GE_PARAMETERS", joinparams([p for p in config.input_params if p.cramerStorage == config.factoryProductName+"_GE"])))
        returnparams = {"serviceFound": "SERVICE_FOUND"}
        returnparams.update({p.jsonname: p.name for p in config.cramer_output_params if p.jsonname is not None})
        DBG(30, "Return parameters for identify API are: {}".format(returnparams))
        lkt.add(LtEntry(prod+"#Create#RETURN_PARAMETERS", ",".join("{}:{}".format(k,re.sub(r'\<N\>$','',v)) for k,v in returnparams.items())))
    else:
        print("No identify function defined for product {}".format(prod))
        lkt = None
    tables.append(lkt)

    # LKT_TND_CRAMER_SUBORDERS
    lkt = LookupTable('LKT_TND_CRAMER_SUBORDERS')
    lkt.add(LtEntry(prod+"#Create#SUBORDER_PRODUCT", "TECHPROD_CRAMER_FACT_PROD_"+prod))
    lkt.add(LtEntry(prod+"#Delete#SUBORDER_PRODUCT", "TECHPROD_CRAMER_FACT_PROD_"+prod))
    lkt.add(LtEntry(prod+"#Create#PARAMETERS", joinparams([p for p in config.input_params if not p.special])))
    lkt.add(LtEntry(prod+"#Delete#PARAMETERS", "{}_RFS_NAME;".format(prod)))
    lkt.add(LtEntry(prod+"#Create#RETURN_PARAMETERS", joinparams(config.cramer_output_params)))
    lkt.add(LtEntry(prod+"#Delete#RETURN_PARAMETERS", ";"))
    lkt.add(LtEntry(prod+"#Create#GE_PARAMETERS", joinparams([p for p in config.input_params if p.cramerStorage == config.factoryProductName+"_GE"])))
    lkt.add(LtEntry(prod+"#Delete#GE_PARAMETERS", ";"))
    tables.append(lkt)

    # LKT_TND_STABLENET
    lkt = LookupTable('LKT_TND_STABLENET')
    lkt.add(LtEntry(prod+"#Create#ORDER_DESCRIPTION", "new_rfs"))
    lkt.add(LtEntry(prod+"#Delete#ORDER_DESCRIPTION", "cease_rfs"))
    for trans in ["Create", "Delete", "Modify"]:
        lkt.add(LtEntry(prod+"#"+trans+"#TARGET_DEVICE", nenameparam))
        lkt.add(LtEntry(prod+"#"+trans+"#RFS_NAME", config.factoryProductName+"_RFS_NAME"))
        parameters = config.stablenet_params[0]
        lkt.add(LtEntry(prod+"#"+trans+"#PARAMETERS", ";".join(parameters)+";"))
    tables.append(lkt)

    return tables

def create_lookup_tables_for_composition(data):
    ''' Create the lookup Tables '''
    if data["compositionType"] == "cfs":
        cfs = data["compositionName"]
        component = ""
    else:
        component = data["compositionName"]
        cfs = ""

    action = "Create" # Currently no other action supported
    
    lkt = LookupTable('LKT_TND_STATIC_PARAM_VALUES')
    for fpdata in data["paramMapping"]:
        fpname = fpdata["factoryProduct"]
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
            outfile = "{}.zip".format(config.factoryProductName) if args.outfile is None else args.outfile
            create_zipfile(outfile, *tables)
            print(outfile)
        elif "compositionName" in jsondata:
            table = create_lookup_tables_for_composition(jsondata)
            DBG(30, "Lookup Table dump:\n"+table.debugdump())
            outfile = "{}.zip".format(jsondata["compositionName"]) if args.outfile is None else args.outfile
            create_zipfile(outfile, table)
            print(outfile)
        
