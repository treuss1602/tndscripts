''' Model for the Factory Product Configuration. '''
import json
import functools
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
    def __init__(self, type, name, desc, valuetype, typedetails, mandatory, examplevalue=None, cramerStorage=None, acadefault=None, special=False):
        DBG(50, "Param.init called with type={}, name={}, desc={}, valuetype={}, typedetails={}, mandatory={}, examplevalue={}, cramerStorage={}, acadefault={}, special={}".format(type, name, desc, valuetype, typedetails, mandatory, examplevalue, cramerStorage, acadefault, special))
        self.type = type
        self.name = name
        self.desc = desc
        self.valuetype = valuetype.lower()
        if self.valuetype == "enumerated" or self.valuetype == "enumeration":
            if typedetails:
                self.enumvalues = [v.strip() for v in typedetails.split(";")]
                self.typedetails = None
            else:
                print("WARNING: Parameter '{}' is of type '{}' but no enumeration values are provided.".format(self.name, self.valuetype))
                self.enumvalues = []
                self.typedetails = None
        else:            
            self.typedetails = typedetails
            self.enumvalues = None
        self.mandatory = mandatory
        if self.valuetype == "boolean":
            self.examplevalue = examplevalue if isinstance(examplevalue, bool) else examplevalue.lower().strip() == "true"
            self.acadefault =  acadefault if isinstance(acadefault, bool) else acadefault.lower().strip() == "true"
        elif self.valuetype == "integer":
            self.examplevalue = int(examplevalue) if examplevalue else 0;
            self.acadefault = int(acadefault) if acadefault else 0;
        else:
            self.examplevalue = examplevalue
            self.acadefault = acadefault
        self.special = special
        self.cramerStorage = cramerStorage

    def as_dict(self):
        param = {"name": self.name, "description": self.desc, "mandatory": self.mandatory, "valueType": self.valuetype}
        if self.enumvalues is not None:
            param["valueTypeDetails"] = {"enumValues": self.enumvalues}
        elif self.typedetails:
            param["valueTypeDetails"] = {"comment": self.typedetails}
        param["special"] = self.special
        param["exampleValue"] =  self.examplevalue
        if self.acadefault is not None:
            param["acadefault"] =  self.acadefault
        if self.cramerStorage:
            param["cramerStorage"] = self.cramerStorage
        return param

    @staticmethod
    def from_dict(data, paramtype):
        if data.get("valueTypeDetails") and data["valueTypeDetails"].get("comment"):
            typedetails = data["valueTypeDetails"]["comment"]
        elif data.get("valueTypeDetails") and data["valueTypeDetails"].get("enumValues"):
            typedetails = ";".join(data["valueTypeDetails"]["enumValues"])
        else:
            typedetails = None
        return Param(paramtype, data["name"], data["description"], data["valueType"], typedetails, data["mandatory"], data["exampleValue"], data.get("cramerStorage"), data.get("acadefault"), data["special"])

    def __str__(self):
        return self.name

    def __repr__(self):
        return "'"+self.name+"'"

def joinparams(*paramsets):
    return ";".join(map(lambda x: x.name, functools.reduce(lambda a,b: a+b, paramsets)))+";"


class FactoryProductConfiguration:
    ''' The full configuration, read & write json, create lookup tables, etc. '''

    def __init__(self, factory_product_name, transaction, version, input_params, cramer_output_params, cramer_validations = []):
        self.factoryProductName = factory_product_name
        self.transaction = transaction
        self.version = float(version) if version is not None else None
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
    def from_file(fp):
        data = json.load(fp)
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

    def create_lookup_tables(self, nenameparam="NETWORK_ELEMENT_NAME"):
        ''' Create the lookup Tables '''
        prod = self.factoryProductName
        trans = self.transaction
        lkt1 = LookupTable('LKT_TND_FACTORY_PRODUCT_PARAMETERS')
        lkt1.add(LtEntry(prod+"#"+trans, joinparams(self.input_params)))

        lkt2 = LookupTable.from_validations(prod, trans, *self.cramer_validations)

        lkt3 = LookupTable('LKT_TND_CRAMER_SUBORDERS')
        lkt3.add(LtEntry(prod+"#"+trans+"#SUBORDER_PRODUCT", "TECHPROD_CRAMER_FACT_PROD_"+prod))
        lkt3.add(LtEntry(prod+"#"+trans+"#PARAMETERS", joinparams([p for p in self.input_params if not p.special])))
        lkt3.add(LtEntry(prod+"#"+trans+"#RETURN_PARAMETERS", joinparams(self.cramer_output_params)))
        lkt3.add(LtEntry(prod+"#"+trans+"#GE_PARAMETERS", joinparams([p for p in self.input_params if p.cramerStorage == self.factoryProductName+"_GE"])))
        lkt3.add(LtEntry(prod+"#"+trans+"#RB#SUBORDER_PRODUCT", "TECHPROD_CRAMER_FACT_PROD_"+prod+"_RB"))
        lkt3.add(LtEntry(prod+"#"+trans+"#RB#PARAMETERS", joinparams([p for p in self.input_params if not p.special])))

        lkt4 = LookupTable('LKT_TND_STABLENET')
        if self.transaction == "Create":
            lkt4.add(LtEntry(prod+"#"+trans+"#ORDER_DESCRIPTION", "new_rfs"))
        elif self.transaction == "Delete":
            lkt4.add(LtEntry(prod+"#"+trans+"#ORDER_DESCRIPTION", "cease_rfs"))
        else:
            raise ValueError("Action {} not (yet) supported for Stablenet Requests.")
        lkt4.add(LtEntry(prod+"#"+trans+"#TARGET_DEVICE", nenameparam))
        lkt4.add(LtEntry(prod+"#"+trans+"#RFS_NAME", self.factoryProductName+"_RFS_NAME"))
        lkt4.add(LtEntry(prod+"#"+trans+"#PARAMETERS", joinparams([p for p in self.input_params if not p.special], self.cramer_output_params)))

        lkt5 = LookupTable('LKT_TND_ENUM_PARAM_CHECK')
        lkt5.add(LtEntry(prod+"#"+trans+"#ENUM_PARAMS", ";".join(p.name for p in self.input_params if p.valuetype == "enumerated")+";"))
        for p in self.input_params:
            if p.valuetype == "enumerated" or p.valuetype == "enumeration":
                lkt5.add(LtEntry(prod+"#"+trans+"#{}".format(p.name), ";".join(p.enumvalues)+";"))

        lkt6 = LookupTable('LKT_MANDATORY_PARAM_CHECK')
        lkt6.add(LtEntry('FACTORY_PRODUCT_'+prod+"#"+trans, " ".join(p.name for p in self.input_params if p.mandatory)+" "))

        return (lkt1, lkt2, lkt3, lkt4, lkt5, lkt6)

