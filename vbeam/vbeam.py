#!/usr/bin/env python3



import vbeam_si as _si
#import vbeam_bo as _bo



clock = None
si = _si.VAccelerator(clock)
#bo = _bo.VAccelerator(clock)




from xmlrpc.server import SimpleXMLRPCServer

def read_pv(pv):
    if 'SI' in pv:
        data = si.read_pv(pv)
        return data
    elif 'BO' in pv:
        return 'Booster'
        #return bo.read_pv(pv)

def write_pv(pv, value):
    if 'SI' in pv:
        si.write_pv(pv, value)
    elif 'BO' in pv:
        bo.write_pv(pv, value)

server = SimpleXMLRPCServer(("localhost", 8000))
print("Listening on port 8000...")
server.register_function(read_pv, "read_pv")
server.serve_forever()
