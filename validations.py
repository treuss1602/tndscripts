''' Module for classes for Cramer validations '''
VALUETYPE_PARAMETER=0
VALUETYPE_LITERAL=1

class Validation:
    ''' Base class for all Cramer API Validations '''

    # No default name
    name = None

    def __init__(self, taskname, apiname):
        self.taskname = taskname
        self.apiname = apiname
        self.parameters = []
        self.return_parameters = []

    def add_parameter(self, name, value, valuetype):
        self.parameters.append((name, value, valuetype))
        if valuetype == VALUETYPE_PARAMETER:
            self.return_parameters.append((name, value))

    def get_param_string(self):
        value = ""
        for i, (k, v, vt) in enumerate(self.parameters, 1):
            if vt == VALUETYPE_LITERAL:
                # value += "{}=\u00ab{}\u00bb;".format(k,v)
                value += "{}=*{}*;".format(k,v)
            else:
                value += "{}={};".format(k,v)
        return value

    def get_return_param_string(self):
        return ",".join("{}:{}".format(*x) for x in self.return_parameters)

class NodeExistsValidation(Validation):
    ''' Checks whether a node of specific name exists, using checkObjectExists API '''
    name = "CHECK_NODE_EXISTS"
    api = "checkObjectExists"

    def __init__(self, nodename, *, taskname=name):
        super().__init__(taskname, self.api)
        self.nodename = nodename
        self.add_parameter("dimObject", "Node", VALUETYPE_LITERAL)
        self.add_parameter("objectName", nodename, VALUETYPE_PARAMETER)

    def config_parameters(self):
        ''' Return the list of parameters needed for configuring this validation.
            The list and order needs to be consistent with __init__ parameters. '''
        return [self.nodename]
    
class NodeLocationValidation(Validation):
    ''' Checks whether a node of specific name exists and has a location, using getLocationByNodeName API '''
    name = "CHECK_NODE_LOCATION"
    api = "getLocationByNodeName"

    def __init__(self, nodename, *, taskname=name):
        super().__init__(taskname, self.api)
        self.nodename = nodename
        self.add_parameter("nodeName", nodename, VALUETYPE_PARAMETER)

    def config_parameters(self):
        ''' Return the list of parameters needed for configuring this validation.
            The list and order needs to be consistent with __init__ parameters. '''
        return [self.nodename]
    
class UserIpamPermissions(Validation):
    ''' Checks whether a user has IPAM permissions for all subnet groups '''
    name = "CHECK_IPAM_PERMISSIONS"
    api = "validateSubnetGroupPermissionsForTND"

    def __init__(self, userName, primaryIPv4IfAddress, additionalIPv4IfAddresses, primaryIPv6IfAddress, additionalIPv6IfAddresses, *, taskname=name):
        super().__init__(taskname, self.api)
        self.userName = userName
        self.primaryIPv4IfAddress = primaryIPv4IfAddress
        self.additionalIPv4IfAddresses = additionalIPv4IfAddresses
        self.primaryIPv6IfAddress = primaryIPv6IfAddress
        self.additionalIPv6IfAddresses = additionalIPv6IfAddresses
        self.add_parameter("userName", userName, VALUETYPE_PARAMETER)
        self.add_parameter("primaryIPv4IfAddress", primaryIPv4IfAddress, VALUETYPE_PARAMETER)
        self.add_parameter("additionalIPv4IfAddresses", additionalIPv4IfAddresses, VALUETYPE_PARAMETER)
        self.add_parameter("primaryIPv6IfAddress", primaryIPv6IfAddress, VALUETYPE_PARAMETER)
        self.add_parameter("additionalIPv6IfAddresses", additionalIPv6IfAddresses, VALUETYPE_PARAMETER)

    def config_parameters(self):
        ''' Return the list of parameters needed for configuring this validation.
            The list and order needs to be consistent with __init__ parameters. '''
        return [self.userName, self.primaryIPv4IfAddress, self.additionalIPv4IfAddresses, self.primaryIPv6IfAddress, self.additionalIPv6IfAddresses]
    

