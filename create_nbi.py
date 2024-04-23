#!/usr/bin/python3
import argparse

from debug import DBG, set_debug_level
from factoryproduct import FactoryProductConfiguration, Param

def tableheader(*values):
    return '<tr>' + ''.join('<th class="confluenceTh"><p>'+str(s)+'</p></th>' for s in values) + '</tr>'

def tablerow(*values):
    return '<tr>' + ''.join('<td class="confluenceTd"><p>'+str(s)+'</p></td>' for s in values) + '</tr>'

def create_confluence_html(heading, name, action, inputparams, outputparams):
    print('<h2 id="FactoryProduct{}-{}">{}</h2>'.format(name, heading.replace(" ",""), heading))
    print('<p>Below order parameters are applicable for orders with LINE_x_NAME=FACTORY_PRODUCT_{} and LINE_x_ACTION={}</p>'.format(name, action))
    print('<div class="table-wrap"><table class="confluenceTable"><tbody>')
    print(tableheader("Parameter name (without prefix)", "Section", "Description", "Example Value", "M/O/C"))
    print(tablerow("EXTERNAL_ORDER_ID", "General", "Reference to the order number. Generated by the northbound system.", "O00324572912", "M"))
    if action != "Display":
        print(tablerow("PAUSE_AFTER_PREPARE", "Order Line", "Whether a manual task should be created in Order Hub at the end of Prepare phase (true) or the whole flow should be executed as one (false).", "false", "M"))
    for param in inputparams:
        print(tablerow(param.name, "Order Line", param.desc, param.examplevalue, "M" if param.mandatory else "O"))
    print('</tbody></table></div>')
    if outputparams:
        print('<p>Return Parameters:</p>')
        print('<div class="table-wrap"><table class="confluenceTable"><tbody>')
        print(tableheader("Parameter name", "Description", "Example Value"))
        for param in outputparams:
            pname = param.name if param.name.startswith(name) else "{}_{}".format(name, param.name)
            print(tablerow(pname, param.desc, param.examplevalue))
        print('</tbody></table></div>')
    else:
        print("<p>There are no return parameters for this action.</p>")
    print()

def create_confluence_markup(heading, name, action, inputparams, outputparams):
    print("h2. {}".format(heading))
    print("Below order parameters are applicable for orders with LINE_x_NAME=FACTORY_PRODUCT_{} and LINE_x_ACTION={}".format(name, action))
    print("||Parameter name (without prefix)||Section||Description||Example Value||M/O/C||")
    print("|EXTERNAL_ORDER_ID|General|Reference to the order number. Generated by the northbound system.|O00324572912|M|")
    if action != "Display":
        print("|PAUSE_AFTER_PREPARE|Order Line|Whether a manual task should be created in Order Hub at the end of Prepare phase (true) or the whole flow should be executed as one (false).|false|M|")
    for param in inputparams:
        print("|{}|Order Line|{}|{}|{}|".format(param.name, param.desc, param.examplevalue, "M" if param.mandatory else "O"))
    if outputparams:
        print("\nReturn Parameters:")
        print("||Parameter name||Description||Example Value||")
        for param in outputparams:
            pname = param.name if param.name.startswith(name) else "{}_{}".format(name, param.name)
            print("|{}|{}|{}|".format(pname, param.desc, param.examplevalue))
    else:
        print("\nThere are no return parameters for this action.")
    print()


def create_confluence_table_create(productconfig: FactoryProductConfiguration, headers=True, html=False):
    if html:
        create_confluence_html("Create", productconfig.factoryProductName, "Create", productconfig.input_params, productconfig.cramer_output_params)
    else:
        create_confluence_markup("Create", productconfig.factoryProductName, "Create", productconfig.input_params, productconfig.cramer_output_params)

def create_confluence_table_delete(productconfig: FactoryProductConfiguration, headers=True, html=False):
    rfsnameparam = "{}_RFS_NAME".format(productconfig.factoryProductName)
    rfsnameexample = productconfig.find_return_param(rfsnameparam).examplevalue
    if html:
        create_confluence_html("Delete", productconfig.factoryProductName, "Delete",
                                [Param("input", rfsnameparam, "The Cramer RFS Name of the service to be deleted.", "String", "", True, rfsnameexample)],
                                [])
    else:
        create_confluence_markup("Delete", productconfig.factoryProductName, "Delete",
                        [Param("input", rfsnameparam, "The Cramer RFS Name of the service to be deleted.", "String", "", True, rfsnameexample)],
                        [])

