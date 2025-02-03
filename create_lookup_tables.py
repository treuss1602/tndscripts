#!/usr/bin/python3
import argparse
import functools
import json
import re
import os
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

def create_update_files_in_targetdir(dirname, *tables):
    DBG(10, "Writing Lookup Tables to files in '{}'".format(dirname))
    for table in tables:
        if table:
            filename = dirname + os.sep + table.name
            with open(filename, "a", newline='\n') as fp:
                fp.write(table.dump())

def joinparams(*paramsets):
    return ";".join(map(lambda x: x.name, functools.reduce(lambda a,b: a+b, paramsets)))+";"

def create_lookup_tables_for_factory_product(config : FactoryProductConfiguration, nenameparam : str="NETWORK_ELEMENT_NAME"):
    ''' Create the lookup Tables '''
    prod = config.factoryProductName
    tables = []
    MODIFY_OPS = ["ModifyParameter", "ModifyCustomSnippets", "ModifyQoS", "ModifySubnets", "ModifyVlan"]
    ALL_OPS = ["Create", "Delete"] + MODIFY_OPS

    # LKT_TND_FACTORY_PRODUCT_PARAMETERS
    lkt = LookupTable('LKT_TND_FACTORY_PRODUCT_PARAMETERS')
    lkt.add(LtEntry(prod+"#Create",
                     joinparams(config.input_params),
                     joinparams([p for p in config.input_params if p.dynamically_mapped]),
                     ";".join(config.key_params)+";"))
    lkt.add(LtEntry(prod+"#Delete", "{}_RFS_NAME;".format(prod), ";", ";".join(config.key_params)+";"))
    lkt.add(LtEntry(prod+"#Compare", "{}_RFS_NAME;".format(prod), ";", ";".join(config.key_params)+";"))
    lkt.add(LtEntry(prod+"#Provision", "{}_RFS_NAME;".format(prod), ";", ";".join(config.key_params)+";"))
    lkt.add(LtEntry(prod+"#Deprovision", "{}_RFS_NAME;".format(prod), ";", ";".join(config.key_params)+";"))
    lkt.add(LtEntry(prod+"#RemoveModelling", "{}_RFS_NAME;".format(prod), ";", ";".join(config.key_params)+";"))
    for tr in MODIFY_OPS:
        if tr in {p.modifyOperation for p in config.input_params}:
            lkt.add(LtEntry(prod+"#"+tr,
                            joinparams([p for p in config.input_params if p.modifyOperation == tr]),
                            ";",
                            ";".join(config.key_params)+";"))
    if prod == "PHY_SINGLE_LINK":
        lkt.add(LtEntry(prod+"#MoveLink", ";".join(["PHY_SINGLE_LINK_RFS_NAME", "TARGET_NETWORK_ELEMENT_NAME", "TARGET_PHYS_IF_NAME"])+";",
                        ";",
                        ";".join(config.key_params)+";"))
    elif prod in ["PHY_ILAG", "PHY_ESILAG"]:
        lkt.add(LtEntry(prod+"#AddMemberLinks", ";".join(["{}_RFS_NAME;".format(prod), "IDN_SERVICES"])+";",
                        ";",
                        ";".join(config.key_params)+";"))
        lkt.add(LtEntry(prod+"#RemoveMemberLinks", ";".join(["{}_RFS_NAME;".format(prod), "IDN_SERVICES"])+";",
                        ";",
                        ";".join(config.key_params)+";"))


    tables.append(lkt)

    # LKT_MANDATORY_PARAM_CHECK
    lkt = LookupTable('LKT_MANDATORY_PARAM_CHECK')
    lkt.add(LtEntry('FACTORY_PRODUCT_'+prod+"#Create", " ".join(p.name.replace('_<N>','_1') for p in config.input_params if p.mandatory)+" ", "ORDER_TYPE IL_REQ_GROUP ORDER_EXTERNAL_ORDER_ID "))
    lkt.add(LtEntry('FACTORY_PRODUCT_'+prod+"#Delete", "{}_RFS_NAME ".format(prod), "ORDER_TYPE IL_REQ_GROUP ORDER_EXTERNAL_ORDER_ID "))
    lkt.add(LtEntry('FACTORY_PRODUCT_'+prod+"#Provision", "{}_RFS_NAME CRAMER_CONTEXT_ID".format(prod), "ORDER_TYPE IL_REQ_GROUP ORDER_EXTERNAL_ORDER_ID "))
    lkt.add(LtEntry('FACTORY_PRODUCT_'+prod+"#Deprovision", "{}_RFS_NAME CRAMER_CONTEXT_ID".format(prod), "ORDER_TYPE IL_REQ_GROUP ORDER_EXTERNAL_ORDER_ID "))
    for tr in MODIFY_OPS:
        if tr in {p.modifyOperation for p in config.input_params}:
            lkt.add(LtEntry('FACTORY_PRODUCT_'+prod+"#"+tr, "{}_RFS_NAME ".format(prod), "ORDER_TYPE IL_REQ_GROUP ORDER_EXTERNAL_ORDER_ID "))
    tables.append(lkt)

    # LKT_TND_ENUM_PARAM_CHECK
    lkt = LookupTable('LKT_TND_ENUM_PARAM_CHECK')
    lkt.add(LtEntry(prod+"#Create#ENUM_PARAMS", ";".join(p.name for p in config.input_params if p.valuetype in ["enumerated", "boolean"])+";PAUSE_AFTER_PREPARE;"))
    for p in config.input_params:
        if p.valuetype == "enumerated":
            lkt.add(LtEntry(prod+"#Create#{}".format(p.name), ";".join(p.enumvalues)+";"))
        elif p.valuetype == "boolean":
            lkt.add(LtEntry(prod+"#Create#{}".format(p.name), "true;false;"))
    lkt.add(LtEntry(prod+"#Create#PAUSE_AFTER_PREPARE", "true;false;"))
    lkt.add(LtEntry(prod+"#Delete#ENUM_PARAMS", "PAUSE_AFTER_PREPARE;"))
    lkt.add(LtEntry(prod+"#Delete#PAUSE_AFTER_PREPARE", "true;false;"))
    for tr in MODIFY_OPS:
        if tr in {p.modifyOperation for p in config.input_params}:
            params = [p for p in config.input_params if p.modifyOperation == tr and p.valuetype in ["enumerated", "boolean"]]
            if params:
                lkt.add(LtEntry(prod+"#"+tr+"#ENUM_PARAMS", ";".join([p.name for p in params])+";PAUSE_AFTER_PREPARE;"))
                for p in params:
                    if p.valuetype == "enumerated":
                        lkt.add(LtEntry(prod+"#"+tr+"#{}".format(p.name), ";".join(p.enumvalues)+(";" if p.mandatory else ";__NULL__;")))
                    elif p.valuetype == "boolean":
                        lkt.add(LtEntry(prod+"#"+tr+"#{}".format(p.name), "true;false"+(";" if p.mandatory else ";__NULL__;")))
                lkt.add(LtEntry(prod+"#"+tr+"#PAUSE_AFTER_PREPARE", "true;false;"))
    tables.append(lkt)

    # LKT_TND_CRAMER_COMMAND_VALIDATION
    tables.append(LookupTable.from_validations(prod, config.cramer_validations))

    # LKT_TND_CRAMER_QUERY_SERVICE
    api = CramerAPIs[prod][0]
    if api:
        lkt = LookupTable('LKT_TND_CRAMER_QUERY_SERVICE')
        lkt.add(LtEntry(prod+"#API_NAME", api))
        rfsparam = config.find_return_param('{}_RFS_NAME'.format(prod))
        inputparams = {rfsparam.jsonname: rfsparam.name}
        DBG(30, "Input parameters for query API are: {}".format(inputparams))
        lkt.add(LtEntry(prod+"#PARAMETERS", ";".join("{}={}".format(*it) for it in inputparams.items())+";"))
        returnparams = {p.jsonname: p.name for p in config.input_params + config.cramer_output_params if p.jsonname is not None}
        DBG(30, "Return parameters for query API are: {}".format(returnparams))
        lkt.add(LtEntry(prod+"#RETURN_PARAMETERS", ",".join("{}:{}".format(k, re.sub(r'\<N\>$','',v)) for k,v in sorted(returnparams.items()))))
        gereturnparams =  set(p.name for p in config.input_params + config.cramer_output_params if p.cramerStorage == config.factoryProductName+"_GE")
        DBG(30, "Return GE parameters for query API are: {}".format(gereturnparams))
        lkt.add(LtEntry(prod+"#RETURN_GE_PARAMETERS", ";".join(sorted(gereturnparams))+";"))

    else:
        print("No query function defined for product {}".format(prod))
        lkt = None
    tables.append(lkt)

    # LKT_TND_CRAMER_IDENTIFY_SERVICE
    api = CramerAPIs[prod][1]
    if api:
        lkt = LookupTable('LKT_TND_CRAMER_IDENTIFY_SERVICE')
        lkt.add(LtEntry(prod+"#API_NAME", api))
        inputparams = {p.jsonname: p.name for p in config.input_params if p.jsonname is not None}
        DBG(30, "Input parameters for identify API are: {}".format(inputparams))
        lkt.add(LtEntry(prod+"#PARAMETERS", ";".join("{}={}".format(*it) for it in inputparams.items())+";"))
        lkt.add(LtEntry(prod+"#GE_PARAMETERS", joinparams([p for p in config.input_params if p.cramerStorage == config.factoryProductName+"_GE"])))
        returnparams = {"serviceFound": "SERVICE_FOUND"}
        returnparams.update({p.jsonname: p.name for p in config.cramer_output_params if p.jsonname is not None})
        DBG(30, "Return parameters for identify API are: {}".format(returnparams))
        lkt.add(LtEntry(prod+"#RETURN_PARAMETERS", ",".join("{}:{}".format(k,re.sub(r'\<N\>$','',v)) for k,v in returnparams.items())))
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
    for tr in MODIFY_OPS:
        if tr in {p.modifyOperation for p in config.input_params}:
            params = [p for p in config.input_params if p.modifyOperation == tr and p.cramerStorage == config.factoryProductName+"_GE"]
            if params:
                lkt.add(LtEntry(prod+"#"+tr+"#PARAMETERS", joinparams(params)))
                lkt.add(LtEntry(prod+"#"+tr+"#GE_PARAMETERS", joinparams(params)))
    tables.append(lkt)

    # LKT_TND_STABLENET
    TRANSACTIONS = {"Create": "new_rfs",
                    "Delete": "cease_rfs",
                    "Compare": "compare_rfs",
                    "ModifyParameter": "modify_rfs_generic",
                    "ModifyCustomSnippets": "modify_rfs_custom_snippets",
                    "ModifyQoS": "modify_rfs_qos",
                    "ModifySubnets": "modify_rfs_ip_subnets",
                    "ModifyVlan": "modify_rfs_vlan",
                    "AddMemberLinks": "placeholder_add_member_links",
                    "RemoveMemberLinks": "placeholder_remove_member_links"}
    supported_transactions = {"Create", "Delete", "Compare"}.union({p.modifyOperation for p in config.input_params})
    if prod in ["PHY_ILAG", "PHY_ESILAG"]:
        supported_transactions.add("AddMemberLinks")
        supported_transactions.add("RemoveMemberLinks")

    lkt = LookupTable('LKT_TND_STABLENET')
    for trans, orderdesc in TRANSACTIONS.items():
        if trans in supported_transactions:
            lkt.add(LtEntry(prod+"#"+trans+"#ORDER_DESCRIPTION", orderdesc))
            lkt.add(LtEntry(prod+"#"+trans+"#TARGET_DEVICE", nenameparam))
            lkt.add(LtEntry(prod+"#"+trans+"#RFS_NAME", config.factoryProductName+"_RFS_NAME"))
            parameters = config.stablenet_params[0]
            lkt.add(LtEntry(prod+"#"+trans+"#PARAMETERS", ";".join(parameters)+";"))
    tables.append(lkt)

    return tables

