#!/usr/bin/python3
import argparse
import uuid
from xml.sax.saxutils import escape

from factoryproduct import FactoryProductConfiguration
from debug import DBG, set_debug_level

def create_sample_request(productconfig : FactoryProductConfiguration, orderno = None, replyto_address = None, mandatory_only = True, soaws_py_syntax = False):
    if orderno is None:
        if soaws_py_syntax:
            orderno = '${uuid}'
            externalOrderId = '${orderNo}'
        else:
            orderno = uuid.uuid4()
            externalOrderId = orderno

    xml = """<?xml version="1.0"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
               xmlns:il="http://soa.comptel.com/2011/02/instantlink">
   <soap:Header xmlns:wsa="http://www.w3.org/2005/08/addressing">
"""
    if replyto_address is not None:
        xml += """      <wsa:ReplyTo>
         <wsa:Address>{}</wsa:Address>
      </wsa:ReplyTo>
""".format(replyto_address)
    xml += """   </soap:Header>
   <soap:Body>
      <il:CreateRequest>
         <il:RequestHeader>
            <il:NeType>CDFF</il:NeType>
            <il:OrderNo>{}</il:OrderNo>
         </il:RequestHeader>
         <il:RequestParameters>
""".format(orderno)
    xml += """            <il:Parameter name="IL_REQ_GROUP" value="TND" />
            <il:Parameter name="ORDER_TYPE" value="Connect" />
            <il:Parameter name="ORDER_EXTERNAL_ORDER_ID" value="{}" />
            <!-- Order Line 1: Create FACTORY_PRODUCT -->
            <il:Parameter name="LINE_1_ORDER_LINE_ID" value="OL_1" />
            <il:Parameter name="LINE_1_NAME" value="FACTORY_PRODUCT_{}" />
            <il:Parameter name="LINE_1_ACTION" value="Create" />
""".format(externalOrderId, productconfig.factoryProductName)
    for p in productconfig.input_params:
        if p.mandatory or not mandatory_only:
            if p.examplevalue is not None:
                DBG(30, "Adding parameter {} to request.".format(p.name))
                pname = p.name if "<N>" not in p.name else p.name.replace("<N>", "1")
                if p.valuetype == "string":
                    xml += '            <il:Parameter name="LINE_1_PS_PARAM_{}" value="{}" />\n'.format(pname, escape(p.examplevalue, entities={"'": "&apos;",'"': "&quot;", '\n': "\\n"}))
                elif p.valuetype == "boolean":
                    xml += '            <il:Parameter name="LINE_1_PS_PARAM_{}" value="{}" />\n'.format(pname, "true" if p.examplevalue else "false")
                else:
                    xml += '            <il:Parameter name="LINE_1_PS_PARAM_{}" value="{}" />\n'.format(pname, p.examplevalue)
            else:
                DBG(10, "Skipping parameter {}. No example value in input file.".format(p.name))
    xml += """         </il:RequestParameters>
      </il:CreateRequest>
   </soap:Body>
</soap:Envelope>"""
    return xml

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
        config = FactoryProductConfiguration.from_file(fp)
    req = create_sample_request(config, orderno=args.orderNo, replyto_address=args.replyAddress, mandatory_only=args.mandatory_only, soaws_py_syntax=args.soaws_py)
    if args.outfile:
        with open(args.outfile, "w") as fp:
            fp.write(req)
    else:
        print(req)
