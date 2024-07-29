#!/usr/bin/python3
import argparse
import json

from factoryproduct import FactoryProductConfiguration
from debug import DBG, set_debug_level

def get_sample_rfs_name(fpname):
    prefixes = {"PHY_SINGLE_LINK": "PHYSL",
                "PHY_ESILAG": "PHYELAG",
                "IPVPN_CORE": "IVC",
                "ELAN_CORE": "ELANC"
                }
    try:
        return "{}000000001".format(prefixes[fpname])
    except KeyError:
        return "{}000000001".format(fpname.replace("_",""))

def quote(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace('\n', '<br/>')

def tableheader(*values, widths=None):
    if widths is None:
        return '<tr>' + ''.join('<th class="confluenceTh"><p>'+quote(s)+'</p></th>' for s in values) + '</tr>'
    else:
        return '<tr>' + ''.join('<th class="confluenceTh" width="{}px"><p>'.format(w)+quote(s)+'</p></th>' for s,w in zip(values, widths)) + '</tr>'

def tablerow(*values, alignments=None):
    if alignments is None:
        return '<tr>' + ''.join('<td class="confluenceTd"><p>'+quote(s)+'</p></td>' for s in values) + '</tr>'
    else:
        return '<tr>' + ''.join('<td class="confluenceTd"{}><p>'.format(' style="text-align:{};"'.format(a) if a else '')+quote(s)+'</p></td>' for s,a in zip(values, alignments)) + '</tr>'

def create_confluence_html_section(heading, name, action, headerparams, inputparams, outputparams):
    IWIDTHS = [400, 90, 340, 300, 70]
    IALIGNS = [None, None, None, None, "center"]
    OWIDTHS = [400, 500, 300]
    print('<h2 id="CFS{}-{}">{}</h2>'.format(name, heading.replace(" ",""), heading))
    print('<p>Below order parameters are applicable for orders with LINE_x_NAME=PRODUCT_{} and LINE_x_ACTION={}</p>'.format(name, action))
    print('<div class="table-wrap"><table class="confluenceTable"><tbody>')
    print(tableheader("Parameter name (without prefix)", "Section", "Description", "Example Value", "M/O/C", widths=IWIDTHS))
    # print(tablerow("EXTERNAL_ORDER_ID", "General", "Reference to the order number. Generated by the northbound system.", "O00324572912", "M", alignments=IALIGNS))
    # if action != "Display":
    #     print(tablerow("PAUSE_AFTER_PREPARE", "Order Line", "Whether a manual task should be created in Order Hub at the end of Prepare phase (true) or the whole flow should be executed as one (false).\nDefault is true", "false", "O", alignments=IALIGNS))
    # if action == "Create":
    #     print(tablerow("SKIP_PROVISIONING", "Order Line", "Whether the flow should skip Provision and Finalize phases. This should only be true if there is a master flow that will execute the Provision flow separately.\nDefault is false", "true", "O", alignments=IALIGNS))
    #     print(tablerow("CRAMER_CONTEXT_ID", "Id of an existing context in Cramer. If given, no separate context will be created.", "Create-b992005a-abfbe1-91918", "O"))
    # elif action == "Delete":
    #     print(tablerow("SKIP_PROVISIONING", "Order Line", "Whether the flow should skip Provision and Finalize phases. This should only be true if there is a master flow that will execute the Deprovision flow separately.\nDefault is false", "true", "O", alignments=IALIGNS))
    #     print(tablerow("CRAMER_CONTEXT_ID", "Id of an existing context in Cramer. If given, no separate context will be created.", "Cease-b992005a-abfbe1-91918", "O"))
    for param in headerparams:
        print(tablerow(*param, alignments=IALIGNS))
    for param in inputparams:
        print(tablerow(param[0], "Order Line", *param[1:4], alignments=IALIGNS))
    print('</tbody></table></div>')
    if outputparams:
        print('<p>Return Parameters:</p>')
        print('<div class="table-wrap"><table class="confluenceTable"><tbody>')
        print(tableheader("Parameter name", "Description", "Example Value", widths=OWIDTHS))
        for param in outputparams:
            print(tablerow(*param[:3]))
        print('</tbody></table></div>')
    else:
        print("<p>There are no return parameters for this action.</p>")
    print()

BASEPARAMS = {
    "Create": [
        ("EXTERNAL_ORDER_ID", "General", "Reference to the order number. Generated by the northbound system.", "O00324572912", "M"),
        ("PAUSE_AFTER_PREPARE", "Order Line", "Whether a manual task should be created in Order Hub at the end of Prepare phase (true) or the whole flow should be executed as one (false).\nDefault is true", "false", "O"),
        ("SKIP_PROVISIONING", "Order Line", "Whether the flow should skip Provision and Finalize phases. This should only be true if there is a master flow that will execute the Provision flow separately.\nDefault is false", "true", "O"),
        ("CRAMER_CONTEXT_ID", "Order Line", "Id of an existing context in Cramer. If given, no separate context will be created.", "Create-b992005a-abfbe1-91918", "O"),
        ("APPLY_CONTEXT", "Order Line", "Whether or not the context shall be applied in Cramer in the Finalize phase.\nDefault is true", "false", "O"),
    ],
    "Delete": [
        ("EXTERNAL_ORDER_ID", "General", "Reference to the order number. Generated by the northbound system.", "O00324572912", "M"),
        ("PAUSE_AFTER_PREPARE", "Order Line", "Whether a manual task should be created in Order Hub at the end of Prepare phase (true) or the whole flow should be executed as one (false).\nDefault is true", "false", "O"),
        ("SKIP_PROVISIONING", "Order Line", "Whether the flow should skip Provision and Finalize phases. This should only be true if there is a master flow that will execute the Deprovision flow separately.\nDefault is false", "true", "O"),
        ("CRAMER_CONTEXT_ID", "Order Line", "Id of an existing context in Cramer. If given, no separate context will be created.", "Cease-b992005a-abfbe1-91918", "O"),
        ("APPLY_CONTEXT", "Order Line", "Whether or not the context shall be applied in Cramer in the Finalize phase.\nDefault is true", "false", "O"),
    ],
    "Display": [
        ("EXTERNAL_ORDER_ID", "General", "Reference to the order number. Generated by the northbound system.", "O00324572912", "M"),
    ],
    "Provision": [
        ("EXTERNAL_ORDER_ID", "General", "Reference to the order number. Generated by the northbound system.", "O00324572912", "M"),
        ("CRAMER_CONTEXT_ID", "Order Line", "Id of an existing context in Cramer.", "Create-b992005a-abfbe1-91918", "M"),
        ("APPLY_CONTEXT", "Order Line", "Whether or not the context shall be applied in Cramer in the Finalize phase.\nDefault is true", "false", "O"),
    ],
    "Deprovision": [
        ("EXTERNAL_ORDER_ID", "General", "Reference to the order number. Generated by the northbound system.", "O00324572912", "M"),
        ("CRAMER_CONTEXT_ID", "Order Line", "Id of an existing context in Cramer.", "Cease-b992005a-abfbe1-91918", "M"),
        ("APPLY_CONTEXT", "Order Line", "Whether or not the context shall be applied in Cramer in the Finalize phase.\nDefault is true", "false", "O"),
    ],
    "RemoveModelling": [
        ("EXTERNAL_ORDER_ID", "General", "Reference to the order number. Generated by the northbound system.", "O00324572912", "M"),
    ],

}



def create_confluence_html(cfsname, input_parameters, display_parameters, fpversions):
    samplename = "{}000000001".format(cfsname)
    print("<p>NBI Specification for {}, based on the following factory product versions in the Parameter Excel Sheet.</p>".format(cfsname))
    print("<ul>")
    for fpname, fpversion in fpversions.items():
        print("<li>{} version {}</li>".format(fpname, fpversion))
    print("</ul>")
    neparam = ('NETWORK_ELEMENT_NAME', 'The network element on which to provsion the CFS.', 'ZH0004MEB101', 'M')
    cfsparam = ("CFS_NAME", "Name of the CFS as generated by Cramer", samplename, 'M')
    create_confluence_html_section("Create", cfsname, "Create", BASEPARAMS["Create"], [neparam]+input_parameters, [cfsparam])
    create_confluence_html_section("Delete", cfsname, "Delete", BASEPARAMS["Delete"], [cfsparam], [])
    create_confluence_html_section("Display", cfsname, "Display", BASEPARAMS["Display"], [cfsparam], [neparam] + display_parameters)
    create_confluence_html_section("Provision", cfsname, "Provision", BASEPARAMS["Provision"], [cfsparam], [])
    create_confluence_html_section("Deprovision", cfsname, "Deprovision", BASEPARAMS["Deprovision"], [cfsparam], [])
    create_confluence_html_section("Remove Modelling (Undo of Create with SKIP_PROVISIONING=true)", cfsname, "RemoveModelling", BASEPARAMS["RemoveModelling"], [cfsparam], [])



def create_confluence_table(cfsname, input_parameters, display_parameters, header=True, fpversions=None):
    samplename = "{}000000001".format(cfsname)
    if header:
        print("NBI Specification for {}, based on the following factory product versions in the Parameter Excel Sheet.".format(cfsname))
        for fpname, fpversion in fpversions.items():
            print("- {} version {}".format(fpname, fpversion))
        print()
    # Create
    print("h2. Create")
    print("||Parameter name (without prefix)||Section||Description||Example Value||M/O/C||")
    print("|EXTERNAL_ORDER_ID|General|Reference to the order number. Generated by the northbound system.|O00324572912|M|")
    print("|NETWORK_ELEMENT_NAME|Order Line|The network element on which to provsion the CFS.|ZH0004MEB101|M|")
    print("|PAUSE_AFTER_PREPARE|Order Line|Whether a manual task should be created in Order Hub at the end of Prepare phase (true) or the whole flow should be executed as one (false).|true|M|")
    print("|SKIP_PROVISIONING|Order Line|Whether the flow should skip Provision and Finalize phases. This should only be true if there is a master flow that will execute the Provision flow separately.|false|M|")
    for param in input_parameters:
        print("|{}|Order Line|{}|{}|{}|".format(*param))
    print("Return Parameters:")
    print("||Parameter name (without prefix)||Description||Example Value||")
    print("|CFS_NAME|Name of the CFS as generated by Cramer|{}|".format(samplename))
    print("|CRAMER_CONTEXT_ID|Context-Id, generated by Cramer, under which the modelling is done in Cramer.|Create-b992005a-abfbe1-90633|".format(samplename))
    # Delete
    print("h2. Delete")
    print("||Parameter name (without prefix)||Section||Description||Example Value||M/O/C||")
    print("|EXTERNAL_ORDER_ID|General|Reference to the order number. Generated by the northbound system.|O00324572912|M|")
    print("|PAUSE_AFTER_PREPARE|Order Line|Whether a manual task should be created in Order Hub at the end of Prepare phase (true) or the whole flow should be executed as one (false).|true|M|")
    print("|SKIP_PROVISIONING|Order Line|Whether the flow should skip Provision and Finalize phases. This should only be true if there is a master flow that will execute the Deprovision flow separately.|false|M|")
    print("|CFS_NAME|Order Line|Name of the CFS as given by Cramer.|{}|M|".format(samplename))
    print("Return Parameters:")
    print("|CRAMER_CONTEXT_ID|Context-Id, generated by Cramer, under which the changes are done in Cramer.|Delete-b992005a-abfbe1-90633|".format(samplename))
    # Display
    print("h2. Display")
    print("||Parameter name (without prefix)||Section||Description||Example Value||M/O/C||")
    print("|EXTERNAL_ORDER_ID|General|Reference to the order number. Generated by the northbound system.|O00324572912|M|")
    print("|CFS_NAME|Order Line|Name of the CFS as given by Cramer.|{}|M|".format(samplename))
    print("Return Parameters:")
    print("||Parameter name (without prefix)||Description||Example Value||")
    print("|NETWORK_ELEMENT_NAME|The network element on which to provsion the CFS.|ZH0004MEB101|")
    for param in display_parameters:
        print("|{}|{}|{}|".format(param[0], param[1], param[2]))


def extract_parameters(config):
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-D', dest='dbglevel', action='store', default=0,    help='Print Debug information')
    parser.add_argument('-H', dest='headers', action='store_true',           help='Include headers (default if multiple files are given)')
    parser.add_argument('-x', dest='html', action='store_true',              help='Output html instead of markup')
    parser.add_argument('filename', metavar='<FILENAME>',                    help='JSON input file')

    args=parser.parse_args()
    set_debug_level(args.dbglevel)

    cfsname = None
    DBG(10, "Reading json file '{}'".format(args.filename))
    with open(args.filename, "r") as fp:
        config = json.load(fp)
    if cfsname is None:
        cfsname = config["compositionName"]
    paramdetails = {}
    fpversions = {fp["factoryProduct"]: fp["factoryProductVersion"] for fp in config["paramMapping"]}
    for fp in config["paramMapping"]:
        inputparams = [(p["from"], p["name"], fp["factoryProduct"]) for p in fp["parameters"] if p["type"] == "input"]
        displayparams = [("{}_RFS_NAME".format(fp["factoryProduct"]), fp["factoryProduct"]),
                         ("{}_PROVISION_STATUS".format(fp["factoryProduct"]), fp["factoryProduct"])] + [(t[0],t[2]) for t in inputparams]
        paramdetails["{}_RFS_NAME".format(fp["factoryProduct"])] = ("Name of the RFS of the {} service as given by Cramer.".format(fp["factoryProduct"]), get_sample_rfs_name(fp["factoryProduct"]), "M")
        paramdetails["{}_PROVISION_STATUS".format(fp["factoryProduct"])] = ("Provision Status of the {} service in Cramer.".format(fp["factoryProduct"]), "SERVICE - ACTIVE", "M")
    DBG(10, paramdetails)
    if "includedComponents" in config:
        for component in config["includedComponents"]:
            component_definition_filename = "Component_{}.json".format(component)
            DBG(10, "Loading additional json file '{}'".format(component_definition_filename))
            with open (component_definition_filename, "r") as f:
                comp_config = json.load(f)
                fpversions.update({fp["factoryProduct"]: fp["factoryProductVersion"] for fp in comp_config["paramMapping"]})
                for fp in comp_config["paramMapping"] :
                    inputparams += [(p["from"], p["name"], fp["factoryProduct"]) for p in fp["parameters"] if p["type"] == "input"]
                    displayparams += [("{}_{}_RFS_NAME".format(component, fp["factoryProduct"]), fp["factoryProduct"])]
                    displayparams += [("{}_{}_PROVISION_STATUS".format(component, fp["factoryProduct"]), fp["factoryProduct"])]
                    displayparams += [(p["from"], fp["factoryProduct"]) for p in fp["parameters"] if p["type"] == "input"]
                    paramdetails["{}_{}_RFS_NAME".format(component, fp["factoryProduct"])] = ("Name of the RFS of the {} service (part of the {} component) as given by Cramer.".format(fp["factoryProduct"], component), get_sample_rfs_name(fp["factoryProduct"]), "M")
                    paramdetails["{}_{}_PROVISION_STATUS".format(component, fp["factoryProduct"])] = ("Provision Status of the {} service (part of the {} component) in Cramer.".format(fp["factoryProduct"], component), "SERVICE - ACTIVE", "M")
    DBG(10, "Display Params: {}".format(displayparams))
    fps = {p[2] for p in inputparams}
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

    if args.html:
        create_confluence_html(cfsname, [(p[0], *paramdetails[p[0]]) for p in inputparams], [(p[0], *paramdetails[p[0]]) for p in displayparams], fpversions)
    else:
        create_confluence_table(cfsname, [(p[0], *paramdetails[p[0]]) for p in inputparams], [(p[0], *paramdetails[p[0]]) for p in displayparams], True, fpversions)
