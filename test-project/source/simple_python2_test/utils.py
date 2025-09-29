# Utils with Python 2 patterns

import cPickle as pickle

def handle_error():
    try:
        1 / 0
    except Exception, e:
        print "Error:", str(e)

def string_check(text):
    if isinstance(text, unicode):
        return True
    return False

def iterate_dict(d):
    return list(d.itervalues())
