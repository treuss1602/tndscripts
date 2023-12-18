#!/usr/bin/python3
import argparse
import re
from zipfile import ZipFile
from collections import namedtuple
from openpyxl import load_workbook

from factoryproduct import Param, FactoryProductConfiguration
from debug import DBG, set_debug_level

def read_data_from_excel(xlfile, tab):
    ''' Read and return the data from the correct sheet in the excel file.'''
    STARTROW = 6
    COLUMNS = {'TECHNAME': 1, 'DESC': 2, 'VALUETYPE': 3, 'TYPEDETAILS': 4, 'OM': 5, 'EXAMPLE_VALUE': 6, 'CRAMERSTORAGE': 7, 'PARAMTYPE': 8, 'ACADEFAULT': 10 }
    PRODNAME_CELL = 'B1'
    ACTION_CELL = 'B3'
    VERSION_CELL = 'B4'

    DBG(10, "Reading data from excel file '{}'".format(xlfile))
    wb = load_workbook(xlfile, data_only=True)
    if tab is None:
        sheet = wb.active
        tab = sheet.title
        print("WARNING: No parameter given for <TABNAME>. Reading active tab '{}'".format(tab))
    else:
        DBG(10, "Reading tab '{}'".format(tab))
        try:
            sheet = wb[tab]
        except KeyError:
            tabs = ", ".join("'"+t+"'" for t in wb.sheetnames)
            raise KeyError("Invalid tab name '{}'. Available tabs are: {}".format(tab, tabs))

    prodname = sheet[PRODNAME_CELL].value
    if not prodname:
        raise ValueError("Unable to read product name from excel {}, tab {}, cell {}".format(xlfile, tab, PRODNAME_CELL))
    action = sheet[ACTION_CELL].value
    if not action:
        raise ValueError("Unable to read action from excel {}, tab {}, cell {}".format(xlfile, tab, ACTION_CELL))
    version = sheet[VERSION_CELL].value
    inparams = []
    crameroutparams = []
    for row in range(STARTROW, 300):
        cellvalues = [sheet.cell(row=row, column=col).value for col in [COLUMNS[s]
            for s in ['TECHNAME','DESC','VALUETYPE','TYPEDETAILS','OM','EXAMPLE_VALUE','PARAMTYPE', 'ACADEFAULT', 'CRAMERSTORAGE']]]
        techname, desc, valuetype, typedetails, mo, example, paramtype, acadefault, cramerstorage = (x.strip() if isinstance(x, str) else x for x in cellvalues)
        if techname == "Version": # avoid reading version history
            break
        if techname and valuetype and mo and paramtype:
            if sheet.cell(row=row, column=1).font.strike:
                DBG(10, "Ignoring parameter {} because of strikethough formatting".format(techname))
                continue
            # Check for arrays
            m = re.match(r'(.*)\[\d+\.\.(\d+)\]', valuetype)
            if m is not None:
                valuetype = m.group(1)
                maxoccurs = int(m.group(2))
            else:
                maxoccurs = None
            if paramtype.lower() == "input" or paramtype.lower() == "special":
                DBG(30, "Adding parameter {} (type {}) to input parameters".format(techname, paramtype))
                inparams.append(Param('input', techname, desc, valuetype, typedetails, mo.upper() == "M", example, cramerstorage, acadefault, paramtype.lower() == "special", maxoccurs))
            elif paramtype.lower() == "return":
                DBG(30, "Adding parameter {} (type {}) to cramer output parameters".format(techname, paramtype))
                crameroutparams.append(Param('Cramer', techname, desc, valuetype, typedetails, mo.upper() == "M", example, cramerstorage, maxoccurs=maxoccurs))
            elif paramtype.lower() == "inputorreturn":
                DBG(30, "Adding parameter {} (type {}) to input AND cramer output parameters".format(techname, paramtype))
                inparams.append(Param('input', techname, desc, valuetype, typedetails, mo.upper() == "M", example, cramerstorage, acadefault, paramtype.lower() == "special", maxoccurs))
                crameroutparams.append(Param('Cramer', techname, desc, valuetype, typedetails, mo.upper() == "M", example, cramerstorage, maxoccurs=maxoccurs))
            else:
                DBG(30, "Ignoring parameter {} (type {})".format(techname, paramtype))

    return prodname, action, version, inparams, crameroutparams

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-D', dest='dbglevel', action='store', default=10,    help='Print Debug information')
    parser.add_argument('-t', dest='tabname', metavar='<TABNAME>', help='Excel tab read')
    parser.add_argument('-n', dest='nename', metavar='<NENAME_PARAM>', default='NETWORK_ELEMENT_NAME', help='Name of the parameter to be used for network element')
    parser.add_argument('-o', dest='outfile', metavar='<OUTPUT_FILE>', help='Name of the output file (overrides default name)')
    parser.add_argument('filename', metavar='<FILENAME>', help='Excel input file')

    args=parser.parse_args()
    set_debug_level(args.dbglevel)

    prodname, transaction, version, inparams, crameroutparams = read_data_from_excel(args.filename, args.tabname)
    config = FactoryProductConfiguration(prodname, transaction, version, inparams, crameroutparams)
    config.add_validation("CHECK_NODE_LOCATION", args.nename, taskname="CHECK_TARGET_NE_EXISTS")
    if "ACCESS_DEVICE_NAME" in config.input_param_names():
        config.add_validation("CHECK_NODE_LOCATION", "ACCESS_DEVICE_NAME", taskname="CHECK_ACCESS_DEVICE_EXISTS")
    outfile = "{}_{}.json".format(prodname, transaction) if args.outfile is None else args.outfile
    DBG(10, "Writing json file '{}'".format(outfile))
    with open(outfile, "w") as fp:
        config.to_file(fp)
