#!/usr/bin/python3
import argparse
import re
import sys
import json
from zipfile import ZipFile
from collections import namedtuple
from openpyxl import load_workbook
from lookuptable import LookupTable, LtEntry

from debug import DBG, set_debug_level

CFS_COMPONENT_MAPPING = {
    "TN_RBH_RPD_ACCESS": ["RBH_RPD"],
    "TN_RBH_CMTS_ACCESS": ["RBH_CMTS"],
    "TN_RBH_CMTS_CORE": ["RBH_CMTS_INET", "RBH_CMTS_ABR_MC"],
    "TN_B2C_OLT_ACCESS": ["RTL_PROV", "RTL_MGT", "RTL_INET", "RTL_VOIP", "INF_DHCPTRAFFIC", "INF_MGT", "RTL_IPTV", "RTL_CGN"],
    "TN_B2C_XDSLAM_ACCESS": ["RTL_PROV", "RTL_MGT", "RTL_INET", "RTL_VOIP", "INF_DHCPTRAFFIC", "INF_MGT", "RTL_IPTV", "RTL_CGN"],
    "TN_CMTS_ACCESS": ["RBH_CMTS_INET", "RBH_CMTS_ABR_MC"],
}

def read_data_from_sheet(sheet, col1, col2, cfsname, componentname, fpname):
    STARTROW = 7
    AMBIGUOUS = ["CUST_SNIPPET_NAMES"] # Parameters which can have different values for different FPs

    rv = []
    for row in range(STARTROW, 300):
        cellvalues = [sheet.cell(row=row, column=col).value for col in [1, 3, 4, col1, col2]]
        techname, valuetype, valuedetails, paramtype, paramdetails = (x.strip() if isinstance(x, str) else x for x in cellvalues)
        if techname == "Version": # avoid reading version history
            break
        if sheet.cell(row=row, column=1).font.strike:
            DBG(20, "Ignoring parameter {} because of strikethough formatting".format(techname))
            continue
        if techname and paramtype and techname != "NETWORK_ELEMENT_NAME":
            if paramtype == 'input':
                if techname in AMBIGUOUS:
                    if cfsname:
                        input_param = "{}_{}".format(fpname, techname)
                    else:
                        input_param = "{}_{}_{}".format(componentname, fpname, techname)
                else:
                    if cfsname:
                        input_param = "{}".format(techname)
                    else:
                        input_param = "{}_{}".format(componentname, techname)
                rv.append({"name": techname, "type": "input", "from": input_param})
            elif paramtype == 'static value':
                if valuetype == "Enumerated" and paramdetails not in [x.strip() for x in valuedetails.split(";")]:
                    print("Warning: Value '{}' for parameter {} is not a valid enum value.".format(paramdetails, techname))
                if valuetype == "Integer" and not isinstance(paramdetails, int):
                    print("Warning: Value '{}' for parameter {} is not a valid integer.".format(paramdetails, techname))
                rv.append({"name": techname, "type": "static", "value": paramdetails})
            elif paramtype == 'static "null"':
                rv.append({"name": techname, "type": "static", "value": None})
            elif paramtype == 'mapped':
                rv.append({"name": techname, "type": "mapped", "from": paramdetails})
            elif paramtype == 'n/a':
                pass
            else:
                print("Warning: Invalid value '{}' for parameter {}".format(paramtype, techname))
    return rv



def read_data_from_excel(xlfile, cfsname, componentname):
    ''' Read and return the data from the correct sheet in the excel file.'''
    PRODNAME_CELL = 'B1'
    VERSION_CELL = 'B4'

    HEADERROW = 5 # Row that contains the Component/CFS names

    DBG(10, "Reading data from excel file '{}'".format(xlfile))
    wb = load_workbook(xlfile, data_only=True)
    rv = []
    for tab in wb.sheetnames:
        if re.match(r'[A-Z_]*', tab):
            DBG(20, "Checking tab {}".format(tab))
            sheet = wb[tab]

            prodname = sheet[PRODNAME_CELL].value
            if not prodname:
                raise ValueError("Unable to read product name from excel {}, tab {}, cell {}".format(xlfile, tab, PRODNAME_CELL))
            version = sheet[VERSION_CELL].value

            for col in range(1,60):
                cellval = sheet.cell(row=HEADERROW, column=col).value
                if  (componentname and cellval == componentname) or (cfsname and cellval == "CFS " + cfsname):
                    col1, col2 = col, col+1
                    DBG(10, "Reading parameters for product {} version {} from tab {}, columns {},{}".format(prodname, version, tab, col1, col2))
                    data = read_data_from_sheet(sheet, col1, col2, cfsname, componentname, prodname)
                    rv.append({"factoryProduct": prodname, "factoryProductVersion": str(version), "parameters": data})
                    break
    
    return rv





if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-D', dest='dbglevel', action='store', default=10,    help='Print Debug information')
    parser.add_argument('-o', dest='outfile', metavar='<OUTPUT_FILE>', help='Name of the output file (overrides default name)')
    parser.add_argument('filename', metavar='<FILENAME>', help='Excel input file')
    parser.add_argument('composite', metavar='<COMPOSITE>', nargs='+', help='CFS or Component name for which to extract data')

    args=parser.parse_args()
    set_debug_level(args.dbglevel)

    for composite in args.composite:
        if composite.startswith("TN_"):
            cfsname = composite
            componentname = None
        else:
            componentname = composite
            cfsname = None

        jsondata = {"compositionName": composite, "compositionType": "cfs" if cfsname else "component"}
        if cfsname:
            jsondata["includedComponents"] = CFS_COMPONENT_MAPPING.get(cfsname, [])
        jsondata["paramMapping"] = read_data_from_excel(args.filename, cfsname, componentname)

        outfile = "{}_{}.json".format("CFS" if cfsname else "Component", composite) if args.outfile is None else args.outfile
        DBG(10, "Writing json file '{}'".format(outfile))
        with open(outfile, "w", newline='\n') as fp:
            json.dump(jsondata, fp, indent=2)
