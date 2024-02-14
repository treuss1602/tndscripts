#!/usr/bin/python3
import argparse

from factoryproduct import FactoryProductConfiguration
from debug import DBG, set_debug_level

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-D', dest='dbglevel', action='store', default=0,   help='Print Debug information')
    parser.add_argument('--pre', dest='preonly', action='store_true',       help='Print parameters passed to NEI only')
    parser.add_argument('--post', dest='postonly', action='store_true',     help='Print parameters passed from NEI to Stablenet only')
    parser.add_argument('filename', metavar='<FILENAME>', nargs="+",        help='JSON input files')

    args=parser.parse_args()
    set_debug_level(args.dbglevel)

    for filename in args.filename:
        DBG(10, "Reading json file '{}'".format(filename))
        with open(filename, "r") as fp:
            config = FactoryProductConfiguration.from_file(fp)
            if len(args.filename) > 1:
                print(config.factoryProductName)
                print("="*len(config.factoryProductName))
            pre, post = config.stablenet_params
            if args.preonly:
                print("\n".join(pre))
            elif args.postonly:
                print("\n".join(post))
            else:
                i,j = 0,0
                while i < len(pre) and j < len(post):
                    if pre[i] == post[j]:
                        print("X X ", pre[i])
                        i += 1
                        j += 1
                    elif pre[i] in post:
                        print("- X ", post[j])
                        j += 1
                    else: # post[j] in pre:
                        print("X - ", pre[i])
                        i += 1
                while i < len(pre):
                    print("X - ", pre[i])
                    i += 1
                while j < len(post):
                    print("- X ", post[j])
                    j += 1

            if len(args.filename) > 1:
                print()
