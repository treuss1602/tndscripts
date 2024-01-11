''' Model for the Factory Product Configuration. '''
import json
import re
import validations
from debug import DBG
from lookuptable import LookupTable, LtEntry

# Load validations from validations module
VALIDATIONS = {}
for name, cls in validations.__dict__.items():
    if isinstance(cls, type) and issubclass(cls, validations.Validation) and cls.name is not None:
        # print("Registering validation {}".format(cls.default_taskname)) # Note that DBG is not working yet as debug_level is not set
        VALIDATIONS[cls.name] = cls


class Param:
    ''' Parameter class '''
    def __init__(self, type, name, desc, valuetype, typedetails, mandatory,
                 examplevalue=None, cramerStorage=None, acadefault=None, special=None, dynamically_mapped=None, maxoccurs=None):
        DBG(50, "Param.init called with type={}, name={}, desc={}, valuetype={}, typedetails={}, mandatory={}, examplevalue={}, "
                "cramerStorage={}, acadefault={}, special={}, dynamically_mapped={}".format(type, name, desc, valuetype, typedetails, mandatory, examplevalue, cramerStorage, acadefault, special, dynamically_mapped))
        self.type = type
        self.name = name
        self.desc = desc
        self.valuetype = valuetype.lower()
        if self.valuetype == "enumerated" or self.valuetype == "enumeration":
            if typedetails:
                self.enumvalues = [v.strip() for v in typedetails.split(";")]
                self.typedetails = None
                self.integerrange = None
            else:
                print("WARNING: Parameter '{}' is of type '{}' but no enumeration values are provided.".format(self.name, self.valuetype))
                self.enumvalues = []
                self.typedetails = None
                self.integerrange = None
        elif self.valuetype == "integer" and typedetails:
            m = re.match(r'(\d+)-(\d+)', typedetails)
            if m:
                self.integerrange = tuple(int(g) for g in m.groups())
                self.typedetails = None
            else:
                self.typedetails = typedetails
                self.integerrange = None
            self.enumvalues = None
        else:            
            self.typedetails = typedetails
            self.integerrange = None
            self.enumvalues = None
        self.mandatory = mandatory
        if self.valuetype == "boolean":
            self.examplevalue = examplevalue if isinstance(examplevalue, bool) else examplevalue.lower().strip() == "true"
            self.acadefault =  acadefault if isinstance(acadefault, bool) else acadefault.lower().strip() == "true"
        elif self.valuetype == "integer":
            self.examplevalue = int(examplevalue) if examplevalue else None;
            self.acadefault = int(acadefault) if acadefault else None;
        elif self.valuetype == "string":
            self.examplevalue = str(examplevalue) if examplevalue else None;
            self.acadefault = str(acadefault) if acadefault else None;
        else:
            self.examplevalue = examplevalue
            self.acadefault = acadefault
        self.special = special
        self.cramerStorage = cramerStorage
        self.dynamically_mapped = dynamically_mapped
        self.maxoccurs = maxoccurs

    def as_dict(self):
        param = {"name": self.name, "description": self.desc, "mandatory": self.mandatory, "valueType": self.valuetype}
        if self.enumvalues is not None:
            param["valueTypeDetails"] = {"enumValues": self.enumvalues}
        elif self.integerrange is not None:
            param["valueTypeDetails"] = {"minValue": self.integerrange[0], "maxValue": self.integerrange[1]}
        elif self.typedetails:
            param["valueTypeDetails"] = {"comment": self.typedetails}
        if self.special is not None:
            param["special"] = self.special
        if self.dynamically_mapped is not None:
            param["dynamicallyMapped"] = self.dynamically_mapped
        if self.examplevalue is not None:
            param["exampleValue"] =  self.examplevalue
        if self.acadefault is not None:
            param["acadefault"] =  self.acadefault
        if self.cramerStorage:
            param["cramerStorage"] = self.cramerStorage
        if self.maxoccurs:
            param["maxOccurs"] = self.maxoccurs
        return param

    @staticmethod
    def from_dict(data, paramtype):
        if data.get("valueTypeDetails") and data["valueTypeDetails"].get("comment"):
            typedetails = data["valueTypeDetails"]["comment"]
        elif data.get("valueTypeDetails") and data["valueTypeDetails"].get("enumValues"):
            typedetails = ";".join(data["valueTypeDetails"]["enumValues"])
        else:
            typedetails = None
        return Param(paramtype, data["name"], data["description"], data["valueType"], typedetails, data["mandatory"], data.get("exampleValue"), data.get("cramerStorage"), data.get("acadefault"), data.get("special"), data.get("dynamicallyMapped", False), data.get("maxOccurs"))

    def __str__(self):
        return self.name

    def __repr__(self):
        return "'"+self.name+"'"

class FactoryProductConfiguration:
    ''' The full configuration, read & write json, create lookup tables, etc. '''

    def __init__(self, factory_product_name, transaction, version, input_params, cramer_output_params, cramer_validations = []):
        self.factoryProductName = factory_product_name
        self.transaction = transaction
        self.version = str(version) if version is not None else None
        self.input_params = input_params
        self.cramer_output_params = cramer_output_params
        self.cramer_validations = cramer_validations

    def add_validation(self, validation_name, *validation_params, taskname = None):
        if validation_name not in VALIDATIONS:
            raise ValueError("Validation '{}' not defined".format(validation_name))
        if taskname:
            val = VALIDATIONS[validation_name](*validation_params, taskname=taskname)
        else:
            val = VALIDATIONS[validation_name](*validation_params)
        self.cramer_validations.append(val)

    def input_param_names(self):
        return {p.name for p in self.input_params}

    def return_param_names(self):
        return {p.name for p in self.cramer_output_params}

    def to_file(self, fp):
        data = {"factoryProductName": self.factoryProductName, "action": self.transaction, "version": self.version}
        data["inputParameters"] = [p.as_dict() for p in self.input_params]
        data["cramerParameters"] = [p.as_dict() for p in self.cramer_output_params]
        data["cramerValidations"] = [{"name": v.name, "parameters": v.config_parameters(), "taskname": v.taskname} for v in self.cramer_validations]
        json.dump(data, fp, indent=2)

    @staticmethod
    def from_jsondata(data):
        input_params = [Param.from_dict(p, "input") for p in data["inputParameters"]]
        cramer_params = [Param.from_dict(p, "Cramer") for p in data["cramerParameters"]]
        prod = FactoryProductConfiguration(data["factoryProductName"], data["action"], data["version"], input_params, cramer_params)
        for v in data["cramerValidations"]:
            DBG(30, "Adding validation {}".format(v["name"]))
            if "taskname" in v:
                prod.add_validation(v["name"], *v["parameters"], taskname=v["taskname"])
            else:
                prod.add_validation(v["name"], *v["parameters"])
        return prod

    @staticmethod
    def from_file(fp):
        data = json.load(fp)
        return FactoryProductConfiguration.from_jsondata(data)