def create_confluence_table_modify(productconfig: FactoryProductConfiguration, action: str, title: str, headers=True, html=False):
    rfsnameparam = "{}_RFS_NAME".format(productconfig.factoryProductName)
    rfsnameexample = productconfig.find_return_param(rfsnameparam).examplevalue
    inparams = [Param("input", rfsnameparam, "The Cramer RFS Name of the service to be modified.", "String", "", True, rfsnameexample)]
    for param in productconfig.input_params:
        if param.modifyOperation == action:
            desc = "New value for the parameter. If the parameter is not provided, it will remain unchanged."
            if not param.mandatory:
                desc += '\nIf the parameter is to be cleared, the string "\\_\\_NULL\\_\\_" is sent as value.'
            example = param.examplevalue
            if not param.mandatory:
                example = example + '\nor\n\\_\\_NULL\\_\\_' if example else "\\_\\_NULL\\_\\_"
            inparams.append(Param("input", param.name, desc, "String", "", False, example))
    if html:
        create_confluence_html(title, productconfig.factoryProductName, action, inparams, [])
    else:
        create_confluence_markup(title, productconfig.factoryProductName, action, inparams, [])

def create_confluence_table_display(productconfig : FactoryProductConfiguration, headers=True, html=False):
    rfsnameparam = "{}_RFS_NAME".format(productconfig.factoryProductName)
    rfsnameexample = productconfig.find_return_param(rfsnameparam).examplevalue
    inparams = [Param("input", rfsnameparam, "The Cramer RFS Name of the service to be displayed.", "String", "", True, rfsnameexample)]
    outparams = []
    for param in productconfig.input_params + productconfig.cramer_output_params:
        pname = param.name if param.name.startswith(productconfig.factoryProductName) else "{}_{}".format(productconfig.factoryProductName, param.name)
        outparams.append(Param("output", pname, param.desc, "", "", True, param.examplevalue))
    if html:
        create_confluence_html("Display", productconfig.factoryProductName, "Display", inparams, outparams)
    else:
        create_confluence_markup("Display", productconfig.factoryProductName, "Display", inparams, outparams)

def print_confluence_markup_header(config, supported_modify_ops):
    print("NBI Specification for {}, based on version {} of the Parameter Excel Sheet.".format(config.factoryProductName, config.version))
    print("Supported actions:")
    for (action, title) in [("Create", "Create"), ("Delete", "Delete")] + supported_modify_ops + [("Display", "Display")]:
        print("* [{}|#{}]".format(title, title))
    print()

def print_confluence_html_header(config, supported_modify_ops):
    print('<p>NBI Specification for {}, based on version {} of the Parameter Excel Sheet.</p>'.format(config.factoryProductName, config.version))
    print('<p>Supported actions:</p>')
    print('<ul>')
    for (action, title) in [("Create", "Create"), ("Delete", "Delete")] + supported_modify_ops + [("Display", "Display")]:
        print('<li><a href="#FactoryProduct{}-{}">{}</a></li>'.format(config.factoryProductName, title.replace(" ",""), title))
    print('</ul>')




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-D', dest='dbglevel', action='store', default=0,    help='Print Debug information')
    parser.add_argument('-a', dest='action', action='store',                 help='Only product NBI for action')
    parser.add_argument('-x', dest='html', action='store_true',             help='Output html instead of markup')
    parser.add_argument('filename', metavar='<FILENAME>', nargs="*",         help='JSON input files')

    args=parser.parse_args()
    set_debug_level(args.dbglevel)

    MODIFY_OPS =[("ModifyParameter", "Generic Modify"),
                 ("ModifyCustomSnippets", "Modify Custom Snippets"),
                 ("ModifyQoS", "Modify QoS"),
                 ("ModifySubnets", "Modify IP Subnets"),
                 ("ModifyVLAN", "Modify VLAN")]

    for f in args.filename:
        DBG(10, "Reading json file '{}'".format(f))
        with open(f, "r") as fp:
            config = FactoryProductConfiguration.from_file(fp)
        supported_modify_ops = [(action, title) for (action, title) in MODIFY_OPS if action in [p.modifyOperation for p in config.input_params]]
        if args.html:
            print_confluence_html_header(config, supported_modify_ops)
        else:
            print_confluence_markup_header(config, supported_modify_ops)

        create_confluence_table_create(config, True, html=args.html)
        create_confluence_table_delete(config, True, html=args.html)
        for action, title in supported_modify_ops:
            create_confluence_table_modify(config, action, title, True, html=args.html)
        create_confluence_table_display(config, True, html=args.html)
