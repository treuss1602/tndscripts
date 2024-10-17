''' Model for FlowOne Lookup Tables '''
import re
from debug import DBG

class LtEntry:
    ''' Lookup Table Entry/Row '''
    def __init__(self, key, *values, tablename=None):
        self.key = key
        self.values = values
        self.tablename = tablename

class LookupTable:
    ''' Lookup Table '''
    def __init__(self, name):
        self.name = name
        self.rows = []

    def add(self, row):
        self.rows.append(row)

    def read(self, fp):
        ''' Parse a file and return a list of key/value tuples (where value is a list of strings) '''
        self.rows = []
        for line in fp:
            m = re.match(r'key="([ A-Za-z0-9_#:\.\-\+\*\|]+)" values=(.*)', line.strip())
            if m is not None:
                key, valstring = m.groups()
                values = [val[1:-1] for val in valstring.split(",,")]
                self.rows.append(LtEntry(key, values, tablename=self.name))
            else:
                raise ValueError("Unable to parse line {}".format(line.strip()))

    def write(self, fp):
        ''' Writes a file in this weird format from data (list of key value tuples (where value is a list of strings) '''
        for entry in self.rows:
            fp.write('key="{}" values={}\n'.format(entry.key, ",,".join(['"{}"'.format(v) for v in entry.values])))

    def debugdump(self):
        ''' Dump the table name and content to a multi-line string '''
        rv = self.name+'\n'
        rv += "="*len(self.name)+'\n'
        for entry in self.rows:
            rv += 'key="{}" values={}\n'.format(entry.key, ",,".join(['"{}"'.format(v) for v in entry.values]))
        return rv+'\n'

    def dump(self):
        ''' Return the weird format as a (multi-line) string to be added to a zipfile. '''
        rv = ""
        for entry in self.rows:
            rv += 'key="{}" values={}\n'.format(entry.key, ",,".join(['"{}"'.format(v) for v in entry.values]))
        return rv

    @staticmethod
    def from_validations(prod, validation_config):
        lt = LookupTable('LKT_TND_CRAMER_COMMAND_VALIDATION')
        for trans, validations in validation_config.items():
            DBG(30, "Adding {} validations for transaction {}".format(len(validations), trans))
            lt.add(LtEntry(prod+"#"+trans+"#TASKS", ";".join(v.taskname for v in validations)+";"))
            for v in validations:
                lt.add(LtEntry(prod+"#"+trans+"#{}#API_NAME".format(v.taskname), v.apiname))
                lt.add(LtEntry(prod+"#"+trans+"#{}#PARAMETERS".format(v.taskname), v.get_param_string()))
                lt.add(LtEntry(prod+"#"+trans+"#{}#RETURN_PARAMETERS".format(v.taskname), v.get_return_param_string()))
        return lt

