''' Classes and functions for Instantlink SOA-WS interface'''
from uuid import uuid4
from enum import Enum
from xml.sax.saxutils import escape
from typing import List, Dict, Union

class RequestType(Enum):
    CREATE = 'CreateRequest'
    DELETE = 'DeleteRequest'
    MODIFY = 'ModifyRequest'
    DISPLAY = 'DisplayRequest'

class OrderLine:
    ''' An order line that is part of a SOA-WS Request-'''

    def __init__(self, id : Union[str, None], product : str, action : str, **parameters):
        self.id = id
        self.product = product
        self.action = action
        self.parameters = parameters

    def add_parameter(self, name, value):
        self.parameters[name] = value

    def add_parameters(self, **parameters):
        self.parameters.update(parameters)


class Request:
    ''' A SOA-WS Request'''

    def __init__(self, requesttype : RequestType, orderType : str, ilReqGroup : str, neType : str = "CDFF", orderNo : str = None, replyToAddress : str = None,
                 parameters : Dict[str,str] = None, orderlines : List[OrderLine] = None):
        self.requesttype = requesttype
        self.orderType = orderType
        self.ilReqGroup = ilReqGroup
        self.neType = neType
        self.orderNo = orderNo if orderNo is not None else str(uuid4())
        self.replyToAddress = replyToAddress
        self.parameters = parameters if parameters else {}
        self.orderlines = orderlines if orderlines else []

    def add_parameter(self, name, value):
        self.parameters[name] = value

    def add_parameters(self, **parameters):
        self.parameters.update(parameters)

    def add_orderline(self, orderline):
        self.orderlines.append(orderline)

    def getOrderNo(self):
        return self.orderNo
    
    def xml(self):
        xml = """<?xml version="1.0"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
               xmlns:il="http://soa.comptel.com/2011/02/instantlink">\n"""
        if self.replyToAddress is not None:
            xml += """   <soap:Header>
      <wsa:ReplyTo xmlns:wsa="http://www.w3.org/2005/08/addressing">
         <wsa:Address>{}</wsa:Address>
      </wsa:ReplyTo>
   </soap:Header>\n""".format(self.replyToAddress)
        else:
            xml += "   <soap:Header />\n"
        xml += """   <soap:Body>
      <il:{}>
         <il:RequestHeader>
            <il:NeType>{}</il:NeType>
            <il:OrderNo>{}</il:OrderNo>
         </il:RequestHeader>
         <il:RequestParameters>""".format(self.requesttype.value, self.neType, self.orderNo)
        xml += """
            <il:Parameter name="IL_REQ_GROUP" value="{}" />
            <il:Parameter name="ORDER_TYPE" value="{}" />\n""".format(self.ilReqGroup, self.orderType)
        # Add order-level parameters
        for name, value in self.parameters.items():
            xml += '            <il:Parameter name="{}" value="{}" />\n'.format(name, escape(value, entities={"'": "&apos;",'"': "&quot;", '\n': "\\n"}))
        # Add order lines
        for i, ol in enumerate(self.orderlines, 1):
            olid = "OL_{}".format(i) if ol.id is None else ol.id
            xml += '            <!-- Order Line {}: {} {} -->\n'.format(i, ol.action, ol.product)
            xml += '            <il:Parameter name="LINE_{}_ORDER_LINE_ID" value="{}" />\n'.format(i, olid)
            xml += '            <il:Parameter name="LINE_{}_NAME" value="{}" />\n'.format(i, ol.product)
            xml += '            <il:Parameter name="LINE_{}_ACTION" value="{}" />\n'.format(i, ol.action)
            for name, value in ol.parameters.items():
                xml += '            <il:Parameter name="LINE_{}_PS_PARAM_{}" value="{}" />\n'.format(i, name, escape(value, entities={"'": "&apos;",'"': "&quot;", '\n': "\\n"}))
        xml += """         </il:RequestParameters>
      </il:{}>
   </soap:Body>
</soap:Envelope>""".format(self.requesttype.value)
        return xml

class CreateRequest(Request):
    ''' A SOA-WS Create Request'''
    def __init__(self, ilReqGroup : str, neType : str = "CDFF", orderNo : str = None, orderType = "Connect", replyToAddress : str = None):
        super().__init__(RequestType.CREATE, orderType, ilReqGroup, neType, orderNo, replyToAddress)

class DeleteRequest(Request):
    ''' A SOA-WS Create Request'''
    def __init__(self, ilReqGroup : str, neType : str = "CDFF", orderNo : str = None, orderType = "Disconnect", replyToAddress : str = None):
        super().__init__(RequestType.DELETE, orderType, ilReqGroup, neType, orderNo, replyToAddress)

class ModifyRequest(Request):
    ''' A SOA-WS Create Request'''
    def __init__(self, ilReqGroup : str, neType : str = "CDFF", orderNo : str = None, orderType = "Modify", replyToAddress : str = None):
        super().__init__(RequestType.MODIFY, orderType, ilReqGroup, neType, orderNo, replyToAddress)

class DisplayRequest(Request):
    ''' A SOA-WS Create Request'''
    def __init__(self, ilReqGroup : str, neType : str = "CDFF", orderNo : str = None, orderType = "Display"):
        super().__init__(RequestType.DISPLAY, orderType, ilReqGroup, neType, orderNo, None)



