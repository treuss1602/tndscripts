#!/usr/bin/python3
import argparse
import json

from factoryproduct import FactoryProductConfiguration
from debug import DBG, set_debug_level
from collections import namedtuple
from flowcharts import CFS, Component, FactoryProduct, Task, Phase

class ExtraTasks:

    def __init__(self, *, at_start=None, at_end=None, after=None):
        self.at_start = at_start if at_start is not None else []
        self.at_end = at_end if at_end is not None else []
        self.after = after if after is not None else {}

def quote(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

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

def describe_flow(cfs, structure, action, cfstasks, componenttasks, *, reverse=False, empty_phases=[], rollback=True):
    rfslink = f"[the generic RFS {action} flow|\\[TND\\] (F1) Process Flows - Factory Products RFS generic flow#{action}]"
    enumerations = [list(range(1,30)), "abcdefghijklmnop", ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x"]]
    rbtasks = []
    ijk = [0, None, None]
    print(f"h1. {action}")
    print(f"The following describes the {action} {cfs} flow:\n")
    for phase in ["Validate", "Prepare", "Provision", "Finalize"]:
        if phase in empty_phases:
            print(f"# {phase} phase (empty)")
        else:
            last_component = None
            cfs_ptasks = cfstasks.get(phase, ExtraTasks())
            print(f"# {phase} phase")
            ijk = [ijk[0], 0, None]
            for ptask in cfs_ptasks.at_start:
                print(f"## {ptask[0]}")
                rbtasks.append((ijk.copy(), ptask))
                ijk[1] += 1
            for element in reversed(structure) if reverse else structure:
                if isinstance(element, str):
                    print(f"## Execute {phase} phase for the {element} factory product RFS (Cf. {rfslink})")
                    ijk[1] += 1
                    for ptask in cfs_ptasks.after.get(element, []):
                        print(f"## {ptask[0]}")
                        rbtasks.append((ijk.copy(), ptask))
                        ijk[1] += 1
                elif isinstance(element, tuple):
                    component, subelements = element
                    if last_component is not None and subelements == last_component[1]:
                        print(f"## Execute {phase} phase for the {component} component (same tasks as for {last_component[0]})")
                        ijk[1] += 1
                    else:
                        print(f"## Execute {phase} phase for the {component} component")
                        ijk = [ijk[0], ijk[1], 0]
                        ctasks = componenttasks[component].get(phase, ExtraTasks())
                        for ctask in ctasks.at_start:
                            print(f"### {ctask[0]}")
                            rbtasks.append((ijk.copy(), ctask))
                            ijk[2] += 1
                        for subelement in reversed(subelements) if reverse else subelements:
                            print(f"### Execute {phase} phase for the {subelement} factory product RFS (Cf. {rfslink})")
                            ijk[2] += 1
                        for ctask in ctasks.at_end:
                            print(f"### {ctask[0]}")
                            rbtasks.append((ijk.copy(), ctask))
                            ijk[2] += 1
                        ijk = [ijk[0], ijk[1]+1, None]
                        for ptask in cfs_ptasks.after.get(component, []):
                            print(f"## {ptask[0]}")
                            rbtasks.append((ijk.copy(), ptask))
                            ijk[2] += 1
                        last_component = element
            for ptask in cfs_ptasks.at_end:
                print(f"## {ptask[0]}") 
                rbtasks.append((ijk.copy(), ptask))
                ijk[1] += 1
        ijk = [ijk[0]+1, None, None]

    print("\nVisual representation of the flow:")
    print("!{}_{}.png|width=1200!".format(cfs, action))
    print("\nh3. Rollback\n")
    if rollback:
        rows = [item for item in reversed(rbtasks) if len(item[1]) == 3]
        if rows:
            print("In addition to the rollback tasks described for the Factory Product RFS, the following additional tasks can be rolled back:")
            print("||Create Task||Rollback Task||")
            for ijk, task in rows:
                enumval = [enumerations[i][ijk[i]] for i in range(3) if ijk[i] is not None]
                print('|{} {}|{}|'.format(".".join(str(e) for e in enumval), task[0], task[2]))
        else:
            print("In addition to the rollback tasks described for the Factory Product RFS, there are no additional rollback tasks.")
    else:
        print("Rollback is not supported by this flow.")





def create_drawing(cfsname, structure, action, cfstasks, componenttasks, *, reverse=False, empty_phases=[]):

    phases = {s: Phase(s, empty=s in empty_phases) for s in ["Validate", "Prepare", "Provision", "Finalize"]}
    lc = "Prepare" in empty_phases

    cfs = CFS("CFS {} - {}".format(cfsname, action), phases.values())

    for phase, tasks in cfstasks.items():
        for ptask in tasks.at_start:
            if ptask[1]:
                cfs.embed(Task(ptask[1], phases[phase]))
    last_component = None
    for element in reversed(structure) if reverse else structure:
        if isinstance(element, str):
            cfs.embed(FactoryProduct("FP {}".format(element), lowcaption=lc))
            for phase, tasks in cfstasks.items():
                for ptask in tasks.after.get(element, []):
                    if ptask[1]:
                        cfs.embed(Task(ptask[1], phases[phase]))
        elif isinstance(element, tuple):
            component, subelements = element
            if last_component is not None and subelements == last_component[1]:
                comp = Component("Component {}".format(component), last_component[0], lowcaption=lc)
                #print(f"## Execute {phase} phase for the {component} component (same tasks as for {last_component[0]})")
            else:
                comp = Component("Component {}".format(component))
                for phase, tasks in componenttasks[component].items():
                    for ptask in tasks.at_start:
                        if ptask[1]:
                            comp.embed(Task(ptask[1], phases[phase]))
                for subelement in reversed(subelements) if reverse else subelements:
                    comp.embed(FactoryProduct("FP {}".format(subelement), lowcaption=lc))
                for phase, tasks in componenttasks[component].items():
                    for ptask in tasks.at_end:
                        if ptask[1]:
                            comp.embed(Task(ptask[1], phases[phase]))
                for phase, tasks in cfstasks.items():
                    for ptask in tasks.after.get(component, []):
                        if ptask[1]:
                            cfs.embed(Task(ptask[1], phases[phase]))
                last_component = element
            cfs.embed(comp)
    for phase, tasks in cfstasks.items():
        for ptask in tasks.at_end:
            if ptask[1]:
                cfs.embed(Task(ptask[1], phases[phase]))

    out = cfs.createImage()
    filename = "{}_{}.png".format(cfsname, action)
    DBG(10, "Generating file {}".format(filename))
    out.save(filename)

def create_output(cfs, structure, action, cfstasks, comptasks, create_graphic, *, reverse=False, empty_phases=[]):
    if create_graphic:
        create_drawing(cfs, structure, action, cfstasks, comptasks, reverse=reverse, empty_phases=empty_phases)
    else:
        describe_flow(cfs, structure, action, cfstasks, comptasks, reverse=reverse, empty_phases=empty_phases)


def create_flow(cfs, structure, create_graphic=False):
    createContext =   (r'[Create a "context" in Cramer|\[TND\] (F1) Cramer APIs#Create Context]',
                       'Cramer\nCreate Context',
                       r'[Rollback the "context" in Cramer|\[TND\] (F1) Cramer APIs#Rollback Context]')
    createCFS     =   (r'[Create a CFS in Cramer|\[TND\] (F1) Cramer APIs#Create CFS]',
                       'Cramer\nCreate CFS Service',
                       r'[Remove the CFS|\[TND\] (F1) Cramer APIs#Remove CFS]')
    createIRB     =   (r'[Find or Create an IRB Service|\[TND\] (F1) Cramer APIs#Find or Create IRB Service]',
                       'Cramer\nFind Or Create IRB')
    createComponent = (r'[Create a Component Service in Cramer|\[TND\] (F1) Cramer APIs#Create Component]',
                       'Cramer\nCreate Component Service',
                       r'[Remove the Component Service|\[TND\] (F1) Cramer APIs#Remove Component]')
    generateL2Name =  (r'[Query location name from Cramer|\[TND\] (F1) Cramer APIs#Query Location Name of a Node] and generate L2_VPN_NAME as {}_L2_<LOCATION_NAME>',
                       'Cramer\nCreate L2 VPN Name')
    skipProvsioning = (r'If order line parameter SKIP_PROVISIONING is true, skip remaining steps (Provision and Finalize phase)',
                       None)
    pauseAfterPrepare = (r'If order line parameter PAUSE_AFTER_PREPARE is true: [Create a manual task to await confirmation that the provisioning can be started|\[TND\] (F1) Internal Libraries#Create a manual task to await confirmation that the provisioning can be started]',
                         'Order Hub\nConfirm Modelling')
    applyContext  =   (r'[Apply the "context" in Cramer|\[TND\] (F1) Cramer APIs#Apply Context]',
                       'Cramer\nApply Context')
    ponr = ('PONR', 'PONR')

    cfstasks = {"Prepare": ExtraTasks(at_start=[createContext, createCFS], at_end=[skipProvsioning], after={'PHY_SINGLE_LINK': [createIRB], 'PHY_ESILAG': [createIRB]} ),
                "Provision": ExtraTasks(at_start=[pauseAfterPrepare], at_end=[ponr]),
                "Finalize": ExtraTasks(at_end=[applyContext])}
    comptasks = {}
    for compname, items in [c for c in structure if isinstance(c, tuple)]:
        if "ELAN_CORE" in items:
            comptasks[compname] = {"Prepare": ExtraTasks(at_start=[createComponent, (generateL2Name[0].format(compname), generateL2Name[1])])}
        else:
            comptasks[compname] = {"Prepare": ExtraTasks(at_start=[createComponent])}
    create_output(cfs, structure, "Create", cfstasks, comptasks, create_graphic)

def delete_flow(cfs, structure, create_graphic=False):
    queryCFS = (r'[Query Child Services of the '+cfs+r' CFS from Cramer|\[TND\] (F1) Cramer APIs#Query Service Decomposition]',
                "Cramer\nQuery CFS Decomposition")
    queryComponent = (r'[Query Child Services of the {} component from Cramer|\[TND\] (F1) Cramer APIs#Query Service Decomposition]',
                      "Cramer\nQuery Component Decomposition")
    createContext =   (r'[Create a "context" in Cramer|\[TND\] (F1) Cramer APIs#Create Context]',
                       "Cramer\nCreate Context",
                       r'[Rollback the "context" in Cramer|\[TND\] (F1) Cramer APIs#Rollback Context]')
    updateCFSPS = (r'[Update Provision Status of CFS to "SERVICE - PLANNED CEASE"|\[TND\] (F1) Cramer APIs#Update Provision Status of Service]',
                   "Cramer\nSet CFS to \"Planned Cease\"",
                   r'[Update Provision Status of CFS to "SERVICE - ACTIVE"|\[TND\] (F1) Cramer APIs#Update Provision Status of Service]')
    updateCompPS = (r'[Update Provision Status of Component to "SERVICE - PLANNED CEASE"|\[TND\] (F1) Cramer APIs#Update Provision Status of Service]',
                    "Cramer\nSet Component to \"Planned Cease\"",
                    r'[Update Provision Status of Component to "SERVICE - ACTIVE"|\[TND\] (F1) Cramer APIs#Update Provision Status of Service]')
    deleteCFS     =   (r'[Delete the CFS in Cramer|\[TND\] (F1) Cramer APIs#Delete CFS]',
                       "Cramer\nDelete CFS")
    deleteComponent = (r'[Delete the Component in Cramer|\[TND\] (F1) Cramer APIs#Delete Component]',
                       "Cramer\nDelete Component")
    skipProvsioning = (r'If order line parameter SKIP_PROVISIONING is true, skip remaining steps (Provision and Finalize phase)',
                       None)
    pauseAfterPrepare = (r'If order line parameter PAUSE_AFTER_PREPARE is true: [Create a manual task to await confirmation that the provisioning can be started|\[TND\] (F1) Internal Libraries#Create a manual task to await confirmation that the provisioning can be started]',
                         'Order Hub\nConfirm Modelling')
    applyContext  =   (r'[Apply the "context" in Cramer|\[TND\] (F1) Cramer APIs#Apply Context]',
                       'Cramer\nApply Context')
    ponr = ('PONR', 'PONR')

    cfstasks = {"Validate": ExtraTasks(at_start=[queryCFS]),
                "Prepare": ExtraTasks(at_start=[createContext, updateCFSPS], at_end=[skipProvsioning]),
                "Provision": ExtraTasks(at_start=[pauseAfterPrepare, ponr]),
                "Finalize": ExtraTasks(at_end=[deleteCFS, applyContext])}
    comptasks = {}
    for compname, items in [c for c in structure if isinstance(c, tuple)]:
        comptasks[compname] = {"Validate": ExtraTasks(at_start=[(queryComponent[0].format(compname), queryComponent[1])]),
                                "Prepare": ExtraTasks(at_start=[updateCompPS]),
                                "Finalize": ExtraTasks(at_end=[deleteComponent])}

    create_output(cfs, structure, "Delete", cfstasks, comptasks, create_graphic, reverse=True)


def provision_flow(cfs, structure, create_graphic=False):
    queryCFS = (r'[Query Child Services of the '+cfs+r' CFS from Cramer|\[TND\] (F1) Cramer APIs#Query Service Decomposition]',
                "Cramer\nQuery CFS Decomposition")
    queryComponent = (r'[Query Child Services of the {} component from Cramer|\[TND\] (F1) Cramer APIs#Query Service Decomposition]',
                      "Cramer\nQuery Component Decomposition")
    applyContext  =   (r'[Apply the "context" in Cramer|\[TND\] (F1) Cramer APIs#Apply Context]',
                       'Cramer\nApply Context')

    cfstasks = {"Validate": ExtraTasks(at_start=[queryCFS]),
                "Finalize": ExtraTasks(at_end=[applyContext])}
    comptasks = {}
    for compname, items in [c for c in structure if isinstance(c, tuple)]:
        comptasks[compname] = {"Validate": ExtraTasks(at_start=[(queryComponent[0].format(compname), queryComponent[1])])}
    
    create_output(cfs, structure, "Provision", cfstasks, comptasks, create_graphic, empty_phases=["Prepare"])

def deprovision_flow(cfs, structure, create_graphic=False):
    queryCFS = (r'[Query Child Services of the '+cfs+r' CFS from Cramer|\[TND\] (F1) Cramer APIs#Query Service Decomposition]',
                "Cramer\nQuery CFS Decomposition")
    queryComponent = (r'[Query Child Services of the {} component from Cramer|\[TND\] (F1) Cramer APIs#Query Service Decomposition]',
                      "Cramer\nQuery Component Decomposition")
    deleteCFS     =   (r'[Delete the CFS in Cramer|\[TND\] (F1) Cramer APIs#Delete CFS]',
                       "Cramer\nDelete CFS")
    deleteComponent = (r'[Delete the Component in Cramer|\[TND\] (F1) Cramer APIs#Delete Component]',
                       "Cramer\nDelete Component")
    applyContext  =   (r'[Apply the "context" in Cramer|\[TND\] (F1) Cramer APIs#Apply Context]',
                       'Cramer\nApply Context')

    cfstasks = {"Validate": ExtraTasks(at_start=[queryCFS]),
                "Finalize": ExtraTasks(at_end=[deleteCFS, applyContext])}
    comptasks = {}
    for compname, items in [c for c in structure if isinstance(c, tuple)]:
        comptasks[compname] = {"Validate": ExtraTasks(at_start=[(queryComponent[0].format(compname), queryComponent[1])]),
                               "Finalize": ExtraTasks(at_end=[deleteComponent])}

    create_output(cfs, structure, "Deprovision", cfstasks, comptasks, create_graphic, reverse=True, empty_phases=["Prepare"])

def remove_modelling_flow(cfs, structure, create_graphic=False):
    queryCFS = (r'[Query Child Services of the '+cfs+r' CFS from Cramer|\[TND\] (F1) Cramer APIs#Query Service Decomposition]',
                "Cramer\nQuery CFS Decomposition")
    queryComponent = (r'[Query Child Services of the {} component from Cramer|\[TND\] (F1) Cramer APIs#Query Service Decomposition]',
                      "Cramer\nQuery Component Decomposition")
    deleteCFS     =   (r'[Delete the CFS in Cramer|\[TND\] (F1) Cramer APIs#Delete CFS]',
                       "Cramer\nDelete CFS")
    deleteComponent = (r'[Delete the Component in Cramer|\[TND\] (F1) Cramer APIs#Delete Component]',
                       "Cramer\nDelete Component")
    rollbackContext = (r'[Rollback the "context" in Cramer|\[TND\] (F1) Cramer APIs#Rollback Context]',
                       "Cramer\nRollback Context")

    cfstasks = {"Validate": ExtraTasks(at_start=[queryCFS]),
                "Finalize": ExtraTasks(at_end=[deleteCFS, rollbackContext])}
    comptasks = {}
    for compname, items in [c for c in structure if isinstance(c, tuple)]:
        comptasks[compname] = {"Validate": ExtraTasks(at_start=[(queryComponent[0].format(compname), queryComponent[1])]),
                                "Finalize": ExtraTasks(at_end=[deleteComponent])}

    create_output(cfs, structure, "RemoveModelling", cfstasks, comptasks, create_graphic, reverse=True, empty_phases=["Provision"])

def explain_structure(cfs, structure):
    print("h1. CFS Structure")
    print(f"The CFS {cfs} (Catalog item PRODUCT_{cfs}) consists of ", end="")
    fps = [it for it in structure if isinstance(it, str)]
    if len(fps) > 1:
        print("the factory products "+", ".join(fps[:-1])+" and "+fps[-1]+" ", end="")
    elif len(fps) == 1:
        print("the factory product "+fps[0]+" ", end="")
    components = [it[0] for it in structure if isinstance(it, tuple)]
    if fps and components:
        print("and ", end="")
    if len(components) > 1:
        print("the components "+", ".join(components[:-1])+" and "+components[-1]+", each of which consists of ", end="")
        fps = [it[1] for it in structure if isinstance(it, tuple)][0]
        if len(fps) > 1:
            print("the factory products "+", ".join(fps[:-1])+" and "+fps[-1]+" ", end="")
        elif len(fps) == 1:
            print("the factory product "+fps[0]+" ", end="")
    elif len(components) == 1:
        print("the component "+components[0]+", which consists of ", end="")
        fps = [it[1] for it in structure if isinstance(it, tuple)][0]
        if len(fps) > 1:
            print("the factory products "+", ".join(fps[:-1])+" and "+fps[-1]+" ", end="")
        elif len(fps) == 1:
            print("the factory product "+fps[0]+" ", end="")
    print(".")


FLOWS = {"Create": create_flow,
         "Delete": delete_flow,
         "Provision": provision_flow,
         "Deprovision": deprovision_flow,
         "RemoveModelling": remove_modelling_flow}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-D', dest='dbglevel', action='store', default=0,      help='Print Debug information')
    parser.add_argument('-H', dest='headers', action='store_true',             help='Include headers (default if multiple files are given)')
    parser.add_argument('-x', dest='html', action='store_true',                help='Output html instead of markup')
    parser.add_argument('-g', dest='graphic', action='store_true',             help='Crate Graphic instead of textual flow')
    parser.add_argument('filename', metavar='<FILENAME>',                      help='JSON input file')
    parser.add_argument('flow', metavar='<FLOW>', choices=list(FLOWS.keys())+[":ALL:"],  help='The action' )


    args=parser.parse_args()
    set_debug_level(args.dbglevel)

    cfsname = None
    DBG(10, "Reading json file '{}'".format(args.filename))
    with open(args.filename, "r") as fp:
        config = json.load(fp)
    cfsname = config["compositionName"]
    cfsstructure = [fp["factoryProduct"] for fp in config["paramMapping"]]
    if "includedComponents" in config:
        for component in config["includedComponents"]:
            component_definition_filename = "Component_{}.json".format(component)
            DBG(10, "Loading additional json file '{}'".format(component_definition_filename))
            with open (component_definition_filename, "r") as f:
                comp_config = json.load(f)
                cfsstructure.append((component, [fp["factoryProduct"] for fp in comp_config["paramMapping"]]))

    if args.flow == ":ALL:":
        if not args.graphic:
            explain_structure(cfsname, cfsstructure)
        for f in FLOWS.values():
            f(cfsname, cfsstructure, args.graphic)
            if not args.graphic:
                print("\n")
    else:
        FLOWS[args.flow](cfsname, cfsstructure, args.graphic)