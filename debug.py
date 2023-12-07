''' Enable consistent debug printing with changeable debug level '''
from datetime import datetime

_dbglevel = 0

def _timestamp():
    dt = datetime.today()
    return dt.strftime("[%Y-%m-%d %H:%M:%S]")

def DBG(lvl, *args):
    ''' Print out the string(s) passed as args as debug statement if lvl is greater or equal the debug level set'''
    if lvl <= _dbglevel:
        print(_timestamp()+" DEBUG: "+"".join(str(x) for x in args))

def ERROR(*args):
    ''' Print out the string(s) passed as args as error statement'''
    print(_timestamp()+" ERROR: "+"".join(str(x) for x in args))

def set_debug_level(val):
    ''' Change the debug level'''
    global _dbglevel
    if isinstance(val,str):
        val = int(val)
    _dbglevel = val
