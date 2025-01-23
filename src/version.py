VERSION = 1.0

def req_version(thing):
    print("[VER] req_version %s" % (str(thing.data)))
    if thing.data == "request":
        thing.data = VERSION
        thing.dirty_out = True
