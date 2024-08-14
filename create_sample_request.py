#!/usr/bin/python3
import argparse
import json
import uuid

from factoryproduct import FactoryProductConfiguration
from soaws import CreateRequest, OrderLine
from debug import DBG, set_debug_level

def create_sample_request(productconfig : FactoryProductConfiguration, orderno = None, replyto_address = None, mandatory_only = True, soaws_py_syntax = False):
    if orderno is None:
        if soaws_py_syntax:
            orderno = '${uuid}'
            externalOrderId = '${orderNo}'
        else:
            orderno = str(uuid.uuid4())
            externalOrderId = orderno
    req = CreateRequest(ilReqGroup="TND", orderNo=orderno, replyToAddress=replyto_address)
    req.add_parameter("ORDER_EXTERNAL_ORDER_ID", externalOrderId)
    ol = OrderLine("OL_1", "FACTORY_PRODUCT_{}".format(productconfig.factoryProductName), "Create")
    if not mandatory_only:
        ol.add_parameter("PAUSE_AFTER_PREPARE", "true")
        ol.add_parameter("SKIP_PROVISIONING", "false")
    for p in productconfig.input_params:
        if p.mandatory or not mandatory_only:
            if p.examplevalue is not None:
                DBG(30, "Adding parameter {} to request.".format(p.name))
                pname = p.name if "<N>" not in p.name else p.name.replace("<N>", "1")
                ol.add_parameter(pname, p.examplevalue)
            else:
                DBG(10, "Skipping parameter {}. No example value in input file.".format(p.name))
    req.add_orderline(ol)
    return req

def create_cfs_sample_request(cfsname, parameters, orderno = None, replyto_address = None, mandatory_only = True, soaws_py_syntax = False):
    if orderno is None:
        if soaws_py_syntax:
            orderno = '${uuid}'
            externalOrderId = '${orderNo}'
        else:
            orderno = str(uuid.uuid4())
            externalOrderId = orderno
    req = CreateRequest(ilReqGroup="TND", orderNo=orderno, replyToAddress=replyto_address)
    req.add_parameter("ORDER_EXTERNAL_ORDER_ID", externalOrderId)
    ol = OrderLine("OL_1", "PRODUCT_{}".format(cfsname), "Create")
    ol.add_parameter("NETWORK_ELEMENT_NAME", "ZH0004MEB101")
    if not mandatory_only:
        ol.add_parameter("PAUSE_AFTER_PREPARE", "true")
        ol.add_parameter("SKIP_PROVISIONING", "false")
    for p in parameters:
        if p[3] or not mandatory_only:
            if p[2] is not None:
                DBG(30, "Adding parameter {} to request.".format(p[0]))
                pname = p[0] if "<N>" not in p[0] else p[0].replace("<N>", "1")
                ol.add_parameter(pname, p[2])
            else:
                DBG(10, "Skipping parameter {}. No example value in input file.".format(p[0]))
    req.add_orderline(ol)
    return req



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-D', dest='dbglevel', action='store', default=10,    help='Print Debug information')
    parser.add_argument('-o', dest='outfile', metavar='<OUTPUT_FILE>', help='Save request to <OUTPUT_FILE>')
    parser.add_argument('-O', dest='orderNo', metavar='<ORDER_NO>', help='Use <ORDER_NO> as orderNo and EXTERNAL_ORDER_ID.')
    parser.add_argument('-R', dest='replyAddress', metavar='<REPLY_TO_ADDRESS>', help='Add <REPLY_TO_ADDRESS> to request header.')
    parser.add_argument('-m', dest='mandatory_only', action='store_true', help='Create request with mandatory parameters only.')
    parser.add_argument('-s', dest='soaws_py', action='store_true', help='Generate request with syntax used by soaws.py')
    parser.add_argument('filename', metavar='<FILENAME>', help='JSON input file.')

    args=parser.parse_args()
    set_debug_level(args.dbglevel)

    DBG(10, "Reading json file '{}'".format(args.filename))
    with open(args.filename, "r") as fp:
        jsondata = json.load(fp)
    if "factoryProductName" in jsondata:
        config = FactoryProductConfiguration.from_jsondata(jsondata)
        req = create_sample_request(config, orderno=args.orderNo, replyto_address=args.replyAddress, mandatory_only=args.mandatory_only, soaws_py_syntax=args.soaws_py)
        if args.outfile:
            with open(args.outfile, "w") as fp:
                fp.write(req.xml())
        else:
            print(req.xml())
    elif "compositionName" in jsondata:
        config = jsondata
        cfsname = config["compositionName"]
        inputparams = [(p["from"], p["name"], fp["factoryProduct"]) for fp in config["paramMapping"] for p in fp["parameters"] if p["type"] == "input"]
        if "includedComponents" in config:
            for component in config["includedComponents"]:
                component_definition_filename = "Component_{}.json".format(component)
                DBG(10, "Loading additional json file '{}'".format(component_definition_filename))
                with open (component_definition_filename, "r") as f:
                    comp_config = json.load(f)
                    inputparams += [(p["from"], p["name"], fp["factoryProduct"]) for fp in comp_config["paramMapping"] for p in fp["parameters"] if p["type"] == "input"]
        fps = {p[2] for p in inputparams}
        paramdetails = {}
        for fp in fps:
            fp_definition_filename = "FP_{}.json".format(fp)
            DBG(10, "Loading additional json file '{}'".format(fp_definition_filename))
            try:
                with open(fp_definition_filename, "r") as f:
                    config = FactoryProductConfiguration.from_file(f)
                for p in filter(lambda p: p[2] == fp, inputparams):
                    pdetails = config.find_input_param(p[1])
                    paramdetails[p[0]] = (pdetails.desc, pdetails.examplevalue, "M" if pdetails.mandatory else "O")
            except Exception as e:
                print("WARNING: Unable to extract information for factory product {}. JSON File missing?".format(fp))
                raise(e)
            
        req = create_cfs_sample_request(cfsname, [(p[0], *paramdetails[p[0]]) for p in inputparams], mandatory_only=args.mandatory_only)
        if args.outfile:
            with open(args.outfile, "w") as fp:
                fp.write(req.xml())
        else:
            print(req.xml())

        