def create_kv(cfs, component, fpname, paramdata):
    pname, ptype = (paramdata[x] for x in ["name", "type"])
    key = "#".join([cfs, component, fpname, "Create", pname])
    DBG(30, "Key is {}".format(key))
    if ptype == "static":
        values = (str(paramdata["value"]).replace('*', '\\*').replace('"', '*') if paramdata["value"] is not None else "<NULL>", "S")
    elif ptype in ["input", "mapped"]:
        values = (paramdata["from"], "D")
    DBG(30, "Values are {}".format(values))
    return key, values


def create_lookup_tables_for_composition(data):
    ''' Create the lookup Tables '''
    if data["compositionType"] == "cfs":
        cfs = data["compositionName"]
        component = ""
    else:
        component = data["compositionName"]
        cfs = ""

    lkt1 = LookupTable('LKT_TND_STATIC_PARAM_VALUES')
    for fpdata in data["paramMapping"]:
        fpname = fpdata["factoryProduct"]
        for paramdata in fpdata["parameters"]:
            key, values = create_kv(cfs, component, fpname, paramdata)
            lkt1.add(LtEntry(key, *values))
    if cfs and "componentOverrides" in data:
        for compoverride in data["componentOverrides"]:
            component = compoverride["componentName"]
            for fpdata in compoverride["overrides"]:
                fpname = fpdata["factoryProduct"]
                for paramdata in fpdata["parameters"]:
                    key, values = create_kv(cfs, component, fpname, paramdata)
                    lkt1.add(LtEntry(key, *values))

    DISPLAY_PARAM_BLACKLIST = ["EVPN_EVI_RANGE"]
    lkt2 = LookupTable('LKT_TND_DISPLAY_PARAMETERS')
    for fpdata in data["paramMapping"]:
        fpname = fpdata["factoryProduct"]
        rfsname = {"name": "{}_RFS_NAME".format(fpname),
                   "type": "input",
                   "from": "{}_{}_RFS_NAME".format(component, fpname) if component else "{}_RFS_NAME".format(fpname)}
        parameters = []
        for paramdata in [rfsname] + fpdata["parameters"]:
            pname, ptype = (paramdata[x] for x in ["name", "type"])
            if pname not in DISPLAY_PARAM_BLACKLIST:
                key = "#".join([cfs, component, fpname, "Display", pname])
                DBG(30, "Key is {}".format(key))
                if ptype == "input":
                    values = paramdata["from"]
                    DBG(30, "Values are {}".format(values))
                    lkt2.add(LtEntry(key, values))
                    parameters.append(pname)
        lkt2.add(LtEntry("#".join([cfs, component, fpname, "Display", "Parameters"]), ";".join(parameters)+ ";"))

    return [lkt1, lkt2]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-D', dest='dbglevel', action='store', default=10,    help='Print Debug information')
    parser.add_argument('-o', dest='outfile', metavar='<OUTPUT_FILE>', help='Name of the output file (overrides default name)')
    parser.add_argument('-d', dest='targetdir', metavar='<TARGET_DIR>', help='Save to directory rather than creating zipfile')
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
            if args.targetdir:
                create_update_files_in_targetdir(args.targetdir, *tables)
            else:
                outfile = "{}.zip".format(config.factoryProductName) if args.outfile is None else args.outfile
                create_zipfile(outfile, *tables)
                print(outfile)
        elif "compositionName" in jsondata:
            tables = create_lookup_tables_for_composition(jsondata)
            for table in tables:
                DBG(30, "Lookup Table dump:\n"+table.debugdump())
            if args.targetdir:
                create_update_files_in_targetdir(args.targetdir, *tables)
            else:
                outfile = "{}.zip".format(jsondata["compositionName"]) if args.outfile is None else args.outfile
                create_zipfile(outfile, *tables)
                print(outfile)

