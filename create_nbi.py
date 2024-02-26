#!/usr/bin/python3
import argparse

from factoryproduct import FactoryProductConfiguration
from debug import DBG, set_debug_level

def create_confluence_table_create(productconfig : FactoryProductConfiguration, headers=True):
    if headers:
        print("h3. {}".format('Create (Action "Create")'))
    print("||Parameter name (without prefix)||Section||Description||Example Value||M/O/C||")
    print("|EXTERNAL_ORDER_ID|General|Reference to the order number. Generated by the northbound system.|O00324572912|M|")
    print("|PAUSE_AFTER_PREPARE|Order Line|Whether a manual task should be created in Order Hub at the end of Prepare phase (true) or the whole flow should be executed as one (false).|false|M|")
    for param in productconfig.input_params:
        print("|{}|Order Line|{}|{}|{}|".format(param.name, param.desc, param.examplevalue, "M" if param.mandatory else "O"))
    print("\nReturn Parameters:")
    print("||Parameter name||Description||Example Value||")
    for param in productconfig.cramer_output_params:
        pname = param.name if param.name.startswith(productconfig.factoryProductName) else "{}_{}".format(productconfig.factoryProductName, param.name)
        print("|{}|{}|{}|".format(pname, param.desc, param.examplevalue))
    print()

def create_confluence_table_delete(productconfig : FactoryProductConfiguration, headers=True):
    rfsnameparam = "{}_RFS_NAME".format(productconfig.factoryProductName)
    rfsnameexample = productconfig.find_return_param(rfsnameparam).examplevalue
    if headers:
        print("h3. {}".format('Delete (Action "Delete")'))
    print("||Parameter name (without prefix)||Section||Description||Example Value||M/O/C||")
    print("|EXTERNAL_ORDER_ID|General|Reference to the order number. Generated by the northbound system.|O00324572912|M|")
    print("|PAUSE_AFTER_PREPARE|Order Line|Whether a manual task should be created in Order Hub at the end of Prepare phase (true) or the whole flow should be executed as one (false).|false|M|")
    print("|{}|Order Line|The Cramer RFS Name of the service to be deleted.|{}|M|".format(rfsnameparam, rfsnameexample))
    print("\nThere are no return parameters for this action.")
    print()

def create_confluence_table_modifyParameter(productconfig : FactoryProductConfiguration, headers=True):
    rfsnameparam = "{}_RFS_NAME".format(productconfig.factoryProductName)
    rfsnameexample = productconfig.find_return_param(rfsnameparam).examplevalue
    gename = "{}_GE".format(productconfig.factoryProductName)
    if headers:
        print("h3. {}".format('Modify Parameter (Action "ModifyParameter")'))
    print("||Parameter name (without prefix)||Section||Description||Example Value||M/O/C||")
    print("|EXTERNAL_ORDER_ID|General|Reference to the order number. Generated by the northbound system.|O00324572912|M|")
    print("|PAUSE_AFTER_PREPARE|Order Line|Whether a manual task should be created in Order Hub at the end of Prepare phase (true) or the whole flow should be executed as one (false).|false|M|")
    print("|{}|Order Line|The Cramer RFS Name of the service to be modified.|{}|M|".format(rfsnameparam, rfsnameexample))
    for param in productconfig.input_params + productconfig.cramer_output_params:
        if param.cramerStorage == gename and not param.name.startswith("QOS"):
            print("|{}|Order Line|{}|{}|{}|".format(param.name, param.desc, param.examplevalue, "O"))
    print("\nThere are no return parameters for this action.")
    print()

def create_confluence_table_modifyQoS(productconfig : FactoryProductConfiguration, headers=True):
    for param in productconfig.input_params + productconfig.cramer_output_params:
        if param.name.startswith("QOS"):
            break
    else:
        return
    rfsnameparam = "{}_RFS_NAME".format(productconfig.factoryProductName)
    rfsnameexample = productconfig.find_return_param(rfsnameparam).examplevalue
    gename = "{}_GE".format(productconfig.factoryProductName)
    if headers:
        print("h3. {}".format('Modify QoS (Action "ModifyQoS")'))
    print("||Parameter name (without prefix)||Section||Description||Example Value||M/O/C||")
    print("|EXTERNAL_ORDER_ID|General|Reference to the order number. Generated by the northbound system.|O00324572912|M|")
    print("|PAUSE_AFTER_PREPARE|Order Line|Whether a manual task should be created in Order Hub at the end of Prepare phase (true) or the whole flow should be executed as one (false).|false|M|")
    print("|{}|Order Line|The Cramer RFS Name of the service to be modified.|{}|M|".format(rfsnameparam, rfsnameexample))
    for param in productconfig.input_params + productconfig.cramer_output_params:
        if param.cramerStorage == gename and param.name.startswith("QOS"):
            print("|{}|Order Line|{}|{}|{}|".format(param.name, param.desc, param.examplevalue, "O"))
    print("\nThere are no return parameters for this action.")
    print()

def create_confluence_table_display(productconfig : FactoryProductConfiguration, headers=True):
    rfsnameparam = "{}_RFS_NAME".format(productconfig.factoryProductName)
    rfsnameexample = productconfig.find_return_param(rfsnameparam).examplevalue
    if headers:
        print("h3. {}".format('Display (Action "Display")'))
    print("||Parameter name (without prefix)||Section||Description||Example Value||M/O/C||")
    print("|EXTERNAL_ORDER_ID|General|Reference to the order number. Generated by the northbound system.|O00324572912|M|")
    print("|{}|Order Line|The Cramer RFS Name of the service to be modified.|{}|M|".format(rfsnameparam, rfsnameexample))
    print("\nReturn Parameters:")
    print("||Parameter name||Description||Example Value||")
    for param in productconfig.input_params + productconfig.cramer_output_params:
        pname = param.name if param.name.startswith(productconfig.factoryProductName) else "{}_{}".format(productconfig.factoryProductName, param.name)
        print("|{}|{}|{}|".format(pname, param.desc, param.examplevalue))
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-D', dest='dbglevel', action='store', default=0,    help='Print Debug information')
    parser.add_argument('-a', dest='action', action='store',                 help='Only product NBI for action')
    parser.add_argument('filename', metavar='<FILENAME>', nargs="*",         help='JSON input files')

    args=parser.parse_args()
    set_debug_level(args.dbglevel)

    for f in args.filename:
        DBG(10, "Reading json file '{}'".format(f))
        with open(f, "r") as fp:
            config = FactoryProductConfiguration.from_file(fp)
        print("h2. Factory Product {}".format(config.factoryProductName))
        create_confluence_table_create(config, True)
        create_confluence_table_delete(config, True)
        create_confluence_table_modifyParameter(config, True)
        create_confluence_table_modifyQoS(config, True)
        create_confluence_table_display(config, True)
