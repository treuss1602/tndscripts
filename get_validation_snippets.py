import inspect
import argparse
import validations
import json
from debug import DBG, set_debug_level

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-D', dest='dbglevel', action='store', default=0,     help='Print Debug information')

    args=parser.parse_args()
    set_debug_level(args.dbglevel)

    subclasses = [(name, value) for name, value in inspect.getmembers(validations, inspect.isclass) if name != "Validation"]
    for name, subclass in subclasses:
        clsdict = dict(inspect.getmembers(subclass))
        description = "// " + clsdict["__doc__"].strip()
        symname = clsdict["name"]
        json_snippet = {"name": symname, "parameters": [], "taskname": symname}
        parameters = inspect.signature(clsdict["__init__"]).parameters
        for pname in parameters:
            if pname != "self" and parameters[pname].kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                json_snippet["parameters"].append("<"+pname+">")
        print(description)
        print(json.dumps(json_snippet))
        print()

