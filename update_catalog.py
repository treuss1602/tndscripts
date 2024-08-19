#!/usr/bin/python
import argparse
import re
import time
import xml.etree.ElementTree as ET
from debug import DBG, set_debug_level

ns = { 'i':'http://schemas.comptel.com/wsdl/comptel/catalog/internal/', 'xsi' : "http://www.w3.org/2001/XMLSchema-instance" }
timestamp = str(int(1000*time.time()))

def incr_version(v):
    ''' Increase a string like "4.3" to "4.4" '''
    m = re.match(r"(.*\.)(\d*)", v)
    return m.group(1) + str(int(m.group(2))+1)

def updateItem(itemname, itemxml, required_updates):
    embitems = itemxml.find('i:embeddedItems', ns)
    updates = set()
    if embitems is None:
        DBG(20, "No <embeddedItems> tag inside item {}".format(itemname))
    else:
        for it in embitems.findall('i:embeddedItem', ns):
            if it.attrib["name"] in required_updates and it.attrib["version"] != required_updates[it.attrib["name"]][0]:
                DBG(10, "Updating instance {} inside {} from version {} to version {}".format(it.attrib["instanceName"], itemname, it.attrib["version"], required_updates[it.attrib["name"]][0]))
                it.attrib["version"] = required_updates[it.attrib["name"]][0]
                updates.add((it.attrib["name"], required_updates[it.attrib["name"]][0]))
            elif it.attrib["name"] in required_updates:
                DBG(10, "Instance {} inside {} is already on version {}".format(it.attrib["instanceName"], itemname, it.attrib["version"]))
    if updates:
        DBG(20, "Version for item {} needs to be increased.".format(itemname))
        oldversion = itemxml.attrib["version"]
        newversion = incr_version(oldversion)
        required_updates[itemname] = (newversion, None)
        DBG(10, "Increasing version for {} from {} to {}".format(itemname, oldversion, newversion))
        itemxml.attrib["version"] = newversion
        itemxml.attrib["description"] = "Updated " +", ".join("{} to v{}".format(i, v) for (i,v) in updates)
        itemxml.attrib["lastChangedTimestamp"] = timestamp


def update_xml(xml, required_updates):
    ''' Read initial item definitions from XML '''
    rv = []
    port = xml.find('i:port', ns)
    if port is None:
        raise RuntimeError("No <port> tag inside XML root")
    items = port.find('i:items', ns)
    if items is None:
        raise RuntimeError("No <items> tag inside <port>")
    for item in items.findall('i:item', ns):
        itemname = item.attrib["name"]
        itemversion = item.attrib["version"]
        DBG(20, "Found item {} version {}".format(itemname, itemversion))
        if itemname in required_updates:
            DBG(20, "Found entry for {}, version {}".format(itemname, itemversion))
            if itemversion != required_updates[itemname][0] and required_updates[itemname][1] is not None:
                DBG(10, "Replacing item {} with version {} from RFS file".format(itemname, required_updates[itemname][0]))
                rv.append(required_updates[itemname][1])
            else:
                rv.append(item)
        else:
            updateItem(itemname, item, required_updates)
            rv.append(item)
    items.clear()
    items.extend(rv)
    return rv


def read_rfs(filename, prefix, replace_all):
    rv = {}
    xml = ET.parse(filename)
    port = xml.find('i:port', ns)
    if port is None:
        raise RuntimeError("No <port> tag inside XML root")
    items = port.find('i:items', ns)
    if items is None:
        raise RuntimeError("No <items> tag inside <port>")
    for item in items.findall('i:item', ns):
        itemname = item.attrib["name"]
        itemversion = item.attrib["version"]
        DBG(20, "RFS contains item {} version {}".format(itemname, itemversion))
        if replace_all or itemname.startswith(prefix):
            rv[itemname] = (itemversion, item)
    return rv



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Update Catalogs with new RFS')
    parser.add_argument('filename', metavar='<FILENAME>', help='The Catalog export XML of the product to be updated')
    parser.add_argument('rfsfile', metavar='<RFSFILE>',   help='The Catalog export XML of the latest version of the RFS')
    parser.add_argument('-o', dest='outfile', action='store',  help='Write output to file instead of stdout')
    parser.add_argument('-a', dest='repl_all', action='store_true',  help='Replace all items (also TLs) with ones from RFS, not only specific ones')
    parser.add_argument('-p', dest='prefix', action='store', default="RFS_", help='Replace items with <prefix> with ones from RFS. Default is "RFS_"')
    parser.add_argument('-D', dest='dbglevel', action='store', default=0, help='Print Debug information')

    args = parser.parse_args()
    set_debug_level(args.dbglevel)

    required_updates = read_rfs(args.rfsfile, args.prefix, args.repl_all)

    xml = ET.parse(args.filename)
    items = update_xml(xml, required_updates)

    ET.register_namespace('', 'http://schemas.comptel.com/wsdl/comptel/catalog/internal/')
    if (args.outfile):
        xml.write(args.outfile, encoding='UTF-8', xml_declaration=True)
    else:
        print(ET.tostring(xml.getroot(), encoding='UTF-8', xml_declaration=True).decode('UTF-8'))

